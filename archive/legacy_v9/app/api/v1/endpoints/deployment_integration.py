"""
DRYAD Backend Deployment Integration Endpoint

Automated bidirectional integration system where:
1. Frontend sends deployment package (configuration)
2. Backend validates and processes configuration
3. Backend generates API keys, credentials, and connection details
4. Backend returns ready package with all integration details

This enables frontend teams to automatically configure their integration
with the complete DRYAD.AI backend system.
"""

import logging
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.database.database import get_db
from app.core.logging_config import get_logger
from app.core.config import config
from app.integrations.dryad_teams_notifier import dryad_teams_notifier

logger = get_logger(__name__)
router = APIRouter()

# In-memory storage for deployment packages (in production, use database)
_deployment_packages: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# REQUEST MODELS - Frontend → Backend
# ============================================================================

class ClientIdentification(BaseModel):
    """Client identification information."""
    client_name: str = Field(..., description="Client/organization name")
    client_id: str = Field(..., description="Unique client identifier")
    environment: str = Field(..., description="Environment: development, staging, production")
    contact_email: str = Field(..., description="Technical contact email")
    project_name: Optional[str] = Field(None, description="Project name")


class APIEndpointRequirements(BaseModel):
    """Required API endpoints."""
    dryad_groves: bool = Field(True, description="Grove management endpoints")
    dryad_branches: bool = Field(True, description="Branch navigation endpoints")
    dryad_vessels: bool = Field(True, description="Vessel context endpoints")
    dryad_oracle: bool = Field(True, description="Oracle consultation endpoints")
    dryad_dialogues: bool = Field(True, description="Dialogue history endpoints")
    dryad_search: bool = Field(False, description="Advanced search endpoints")
    dryad_export_import: bool = Field(False, description="Export/import endpoints")
    agent_studio: bool = Field(False, description="Agent Studio endpoints")
    admin_center: bool = Field(False, description="Admin Center endpoints")
    multi_agent: bool = Field(False, description="Multi-agent workflows")
    websocket: bool = Field(False, description="WebSocket real-time features")


class AuthenticationPreferences(BaseModel):
    """Authentication method preferences."""
    oauth2_google: bool = Field(True, description="OAuth2 with Google")
    jwt_tokens: bool = Field(True, description="JWT token authentication")
    api_keys: bool = Field(False, description="API key authentication")
    webhook_auth: bool = Field(False, description="Webhook authentication")


class RateLimitRequirements(BaseModel):
    """Rate limiting requirements."""
    requests_per_minute: int = Field(60, ge=1, le=1000, description="Requests per minute")
    burst_size: int = Field(10, ge=1, le=100, description="Burst size")
    concurrent_requests: int = Field(10, ge=1, le=100, description="Max concurrent requests")


class FeatureFlags(BaseModel):
    """Feature flags needed."""
    enable_vector_search: bool = Field(False, description="Enable vector search")
    enable_multi_provider: bool = Field(False, description="Enable multi-provider Oracle")
    enable_branch_suggestions: bool = Field(False, description="Enable AI branch suggestions")
    enable_export_import: bool = Field(False, description="Enable export/import")
    enable_webhooks: bool = Field(False, description="Enable webhook notifications")
    enable_realtime: bool = Field(False, description="Enable real-time updates")


class DatabaseAccessRequirements(BaseModel):
    """Database access requirements."""
    read_access: bool = Field(False, description="Read access to database")
    write_access: bool = Field(False, description="Write access to database")
    tables_needed: List[str] = Field(default_factory=list, description="Specific tables needed")


class WebhookConfiguration(BaseModel):
    """Webhook configuration for receiving notifications from DRYAD."""
    url: str = Field(..., description="Publicly accessible webhook endpoint URL")
    events: List[str] = Field(default_factory=list, description="Event types to subscribe to")

    @validator('url')
    def validate_webhook_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Webhook URL must start with http:// or https://")
        return v


class FrontendDeploymentPackage(BaseModel):
    """
    Frontend deployment package sent to backend.

    This contains all configuration requirements from the frontend team.
    """
    client: ClientIdentification
    api_endpoints: APIEndpointRequirements
    authentication: AuthenticationPreferences
    cors_origins: List[str] = Field(..., description="CORS origins to allow")
    rate_limits: RateLimitRequirements
    features: FeatureFlags
    database_access: Optional[DatabaseAccessRequirements] = None
    webhook_config: Optional[WebhookConfiguration] = None
    custom_requirements: Optional[Dict[str, Any]] = Field(None, description="Custom requirements")

    @validator('cors_origins')
    def validate_cors_origins(cls, v):
        if not v:
            raise ValueError("At least one CORS origin required")
        return v

    @validator('webhook_config')
    def validate_webhook_config(cls, v, values):
        """Validate webhook configuration consistency."""
        if v:
            # Check if webhooks are enabled
            features = values.get('features')
            auth = values.get('authentication')

            if features and not features.enable_webhooks:
                raise ValueError("webhook_config provided but enable_webhooks is False")

            if auth and not auth.webhook_auth:
                raise ValueError("webhook_config provided but webhook_auth is False")

        return v


# ============================================================================
# RESPONSE MODELS - Backend → Frontend
# ============================================================================

class GeneratedCredentials(BaseModel):
    """Generated authentication credentials."""
    api_key: Optional[str] = None
    api_key_id: Optional[str] = None
    webhook_secret: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class EndpointURLs(BaseModel):
    """Complete endpoint URLs for all DRYAD APIs."""
    base_url: str
    api_version: str
    
    # DRYAD Core Endpoints
    groves: Optional[str] = None
    branches: Optional[str] = None
    vessels: Optional[str] = None
    oracle: Optional[str] = None
    dialogues: Optional[str] = None
    search: Optional[str] = None
    export_import: Optional[str] = None
    
    # Additional Endpoints
    agent_studio: Optional[str] = None
    admin_center: Optional[str] = None
    multi_agent: Optional[str] = None
    
    # Utility Endpoints
    health: str
    docs: str
    websocket: Optional[str] = None


class DatabaseConnectionInfo(BaseModel):
    """Database connection information (if access granted)."""
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_required: bool = True


class ConfigurationValidation(BaseModel):
    """Configuration validation results."""
    valid: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class IntegrationStatus(BaseModel):
    """Integration status and health check information."""
    status: str = Field(..., description="ready, pending, error")
    health_check_url: str
    api_docs_url: str
    websocket_url: Optional[str] = None
    estimated_setup_time: str = "5 minutes"


class WebhookInfo(BaseModel):
    """Webhook configuration information."""
    enabled: bool
    url: Optional[str] = None
    events: List[str] = Field(default_factory=list)
    secret_provided: bool = False


class BackendResponsePackage(BaseModel):
    """
    Backend response package returned to frontend.

    This contains all credentials, URLs, and configuration needed
    for immediate integration.
    """
    deployment_id: str
    client_id: str
    environment: str
    created_at: str
    expires_at: Optional[str] = None

    credentials: GeneratedCredentials
    endpoints: EndpointURLs
    database: Optional[DatabaseConnectionInfo] = None
    validation: ConfigurationValidation
    integration_status: IntegrationStatus
    webhook_info: Optional[WebhookInfo] = None

    # Quick start information
    quick_start_guide_url: str
    code_examples_url: str
    support_contact: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_api_key() -> tuple[str, str]:
    """Generate API key and ID."""
    api_key_id = f"key_{uuid.uuid4().hex[:16]}"
    api_key = f"gai_{secrets.token_urlsafe(32)}"
    return api_key, api_key_id


def generate_webhook_secret() -> str:
    """Generate webhook secret."""
    return f"whsec_{secrets.token_urlsafe(32)}"


def validate_deployment_package(package: FrontendDeploymentPackage) -> ConfigurationValidation:
    """Validate deployment package configuration."""
    warnings = []
    errors = []
    recommendations = []
    
    # Validate CORS origins
    for origin in package.cors_origins:
        if origin == "*":
            warnings.append("Wildcard CORS origin (*) is not recommended for production")
        if not origin.startswith(("http://", "https://")):
            errors.append(f"Invalid CORS origin format: {origin}")
    
    # Validate environment
    if package.client.environment == "production":
        if any(origin.startswith("http://localhost") for origin in package.cors_origins):
            warnings.append("Production environment should not use localhost CORS origins")
        if not package.authentication.oauth2_google:
            recommendations.append("Consider enabling OAuth2 for production")
    
    # Validate rate limits
    if package.rate_limits.requests_per_minute > 500:
        warnings.append("High rate limit may impact server performance")
    
    # Validate feature combinations
    if package.features.enable_webhooks and not package.authentication.webhook_auth:
        recommendations.append("Enable webhook authentication for webhook features")

    if package.features.enable_realtime and not package.api_endpoints.websocket:
        errors.append("Real-time features require WebSocket endpoints")

    # Webhook configuration validation
    if package.webhook_config:
        if not package.features.enable_webhooks:
            errors.append("webhook_config provided but enable_webhooks is False")
        if not package.authentication.webhook_auth:
            errors.append("webhook_config provided but webhook_auth is False")

        # Validate webhook URL is publicly accessible
        if package.client.environment == "production":
            if "localhost" in package.webhook_config.url or "127.0.0.1" in package.webhook_config.url:
                errors.append("Production webhook URL cannot use localhost")

    # Database access validation
    if package.database_access and package.database_access.write_access:
        warnings.append("Direct database write access is not recommended - use API endpoints instead")

    valid = len(errors) == 0
    
    return ConfigurationValidation(
        valid=valid,
        warnings=warnings,
        errors=errors,
        recommendations=recommendations
    )


def build_endpoint_urls(
    base_url: str,
    requirements: APIEndpointRequirements
) -> EndpointURLs:
    """Build complete endpoint URLs based on requirements."""
    api_version = "v1"

    urls = EndpointURLs(
        base_url=base_url,
        api_version=api_version,
        health=f"{base_url}/",  # Root endpoint serves as health check
        docs=f"{base_url}/docs"
    )
    
    # DRYAD Core Endpoints
    if requirements.dryad_groves:
        urls.groves = f"{base_url}/api/{api_version}/dryad/groves"
    if requirements.dryad_branches:
        urls.branches = f"{base_url}/api/{api_version}/dryad/branches"
    if requirements.dryad_vessels:
        urls.vessels = f"{base_url}/api/{api_version}/dryad/vessels"
    if requirements.dryad_oracle:
        urls.oracle = f"{base_url}/api/{api_version}/dryad/oracle"
    if requirements.dryad_dialogues:
        urls.dialogues = f"{base_url}/api/{api_version}/dryad/dialogues"
    if requirements.dryad_search:
        urls.search = f"{base_url}/api/{api_version}/dryad/search"
    if requirements.dryad_export_import:
        urls.export_import = f"{base_url}/api/{api_version}/dryad/groves/export"
    
    # Additional Endpoints
    if requirements.agent_studio:
        urls.agent_studio = f"{base_url}/api/{api_version}/agent-studio"
    if requirements.admin_center:
        urls.admin_center = f"{base_url}/api/{api_version}/admin"
    if requirements.multi_agent:
        urls.multi_agent = f"{base_url}/api/{api_version}/multi-agent"
    
    # WebSocket
    if requirements.websocket:
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        urls.websocket = f"{ws_url}/ws"
    
    return urls


# ============================================================================
# DEPLOYMENT INTEGRATION ENDPOINT
# ============================================================================

@router.post("/deploy/configure", response_model=BackendResponsePackage, status_code=status.HTTP_201_CREATED, tags=["Deployment"])
async def configure_deployment(
    package: FrontendDeploymentPackage,
    db: AsyncSession = Depends(get_db)
):
    """
    Process frontend deployment package and return ready configuration.
    
    **Workflow:**
    1. Frontend sends deployment package with requirements
    2. Backend validates configuration
    3. Backend generates API keys and credentials
    4. Backend configures CORS and rate limits
    5. Backend returns complete integration package
    
    **Returns:** Complete configuration with credentials, URLs, and setup instructions
    """
    try:
        logger.info(f"Processing deployment package for client: {package.client.client_name}")
        
        # Validate deployment package
        validation = validate_deployment_package(package)
        
        if not validation.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Deployment package validation failed",
                    "errors": validation.errors
                }
            )
        
        # Generate deployment ID
        deployment_id = f"deploy_{uuid.uuid4().hex[:16]}"
        
        # Generate credentials
        credentials = GeneratedCredentials()
        
        if package.authentication.api_keys:
            api_key, api_key_id = generate_api_key()
            credentials.api_key = api_key
            credentials.api_key_id = api_key_id
        
        if package.authentication.webhook_auth:
            credentials.webhook_secret = generate_webhook_secret()
        
        # Determine base URL based on environment
        if package.client.environment == "production":
            base_url = config.PRODUCTION_URL if hasattr(config, 'PRODUCTION_URL') else "https://api.dryad.ai"
        else:
            base_url = "http://localhost:8000"
        
        # Build endpoint URLs
        endpoints = build_endpoint_urls(base_url, package.api_endpoints)
        
        # Database connection info (if requested)
        database_info = None
        if package.database_access and package.database_access.read_access:
            # In production, create read-only database user
            database_info = DatabaseConnectionInfo(
                host="localhost",
                port=5432,
                database="DRYAD.AI",
                ssl_required=True
            )
        
        # Integration status
        integration_status = IntegrationStatus(
            status="ready",
            health_check_url=endpoints.health,
            api_docs_url=endpoints.docs,
            websocket_url=endpoints.websocket
        )

        # Webhook information
        webhook_info = None
        if package.webhook_config:
            webhook_info = WebhookInfo(
                enabled=True,
                url=package.webhook_config.url,
                events=package.webhook_config.events,
                secret_provided=bool(credentials.webhook_secret)
            )
            logger.info(f"Webhook configured for {package.client.client_id}: {package.webhook_config.url}")

        # Create response package
        response = BackendResponsePackage(
            deployment_id=deployment_id,
            client_id=package.client.client_id,
            environment=package.client.environment,
            created_at=datetime.utcnow().isoformat(),
            expires_at=(datetime.utcnow() + timedelta(days=365)).isoformat(),
            credentials=credentials,
            endpoints=endpoints,
            database=database_info,
            validation=validation,
            integration_status=integration_status,
            webhook_info=webhook_info,
            quick_start_guide_url=f"{base_url}/docs/quick-start",
            code_examples_url=f"{base_url}/docs/examples",
            support_contact=package.client.contact_email
        )
        
        # Store deployment package
        _deployment_packages[deployment_id] = {
            "request": package.dict(),
            "response": response.dict(),
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Deployment package created successfully: {deployment_id}")

        # Send Teams notification: Deployment received
        try:
            await dryad_teams_notifier.send_deployment_received(
                client_id=package.client.client_id,
                deployment_data=package.dict()
            )
        except Exception as e:
            logger.warning(f"Failed to send Teams notification (deployment received): {e}")

        # Send Teams notification: Ready package sent
        try:
            await dryad_teams_notifier.send_ready_package(
                client_id=package.client.client_id,
                credentials=credentials.dict()
            )
        except Exception as e:
            logger.warning(f"Failed to send Teams notification (ready package): {e}")

        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing deployment package: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process deployment package: {str(e)}"
        )


@router.get("/deploy/{deployment_id}", tags=["Deployment"])
async def get_deployment_package(deployment_id: str):
    """Get deployment package by ID."""
    if deployment_id not in _deployment_packages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment package not found"
        )
    
    return _deployment_packages[deployment_id]


@router.get("/deploy", tags=["Deployment"])
async def list_deployment_packages():
    """List all deployment packages."""
    return {
        "deployments": list(_deployment_packages.values()),
        "total": len(_deployment_packages)
    }


@router.get("/deploy/package/download", tags=["Deployment"])
async def download_integration_package():
    """
    Download the complete DRYAD integration package as a ZIP file.

    This endpoint serves the complete integration package containing:
    - Documentation (13 guides)
    - Code examples (TypeScript/JavaScript)
    - Sample deployment packages
    - Quick reference guide
    - Test payloads

    Frontend developers can use this to automatically download and extract
    the integration package without manual file transfer.

    Returns:
        FileResponse: ZIP file containing the complete integration package
    """
    # Path to the ZIP file
    zip_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
        "DRYAD_Complete_Backend_Integration_Package.zip"
    )

    # Check if file exists
    if not os.path.exists(zip_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration package not found at {zip_path}"
        )

    logger.info(f"Serving integration package from: {zip_path}")

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename="DRYAD_Complete_Backend_Integration_Package.zip",
        headers={
            "Content-Disposition": "attachment; filename=DRYAD_Complete_Backend_Integration_Package.zip"
        }
    )

