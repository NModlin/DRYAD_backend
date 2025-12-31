"""
Self-Healing UI Endpoints
Provides HTML interfaces for human review of self-healing tasks.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database.database import AsyncSessionLocal
from app.database.self_healing_models import SelfHealingTask, TaskStatus
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/self-healing-ui", tags=["self-healing-ui"])


async def get_db():
    """Database session dependency."""
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
async def view_task_ui(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Display task details in a nice HTML format with Approve/Reject buttons.
    """
    try:
        # Get task from database
        result = await db.execute(
            select(SelfHealingTask).where(SelfHealingTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Format the HTML
        severity_color = {
            "low": "#28a745",
            "medium": "#ffc107",
            "high": "#dc3545",
            "critical": "#721c24"
        }.get(task.severity, "#6c757d")
        
        status_color = {
            "pending_review": "#ffc107",
            "approved": "#17a2b8",
            "rejected": "#dc3545",
            "in_progress": "#007bff",
            "completed": "#28a745",
            "failed": "#dc3545"
        }.get(task.status, "#6c757d")
        
        # Build plan details HTML
        plan_html = ""
        if task.plan:
            changes = task.plan.get("changes", [])
            for i, change in enumerate(changes, 1):
                plan_html += f"""
                <div style="background: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 3px solid #007bff;">
                    <strong>{i}. {change.get('file', 'Unknown file')}</strong><br>
                    Lines {change.get('line_start', '?')} - {change.get('line_end', '?')}<br>
                    <em>{change.get('rationale', 'No rationale provided')}</em>
                </div>
                """
            
            tests = task.plan.get("tests_to_run", [])
            if tests:
                plan_html += f"""
                <div style="margin-top: 15px;">
                    <strong>Tests to Run:</strong><br>
                    {'<br>'.join([f'• {test}' for test in tests])}
                </div>
                """
        
        # Disable buttons if not pending review
        buttons_disabled = task.status != "pending_review"
        button_style = "opacity: 0.5; cursor: not-allowed;" if buttons_disabled else ""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Self-Healing Task Review</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    margin-top: 0;
                    border-bottom: 2px solid #007bff;
                    padding-bottom: 10px;
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                    margin-right: 10px;
                }}
                .section {{
                    margin: 20px 0;
                }}
                .label {{
                    font-weight: bold;
                    color: #666;
                    margin-bottom: 5px;
                }}
                .value {{
                    color: #333;
                    margin-bottom: 15px;
                }}
                .error-message {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }}
                .proposed-fix {{
                    background: #d1ecf1;
                    border-left: 4px solid #17a2b8;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }}
                .button-group {{
                    margin-top: 30px;
                    display: flex;
                    gap: 15px;
                }}
                button {{
                    padding: 12px 30px;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: all 0.3s;
                }}
                button:hover:not(:disabled) {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }}
                button:disabled {{
                    opacity: 0.5;
                    cursor: not-allowed;
                }}
                .approve-btn {{
                    background: #28a745;
                    color: white;
                }}
                .reject-btn {{
                    background: #dc3545;
                    color: white;
                }}
                .loading {{
                    display: none;
                    text-align: center;
                    margin-top: 20px;
                }}
                .result {{
                    display: none;
                    padding: 15px;
                    margin-top: 20px;
                    border-radius: 6px;
                }}
                .result.success {{
                    background: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                }}
                .result.error {{
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛡️ Self-Healing Fix Review</h1>
                
                <div class="section">
                    <span class="badge" style="background: {severity_color};">{task.severity.upper()}</span>
                    <span class="badge" style="background: {status_color};">{task.status.replace('_', ' ').upper()}</span>
                </div>
                
                <div class="section">
                    <div class="label">Task ID:</div>
                    <div class="value" style="font-family: monospace; font-size: 12px;">{task.id}</div>
                </div>
                
                <div class="section">
                    <div class="label">Error Type:</div>
                    <div class="value">{task.error_type}</div>
                </div>
                
                <div class="section">
                    <div class="label">Location:</div>
                    <div class="value">{task.file_path}:{task.line_number}</div>
                </div>
                
                <div class="section">
                    <div class="label">Detected:</div>
                    <div class="value">{task.created_at}</div>
                </div>
                
                <div class="error-message">
                    <strong>Error Message:</strong><br>
                    {task.error_message}
                </div>
                
                <div class="proposed-fix">
                    <strong>Proposed Fix:</strong><br>
                    {task.goal}
                </div>
                
                <div class="section">
                    <div class="label">Plan Details:</div>
                    {plan_html if plan_html else '<em>No detailed plan available</em>'}
                </div>
                
                <div class="button-group">
                    <button class="approve-btn" onclick="reviewTask('approved')" {"disabled" if buttons_disabled else ""}>
                        ✅ Approve Fix
                    </button>
                    <button class="reject-btn" onclick="reviewTask('rejected')" {"disabled" if buttons_disabled else ""}>
                        ❌ Reject Fix
                    </button>
                </div>
                
                {"<p style='color: #666; margin-top: 15px;'><em>This task has already been reviewed.</em></p>" if buttons_disabled else ""}
                
                <div class="loading" id="loading">
                    <p>⏳ Processing your decision...</p>
                </div>
                
                <div class="result" id="result"></div>
            </div>
            
            <script>
                async function reviewTask(decision) {{
                    const loading = document.getElementById('loading');
                    const result = document.getElementById('result');
                    const buttons = document.querySelectorAll('button');
                    
                    // Disable buttons and show loading
                    buttons.forEach(btn => btn.disabled = true);
                    loading.style.display = 'block';
                    result.style.display = 'none';
                    
                    try {{
                        const response = await fetch('/api/v1/orchestrator/self-healing/review/{task_id}', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{
                                decision: decision,
                                reviewer: 'web-ui-user',
                                comments: `Reviewed via web UI at ${{new Date().toISOString()}}`
                            }})
                        }});
                        
                        const data = await response.json();
                        
                        loading.style.display = 'none';
                        result.style.display = 'block';
                        
                        if (response.ok) {{
                            result.className = 'result success';
                            result.innerHTML = `
                                <strong>✅ Success!</strong><br>
                                ${{data.message || 'Task has been ' + decision}}
                                <br><br>
                                <em>You can close this window now.</em>
                            `;
                        }} else {{
                            throw new Error(data.detail || 'Unknown error');
                        }}
                    }} catch (error) {{
                        loading.style.display = 'none';
                        result.style.display = 'block';
                        result.className = 'result error';
                        result.innerHTML = `
                            <strong>❌ Error</strong><br>
                            ${{error.message}}
                            <br><br>
                            <button onclick="location.reload()">Try Again</button>
                        `;
                        buttons.forEach(btn => btn.disabled = false);
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error displaying task UI: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

