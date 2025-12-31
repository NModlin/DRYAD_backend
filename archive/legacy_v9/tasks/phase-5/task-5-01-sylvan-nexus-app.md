# Task 5-01: The Sylvan Nexus - Multi-Platform Personal Knowledge Assistant

**Phase:** 5 - Advanced Features & Polish  
**Week:** 21-24 - Post-v1.0 Enhancement  
**Priority:** HIGH (Post-v1.0)  
**Estimated Hours:** 80 hours

---

## 📋 OVERVIEW

Build "The Sylvan Nexus" - a multi-platform personal knowledge assistant application that connects to DRYAD.AI server for seamless knowledge management across Android Mobile, Android TV, Xbox, and Web platforms. Implements intelligent network-aware routing (local when home, cloud when remote) and Google Cloud "mailbox" pattern for secure data delivery.

---

## 🎯 OBJECTIVES

1. Design multi-platform architecture
2. Implement Android mobile app
3. Implement Android TV app
4. Create web-based interface
5. Build Google Cloud mailbox service
6. Implement network-aware routing
7. Add Google Drive backup/restore
8. Test cross-platform synchronization

---

## 📊 CURRENT STATE

**Existing:**
- DRYAD.AI backend with Groves/Branches/Vessels architecture
- Local server deployment
- Cloud approval proxy (Task 2-47)
- Admin dashboard and API endpoints

**Gaps:**
- No mobile app
- No TV app
- No cloud mailbox for data delivery
- No network-aware routing
- No Google Drive integration

---

## 🏗️ ARCHITECTURE

### **The Sylvan Nexus Vision**

```
┌─────────────────────────────────────────────────────────┐
│                   The Sylvan Nexus                      │
│              Personal Knowledge Assistant                │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
   │ Android │        │ Android │        │   Web   │
   │ Mobile  │        │   TV    │        │ Browser │
   └────┬────┘        └────┬────┘        └────┬────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                ┌───────────▼───────────┐
                │  Network-Aware Router │
                │  (Auto-detect home)   │
                └───────────┬───────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
    ┌───────▼────────┐            ┌────────▼────────┐
    │ Local DRYAD    │            │ Google Cloud    │
    │ Server (Home)  │            │ Mailbox Service │
    └────────────────┘            └─────────────────┘
            │                               │
            │                               │
    ┌───────▼────────┐            ┌────────▼────────┐
    │ Local Database │            │   Firestore     │
    │   (Primary)    │            │  (Temporary)    │
    └────────────────┘            └─────────────────┘
            │
    ┌───────▼────────┐
    │ Google Drive   │
    │    Backup      │
    └────────────────┘
```

### **Key Components:**

1. **Android Mobile App** (Kotlin/Jetpack Compose)
2. **Android TV App** (Kotlin/Leanback)
3. **Web Interface** (React/Next.js)
4. **Network-Aware Router** (Detects home network)
5. **Google Cloud Mailbox** (Firestore-based data delivery)
6. **Google Drive Sync** (Backup/restore)

---

## 🔧 IMPLEMENTATION

### Phase 1: Android Mobile App (24 hours)

Create `sylvan-nexus-mobile/` directory:

```kotlin
// app/src/main/java/ai/dryad/sylvan/MainActivity.kt
package ai.dryad.sylvan

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import ai.dryad.sylvan.ui.theme.SylvanNexusTheme
import ai.dryad.sylvan.network.NetworkRouter
import ai.dryad.sylvan.api.DryadClient

class MainActivity : ComponentActivity() {
    private lateinit var networkRouter: NetworkRouter
    private lateinit var dryadClient: DryadClient
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Initialize network-aware router
        networkRouter = NetworkRouter(this)
        dryadClient = DryadClient(networkRouter)
        
        setContent {
            SylvanNexusTheme {
                SylvanNexusApp(dryadClient)
            }
        }
    }
}

@Composable
fun SylvanNexusApp(dryadClient: DryadClient) {
    var selectedTab by remember { mutableStateOf(0) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("🌲 Sylvan Nexus") }
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    icon = { Icon(Icons.Default.Home, "Groves") },
                    label = { Text("Groves") },
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 }
                )
                NavigationBarItem(
                    icon = { Icon(Icons.Default.Search, "Search") },
                    label = { Text("Search") },
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 }
                )
                NavigationBarItem(
                    icon = { Icon(Icons.Default.Settings, "Settings") },
                    label = { Text("Settings") },
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 }
                )
            }
        }
    ) { padding ->
        when (selectedTab) {
            0 -> GrovesScreen(dryadClient, Modifier.padding(padding))
            1 -> SearchScreen(dryadClient, Modifier.padding(padding))
            2 -> SettingsScreen(dryadClient, Modifier.padding(padding))
        }
    }
}
```

---

### Phase 2: Network-Aware Router (8 hours)

```kotlin
// app/src/main/java/ai/dryad/sylvan/network/NetworkRouter.kt
package ai.dryad.sylvan.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class NetworkRouter(private val context: Context) {
    
    private val _connectionMode = MutableStateFlow(ConnectionMode.CLOUD)
    val connectionMode: StateFlow<ConnectionMode> = _connectionMode
    
    // Configuration
    private val homeNetworkSSID = "YOUR_HOME_WIFI_SSID"
    private val localServerUrl = "http://192.168.1.100:8000"
    private val cloudMailboxUrl = "https://your-cloud-run-url.run.app"
    
    enum class ConnectionMode {
        LOCAL,   // Connected to home network
        CLOUD,   // Remote, use cloud mailbox
        OFFLINE  // No connection
    }
    
    suspend fun detectNetwork(): ConnectionMode {
        val connectivityManager = context.getSystemService(
            Context.CONNECTIVITY_SERVICE
        ) as ConnectivityManager
        
        val network = connectivityManager.activeNetwork ?: return ConnectionMode.OFFLINE
        val capabilities = connectivityManager.getNetworkCapabilities(network)
            ?: return ConnectionMode.OFFLINE
        
        // Check if on WiFi
        if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
            // Check if home network
            val wifiManager = context.applicationContext.getSystemService(
                Context.WIFI_SERVICE
            ) as android.net.wifi.WifiManager
            
            val wifiInfo = wifiManager.connectionInfo
            val ssid = wifiInfo.ssid.removeSurrounding("\"")
            
            if (ssid == homeNetworkSSID) {
                _connectionMode.value = ConnectionMode.LOCAL
                return ConnectionMode.LOCAL
            }
        }
        
        // Not on home network, use cloud
        _connectionMode.value = ConnectionMode.CLOUD
        return ConnectionMode.CLOUD
    }
    
    fun getBaseUrl(): String {
        return when (_connectionMode.value) {
            ConnectionMode.LOCAL -> localServerUrl
            ConnectionMode.CLOUD -> cloudMailboxUrl
            ConnectionMode.OFFLINE -> ""
        }
    }
}
```

---

### Phase 3: Google Cloud Mailbox Service (16 hours)

```python
# cloud-mailbox/main.py
"""
Google Cloud Mailbox Service

Temporary storage for DRYAD data delivery to remote clients.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import firestore

app = FastAPI(title="DRYAD Cloud Mailbox")
db = firestore.Client()

MAILBOX_TTL_HOURS = 24  # Auto-delete after 24 hours


class MailboxMessage(BaseModel):
    """Message from DRYAD to client."""
    user_id: str
    message_type: str  # "grove", "branch", "vessel", "search_results"
    data: dict
    secret: str


class MailboxRequest(BaseModel):
    """Request from client to retrieve messages."""
    user_id: str
    secret: str
    message_ids: list[str] | None = None


@app.post("/api/mailbox/send")
async def send_to_mailbox(message: MailboxMessage):
    """
    DRYAD sends data to user's mailbox.
    
    Flow:
    1. User requests data from DRYAD (e.g., "show me grove X")
    2. DRYAD can't reach user directly (not on home network)
    3. DRYAD sends data to cloud mailbox
    4. User's app polls mailbox and retrieves data
    """
    # Validate secret
    if message.secret != os.getenv("MAILBOX_SECRET"):
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    # Store in Firestore
    message_ref = db.collection("mailbox").document()
    message_ref.set({
        "user_id": message.user_id,
        "message_type": message.message_type,
        "data": message.data,
        "created_at": firestore.SERVER_TIMESTAMP,
        "expires_at": datetime.utcnow() + timedelta(hours=MAILBOX_TTL_HOURS),
        "retrieved": False
    })
    
    return {
        "status": "delivered",
        "message_id": message_ref.id,
        "expires_in_hours": MAILBOX_TTL_HOURS
    }


@app.post("/api/mailbox/retrieve")
async def retrieve_from_mailbox(request: MailboxRequest):
    """
    Client retrieves messages from mailbox.
    
    Flow:
    1. Client polls mailbox every 30 seconds
    2. Retrieves any new messages
    3. Marks messages as retrieved
    4. Messages auto-delete after TTL
    """
    # Validate secret
    if request.secret != os.getenv("MAILBOX_SECRET"):
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    # Query messages for user
    query = db.collection("mailbox").where(
        "user_id", "==", request.user_id
    ).where(
        "retrieved", "==", False
    ).order_by("created_at", direction=firestore.Query.DESCENDING)
    
    messages = []
    for doc in query.stream():
        message_data = doc.to_dict()
        messages.append({
            "message_id": doc.id,
            "message_type": message_data["message_type"],
            "data": message_data["data"],
            "created_at": message_data["created_at"]
        })
        
        # Mark as retrieved
        doc.reference.update({"retrieved": True})
    
    return {"messages": messages, "count": len(messages)}
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Android mobile app functional
- [ ] Android TV app functional
- [ ] Web interface working
- [ ] Network-aware routing operational
- [ ] Google Cloud mailbox service deployed
- [ ] Google Drive backup/restore working
- [ ] Cross-platform sync tested
- [ ] Documentation complete

---

## 📝 NOTES

- Start with Android mobile, then TV, then web
- Use Jetpack Compose for modern Android UI
- Keep cloud costs in free tier
- Implement offline mode with local caching
- Auto-delete mailbox messages after 24 hours
- Support branching conversations
- Preserve context across platforms


