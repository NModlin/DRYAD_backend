"""
DRYAD Cloud Approval Proxy

Lightweight FastAPI service for remote approval access.
"""
from __future__ import annotations

import os
import httpx
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.cloud import firestore
import hashlib
import secrets

app = FastAPI(title="DRYAD Approval Proxy")

# Initialize Firestore
db = firestore.Client()

# Configuration
PUSHOVER_APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PROXY_SECRET = os.getenv("PROXY_SECRET")  # Shared secret with local DRYAD
CLOUD_RUN_URL = os.getenv("CLOUD_RUN_URL")


class ApprovalRequest(BaseModel):
    """Approval request from local DRYAD."""
    approval_id: str
    action_type: str
    action_description: str
    risk_level: str
    requested_at: str
    callback_url: str  # Local DRYAD webhook URL
    secret: str  # Shared secret for authentication


class ApprovalDecision(BaseModel):
    """Approval decision from user."""
    approval_id: str
    decision: str  # "approve" or "reject"
    notes: str | None = None
    secret: str


@app.post("/api/approval-request")
async def receive_approval_request(request: ApprovalRequest):
    """
    Receive approval request from local DRYAD server.

    Flow:
    1. Validate shared secret
    2. Store in Firestore
    3. Send Pushover notification
    """
    # Validate secret
    if request.secret != PROXY_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")

    # Store in Firestore
    approval_ref = db.collection("approvals").document(request.approval_id)
    approval_ref.set({
        "approval_id": request.approval_id,
        "action_type": request.action_type,
        "action_description": request.action_description,
        "risk_level": request.risk_level,
        "requested_at": request.requested_at,
        "callback_url": request.callback_url,
        "status": "pending",
        "created_at": firestore.SERVER_TIMESTAMP
    })

    # Send Pushover notification
    await send_pushover_notification(
        title=f"🔔 DRYAD Approval Required",
        message=f"{request.action_type}: {request.action_description}",
        url=f"{CLOUD_RUN_URL}/approval/{request.approval_id}",
        priority=1  # High priority
    )

    return {"status": "received", "approval_id": request.approval_id}


@app.get("/approval/{approval_id}", response_class=HTMLResponse)
async def get_approval_interface(approval_id: str):
    """
    Serve web-based approval interface.

    User clicks Pushover notification link and lands here.
    """
    # Fetch approval from Firestore
    approval_ref = db.collection("approvals").document(approval_id)
    approval_doc = approval_ref.get()

    if not approval_doc.exists:
        return "<h1>Approval not found</h1>"

    approval = approval_doc.to_dict()

    if approval["status"] != "pending":
        return f"<h1>Approval already {approval['status']}</h1>"

    # Render approval interface
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DRYAD Approval</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .card {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .risk-high {{ color: #dc3545; }}
            .risk-medium {{ color: #ffc107; }}
            .risk-low {{ color: #28a745; }}
            button {{
                padding: 15px 30px;
                margin: 10px 5px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
            }}
            .approve {{ background: #28a745; color: white; }}
            .reject {{ background: #dc3545; color: white; }}
            textarea {{
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🌲 DRYAD Approval Request</h1>
            <p><strong>Action:</strong> {approval['action_type']}</p>
            <p><strong>Description:</strong> {approval['action_description']}</p>
            <p><strong>Risk Level:</strong>
                <span class="risk-{approval['risk_level'].lower()}">
                    {approval['risk_level']}
                </span>
            </p>
            <p><strong>Requested:</strong> {approval['requested_at']}</p>

            <textarea id="notes" placeholder="Optional notes..."></textarea>

            <button class="approve" onclick="submitDecision('approve')">
                ✅ Approve
            </button>
            <button class="reject" onclick="submitDecision('reject')">
                ❌ Reject
            </button>

            <div id="result"></div>
        </div>

        <script>
            async function submitDecision(decision) {{
                const notes = document.getElementById('notes').value;
                const result = document.getElementById('result');

                try {{
                    const response = await fetch('/api/approval-decision', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            approval_id: '{approval_id}',
                            decision: decision,
                            notes: notes,
                            secret: '{PROXY_SECRET}'
                        }})
                    }});

                    const data = await response.json();

                    if (response.ok) {{
                        result.innerHTML = `<p style="color: green;">
                            ✅ Decision submitted successfully!
                        </p>`;
                        setTimeout(() => window.close(), 2000);
                    }} else {{
                        result.innerHTML = `<p style="color: red;">
                            ❌ Error: ${{data.detail}}
                        </p>`;
                    }}
                }} catch (error) {{
                    result.innerHTML = `<p style="color: red;">
                        ❌ Network error: ${{error}}
                    </p>`;
                }}
            }}
        </script>
    </body>
    </html>
    """

    return html


@app.post("/api/approval-decision")
async def submit_approval_decision(decision: ApprovalDecision):
    """
    Process approval decision from user.

    Flow:
    1. Validate secret
    2. Update Firestore
    3. Send webhook to local DRYAD
    """
    # Validate secret
    if decision.secret != PROXY_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")

    # Get approval from Firestore
    approval_ref = db.collection("approvals").document(decision.approval_id)
    approval_doc = approval_ref.get()

    if not approval_doc.exists:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval = approval_doc.to_dict()

    if approval["status"] != "pending":
        raise HTTPException(status_code=400, detail="Approval already processed")

    # Update status
    approval_ref.update({
        "status": decision.decision,
        "decision_notes": decision.notes,
        "decided_at": firestore.SERVER_TIMESTAMP
    })

    # Send webhook to local DRYAD
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                approval["callback_url"],
                json={
                    "approval_id": decision.approval_id,
                    "decision": decision.decision,
                    "notes": decision.notes,
                    "secret": PROXY_SECRET
                }
            )

            if response.status_code != 200:
                # Store for retry
                approval_ref.update({"callback_failed": True})

    except Exception as e:
        # Store for retry
        approval_ref.update({"callback_error": str(e)})

    return {"status": "success", "decision": decision.decision}


async def send_pushover_notification(
    title: str,
    message: str,
    url: str,
    priority: int = 0
):
    """Send Pushover notification."""
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_APP_TOKEN,
                "user": PUSHOVER_USER_KEY,
                "title": title,
                "message": message,
                "url": url,
                "url_title": "Review Approval",
                "priority": priority
            }
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "dryad-approval-proxy"}

