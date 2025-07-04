from fastapi import FastAPI, Request, HTTPException, Response, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
import httpx
import asyncio
from typing import Dict, List, Optional
import os
import shutil
import sys
import base64
import hashlib
import time
import uuid
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging
import random
import string

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add vault directory to Python path
sys.path.append('/app/vault')

try:
    from vault_client import VaultClient, VaultClientError
    vault_client = VaultClient()
    VAULT_AVAILABLE = True
except ImportError:
    print("Warning: Vault client not available, using fallback credentials")
    VAULT_AVAILABLE = False

app = FastAPI(title="DIDentity Monitoring Dashboard")

# Ensure templates and static directories exist
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Copy dashboard.html to templates if needed
if not os.path.exists("templates/dashboard.html") and os.path.exists("dashboard.html"):
    shutil.copy("dashboard.html", "templates/dashboard.html")

# Copy any static files if they exist in root
for static_file in ['favicon.ico', 'style.css', 'script.js']:
    if os.path.exists(static_file) and not os.path.exists(f"static/{static_file}"):
        shutil.copy(static_file, f"static/{static_file}")

# Templates directory
templates = Jinja2Templates(directory="templates")

# Mount static files with error handling
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"Warning: Could not mount static directory: {e}")

def get_rabbitmq_credentials():
    """Get RabbitMQ credentials from Vault or fallback"""
    if VAULT_AVAILABLE:
        try:
            rabbitmq_config = vault_client.get_rabbitmq_config()
            username = rabbitmq_config.get('username', 'admin')
            password = rabbitmq_config.get('password', 'guest')
            return username, password
        except VaultClientError as e:
            print(f"Warning: Could not retrieve RabbitMQ credentials from Vault: {e}")
    
    # Fallback to default credentials
    return 'guest', 'guest'

def get_grafana_credentials():
    """Get Grafana credentials from Vault or fallback"""
    if VAULT_AVAILABLE:
        try:
            grafana_config = vault_client.get_grafana_config()
            username = grafana_config.get('admin_user', 'admin')
            password = grafana_config.get('admin_password', 'admin')
            return username, password
        except VaultClientError as e:
            print(f"Warning: Could not retrieve Grafana credentials from Vault: {e}")
    
    # Fallback to default credentials
    return 'admin', 'admin'

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    if request.url.path.startswith("/static/"):
        return JSONResponse(
            status_code=404,
            content={"error": "Static file not found"}
        )
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "services": [],
            "monitoring_tools": [],
            "healthy_services": 0,
            "total_services": 0,
            "healthy_monitoring": 0,
            "total_monitoring": 0,
            "error": "Page not found"
        },
        status_code=404
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors"""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "services": [],
            "monitoring_tools": [],
            "healthy_services": 0,
            "total_services": 0,
            "healthy_monitoring": 0,
            "total_monitoring": 0,
            "error": "Internal server error"
        },
        status_code=500
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request", "details": exc.errors()}
    )

# Service endpoints
SERVICES = {
    "auth": {"name": "Auth Service", "url": "http://auth-service:8000", "port": 8004},
    "did": {"name": "DID Service", "url": "http://did-service:8000", "port": 8001},
    "credential": {"name": "Credential Service", "url": "http://credential-service:8000", "port": 8002},
    "verification": {"name": "Verification Service", "url": "http://verification-service:8000", "port": 8003},
}

# Service uptime tracking
SERVICE_UPTIME = {
    service_key: {"last_healthy": None, "uptime_start": None, "total_uptime": 0}
    for service_key in SERVICES.keys()
}

MONITORING_TOOLS = {
    "grafana": {
        "name": "Grafana", 
        "url": "http://grafana:3000", 
        "port": 3000, 
        "embed_path": "/d/did-services-overview/did-services-overview?orgId=1&refresh=5s&kiosk=tv&theme=light",
        "embed_alternatives": [
            "/d-solo/did-services-overview/did-services-overview?orgId=1&refresh=5s&kiosk=tv&theme=light&panelId=2",
            "/d/did-services-overview/did-services-overview?orgId=1&refresh=5s&kiosk",
            "/d/did-services-overview/did-services-overview?orgId=1&kiosk=tv",
            "/d/did-services-overview/did-services-overview?orgId=1"
        ]
    },
    "prometheus": {"name": "Prometheus", "url": "http://prometheus:9090", "port": 9090, "embed_path": "/graph"},
    "jaeger": {"name": "Jaeger", "url": "http://jaeger:16686", "port": 16686, "embed_path": "/search?service=auth-service"},
    "rabbitmq": {"name": "RabbitMQ", "url": "http://rabbitmq:15672", "port": 15672, "embed_path": "/"},
}

def format_uptime(uptime_seconds: float) -> str:
    """Format uptime in human-readable format"""
    if uptime_seconds < 60:
        return f"{uptime_seconds:.0f}s"
    elif uptime_seconds < 3600:
        return f"{uptime_seconds/60:.1f}m"
    elif uptime_seconds < 86400:
        return f"{uptime_seconds/3600:.1f}h"
    else:
        return f"{uptime_seconds/86400:.1f}d"

async def check_service_health(service_name: str, service_info: Dict) -> Dict:
    """Check if a service is healthy"""
    current_time = time.time()
    uptime_info = SERVICE_UPTIME[service_name]
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_info['url']}/health")
            if response.status_code == 200:
                data = response.json()
                
                # Update uptime tracking
                if uptime_info["uptime_start"] is None:
                    uptime_info["uptime_start"] = current_time
                
                uptime_info["last_healthy"] = current_time
                current_uptime = current_time - uptime_info["uptime_start"]
                
                return {
                    "name": service_info["name"],
                    "status": "healthy",
                    "details": data,
                    "port": service_info["port"],
                    "uptime": format_uptime(current_uptime),
                    "uptime_seconds": current_uptime
                }
    except Exception as e:
        # Service is unhealthy, reset uptime tracking
        uptime_info["uptime_start"] = None
        pass
    
    return {
        "name": service_info["name"],
        "status": "unhealthy",
        "details": {"error": str(e) if 'e' in locals() else "Service unavailable"},
        "port": service_info["port"],
        "uptime": "0s",
        "uptime_seconds": 0
    }

async def check_monitoring_tool_health(tool_name: str, tool_info: Dict) -> Dict:
    """Check if a monitoring tool is accessible"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # For RabbitMQ, we need basic auth with Vault credentials
            headers = {}
            if tool_name == "rabbitmq":
                username, password = get_rabbitmq_credentials()
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers = {"Authorization": f"Basic {credentials}"}
            
            response = await client.get(tool_info["url"], headers=headers, follow_redirects=True)
            if response.status_code in [200, 301, 302, 401]:  # 401 for RabbitMQ is expected
                result = {
                    "name": tool_info["name"],
                    "status": "healthy",
                    "url": f"http://localhost:{tool_info['port']}",
                    "embed_url": f"http://localhost:{tool_info['port']}{tool_info.get('embed_path', '')}",
                    "port": tool_info["port"]
                }
                
                # Add embed alternatives for Grafana
                if tool_name == "grafana" and "embed_alternatives" in tool_info:
                    result["embed_alternatives"] = [
                        f"http://localhost:{tool_info['port']}{alt_path}" 
                        for alt_path in tool_info["embed_alternatives"]
                    ]
                
                # Add additional RabbitMQ information with Vault credentials
                if tool_name == "rabbitmq":
                    try:
                        # Try to get basic API info
                        api_response = await client.get(f"{tool_info['url']}/api/overview", headers=headers)
                        if api_response.status_code == 200:
                            api_data = api_response.json()
                            result["rabbitmq_info"] = {
                                "version": api_data.get("rabbitmq_version", "Unknown"),
                                "erlang_version": api_data.get("erlang_version", "Unknown"),
                                "node_name": api_data.get("node", "Unknown"),
                                "management_version": api_data.get("management_version", "Unknown"),
                                "credentials_source": "Vault" if VAULT_AVAILABLE else "Default"
                            }
                            
                            # Get queue information
                            queues_response = await client.get(f"{tool_info['url']}/api/queues", headers=headers)
                            if queues_response.status_code == 200:
                                queues_data = queues_response.json()
                                result["rabbitmq_info"]["total_queues"] = len(queues_data)
                                result["rabbitmq_info"]["total_messages"] = sum(q.get("messages", 0) for q in queues_data)
                                
                    except Exception as e:
                        # API access failed, but basic connection works
                        result["rabbitmq_info"] = {
                            "error": "API access limited", 
                            "note": "Management UI available",
                            "credentials_source": "Vault" if VAULT_AVAILABLE else "Default"
                        }
                
                return result
    except Exception as e:
        pass
    
    return {
        "name": tool_info["name"],
        "status": "unhealthy",
        "url": f"http://localhost:{tool_info['port']}",
        "port": tool_info["port"],
        "error": str(e) if 'e' in locals() else "Tool unavailable"
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    # Check all services health in parallel
    service_tasks = [
        check_service_health(name, info) 
        for name, info in SERVICES.items()
    ]
    
    # Check all monitoring tools health in parallel
    monitoring_tasks = [
        check_monitoring_tool_health(name, info) 
        for name, info in MONITORING_TOOLS.items()
    ]
    
    # Execute all health checks concurrently
    try:
        services_results, monitoring_results = await asyncio.gather(
            asyncio.gather(*service_tasks),
            asyncio.gather(*monitoring_tasks)
        )
        
        # Calculate health statistics
        healthy_services = sum(1 for s in services_results if s["status"] == "healthy")
        total_services = len(services_results)
        healthy_monitoring = sum(1 for m in monitoring_results if m["status"] == "healthy")
        total_monitoring = len(monitoring_results)
        
        # Add Vault status information
        vault_status = None
        if VAULT_AVAILABLE:
            try:
                vault_status = vault_client.health_check()
            except Exception as e:
                vault_status = {"status": "unhealthy", "error": str(e)}
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "services": services_results,
                "monitoring_tools": monitoring_results,
                "healthy_services": healthy_services,
                "total_services": total_services,
                "healthy_monitoring": healthy_monitoring,
                "total_monitoring": total_monitoring,
                "vault_status": vault_status,
                "vault_available": VAULT_AVAILABLE
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "services": [],
                "monitoring_tools": [],
                "healthy_services": 0,
                "total_services": 0,
                "healthy_monitoring": 0,
                "total_monitoring": 0,
                "error": f"Dashboard error: {str(e)}",
                "vault_available": VAULT_AVAILABLE
            }
        )

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/services/health")
async def services_health():
    """Get health status of all services"""
    service_health_tasks = [
        check_service_health(name, info) 
        for name, info in SERVICES.items()
    ]
    return await asyncio.gather(*service_health_tasks)

@app.get("/api/monitoring/health")
async def monitoring_health():
    """Get health status of all monitoring tools"""
    monitoring_health_tasks = [
        check_monitoring_tool_health(name, info)
        for name, info in MONITORING_TOOLS.items()
    ]
    return await asyncio.gather(*monitoring_health_tasks)

@app.get("/api/services/uptime")
async def services_uptime():
    """Get service uptime statistics"""
    uptime_stats = {}
    for service_name, uptime_info in SERVICE_UPTIME.items():
        if uptime_info["uptime_start"] is not None:
            current_uptime = time.time() - uptime_info["uptime_start"]
            uptime_stats[service_name] = {
                "service": SERVICES[service_name]["name"],
                "uptime": format_uptime(current_uptime),
                "uptime_seconds": current_uptime,
                "started_at": datetime.fromtimestamp(uptime_info["uptime_start"]).strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            uptime_stats[service_name] = {
                "service": SERVICES[service_name]["name"],
                "uptime": "0s",
                "uptime_seconds": 0,
                "started_at": "Never"
            }
    return {"uptime_stats": uptime_stats}

@app.get("/api/rabbitmq/stats")
async def rabbitmq_stats():
    """Get detailed RabbitMQ statistics"""
    rabbitmq_info = MONITORING_TOOLS.get("rabbitmq")
    if not rabbitmq_info:
        return {"error": "RabbitMQ configuration not found", "status": "error"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Authorization": "Basic Z3Vlc3Q6Z3Vlc3Q="}  # guest:guest in base64
            
            # First, test basic connectivity
            try:
                basic_response = await client.get(f"{rabbitmq_info['url']}", headers=headers, follow_redirects=False)
                if basic_response.status_code == 404:
                    return {"error": "RabbitMQ Management UI not accessible", "status": "error", "status_code": 404}
            except Exception as e:
                return {"error": f"Cannot connect to RabbitMQ: {str(e)}", "status": "error"}
            
            # Get overview
            try:
                overview_response = await client.get(f"{rabbitmq_info['url']}/api/overview", headers=headers)
                
                if overview_response.status_code == 401:
                    return {"error": "Authentication failed - check RabbitMQ credentials", "status": "error", "status_code": 401}
                elif overview_response.status_code == 404:
                    return {"error": "RabbitMQ Management API not found", "status": "error", "status_code": 404}
                elif overview_response.status_code != 200:
                    return {"error": f"RabbitMQ API returned status {overview_response.status_code}", "status": "error", "status_code": overview_response.status_code}
                
                # Check if response is JSON
                content_type = overview_response.headers.get('content-type', '')
                if 'application/json' not in content_type:
                    return {"error": f"RabbitMQ API returned non-JSON response (content-type: {content_type})", "status": "error"}
                
                overview_data = overview_response.json()
                
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP error accessing RabbitMQ API: {e.response.status_code}", "status": "error", "status_code": e.response.status_code}
            except Exception as e:
                return {"error": f"Failed to parse RabbitMQ overview: {str(e)}", "status": "error"}
            
            # Initialize default values
            queues_data = []
            exchanges_data = []
            connections_data = []
            
            # Get queues (optional)
            try:
                queues_response = await client.get(f"{rabbitmq_info['url']}/api/queues", headers=headers)
                if queues_response.status_code == 200 and 'application/json' in queues_response.headers.get('content-type', ''):
                    queues_data = queues_response.json()
            except Exception as e:
                print(f"Warning: Could not fetch queues data: {e}")
            
            # Get exchanges (optional)
            try:
                exchanges_response = await client.get(f"{rabbitmq_info['url']}/api/exchanges", headers=headers)
                if exchanges_response.status_code == 200 and 'application/json' in exchanges_response.headers.get('content-type', ''):
                    exchanges_data = exchanges_response.json()
            except Exception as e:
                print(f"Warning: Could not fetch exchanges data: {e}")
            
            # Get connections (optional)
            try:
                connections_response = await client.get(f"{rabbitmq_info['url']}/api/connections", headers=headers)
                if connections_response.status_code == 200 and 'application/json' in connections_response.headers.get('content-type', ''):
                    connections_data = connections_response.json()
            except Exception as e:
                print(f"Warning: Could not fetch connections data: {e}")
            
            return {
                "status": "healthy",
                "overview": {
                    "rabbitmq_version": overview_data.get("rabbitmq_version", "Unknown"),
                    "erlang_version": overview_data.get("erlang_version", "Unknown"),
                    "node": overview_data.get("node", "Unknown"),
                    "management_version": overview_data.get("management_version", "Unknown"),
                    "uptime": overview_data.get("uptime", 0)
                },
                "statistics": {
                    "total_queues": len(queues_data),
                    "total_exchanges": len(exchanges_data),
                    "total_connections": len(connections_data),
                    "total_messages": sum(q.get("messages", 0) for q in queues_data),
                    "ready_messages": sum(q.get("messages_ready", 0) for q in queues_data),
                    "unacknowledged_messages": sum(q.get("messages_unacknowledged", 0) for q in queues_data)
                },
                "queues": [
                    {
                        "name": q.get("name", "Unknown"),
                        "vhost": q.get("vhost", "/"),
                        "messages": q.get("messages", 0),
                        "messages_ready": q.get("messages_ready", 0),
                        "messages_unacknowledged": q.get("messages_unacknowledged", 0),
                        "consumers": q.get("consumers", 0)
                    }
                    for q in queues_data[:10]  # Limit to first 10 queues
                ]
            }
            
    except httpx.ConnectError:
        return {"error": "Cannot connect to RabbitMQ - service may be down", "status": "error"}
    except httpx.TimeoutException:
        return {"error": "RabbitMQ connection timeout", "status": "error"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "status": "error"}

# Session management for secure authentication
class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.session_timeout = 3600  # 1 hour
    
    def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': time.time(),
            'last_accessed': time.time()
        }
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        if not session_id or session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        if time.time() - session['last_accessed'] > self.session_timeout:
            del self.sessions[session_id]
            return False
        
        session['last_accessed'] = time.time()
        return True
    
    def cleanup_expired_sessions(self):
        current_time = time.time()
        expired_sessions = [
            sid for sid, session in self.sessions.items() 
            if current_time - session['last_accessed'] > self.session_timeout
        ]
        for sid in expired_sessions:
            del self.sessions[sid]

session_manager = SessionManager()

# Authenticated HTTP client for reuse
class AuthenticatedClient:
    def __init__(self):
        self.grafana_client = None
        self.rabbitmq_client = None
        self.client_timeout = 300  # 5 minutes
        self.last_created = 0
    
    async def get_grafana_client(self):
        current_time = time.time()
        if (self.grafana_client is None or 
            current_time - self.last_created > self.client_timeout):
            
            username, password = get_grafana_credentials()
            auth = httpx.BasicAuth(username, password)
            self.grafana_client = httpx.AsyncClient(
                auth=auth,
                timeout=30.0,
                follow_redirects=True,
                headers={
                    'User-Agent': 'DIDentity-Monitoring-Dashboard/1.0'
                }
            )
            self.last_created = current_time
        return self.grafana_client
    
    async def get_rabbitmq_client(self):
        current_time = time.time()
        if (self.rabbitmq_client is None or 
            current_time - self.last_created > self.client_timeout):
            
            username, password = get_rabbitmq_credentials()
            auth = httpx.BasicAuth(username, password)
            self.rabbitmq_client = httpx.AsyncClient(
                auth=auth,
                timeout=30.0,
                follow_redirects=True,
                headers={
                    'User-Agent': 'DIDentity-Monitoring-Dashboard/1.0'
                }
            )
            self.last_created = current_time
        return self.rabbitmq_client
    
    async def close(self):
        if self.grafana_client:
            await self.grafana_client.aclose()
        if self.rabbitmq_client:
            await self.rabbitmq_client.aclose()

auth_client = AuthenticatedClient()

@app.on_event("shutdown")
async def shutdown_event():
    await auth_client.close()

# Secure proxy endpoints
@app.post("/api/auth/grafana")
async def authenticate_grafana(response: Response):
    """Create authenticated session for Grafana access"""
    try:
        username, password = get_grafana_credentials()
        
        # Test authentication
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "http://grafana:3000/api/user",
                auth=httpx.BasicAuth(username, password),
                timeout=10.0
            )
            
            if auth_response.status_code == 200:
                # Create session
                session_id = session_manager.create_session("grafana_user")
                
                # Set HTTP-only cookie
                response.set_cookie(
                    key="grafana_session",
                    value=session_id,
                    httponly=True,
                    secure=False,  # Set to True in production with HTTPS
                    samesite="strict",
                    max_age=3600  # 1 hour
                )
                
                return {"status": "authenticated", "expires_in": 3600}
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.post("/api/auth/rabbitmq")
async def authenticate_rabbitmq(response: Response):
    """Create authenticated session for RabbitMQ access"""
    try:
        username, password = get_rabbitmq_credentials()
        
        # Test authentication
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "http://rabbitmq:15672/api/overview",
                auth=httpx.BasicAuth(username, password),
                timeout=10.0
            )
            
            if auth_response.status_code == 200:
                # Create session
                session_id = session_manager.create_session("rabbitmq_user")
                
                # Set HTTP-only cookie
                response.set_cookie(
                    key="rabbitmq_session",
                    value=session_id,
                    httponly=True,
                    secure=False,  # Set to True in production with HTTPS
                    samesite="strict",
                    max_age=3600  # 1 hour
                )
                
                return {"status": "authenticated", "expires_in": 3600}
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/api/proxy/grafana/{path:path}")
async def proxy_grafana(path: str, request: Request, grafana_session: Optional[str] = Cookie(None)):
    """Secure proxy for Grafana with session-based auth"""
    if not session_manager.validate_session(grafana_session):
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    try:
        client = await auth_client.get_grafana_client()
        
        # Forward query parameters
        query_params = str(request.url.query)
        target_url = f"http://grafana:3000/{path}"
        if query_params:
            target_url += f"?{query_params}"
        
        # Forward the request
        response = await client.get(target_url)
        
        # Return response with appropriate content type
        content_type = response.headers.get("content-type", "text/html")
        
        if "text/html" in content_type:
            # For HTML responses, modify any absolute URLs to go through proxy
            content = response.text
            content = content.replace('href="/', 'href="/api/proxy/grafana/')
            content = content.replace('src="/', 'src="/api/proxy/grafana/')
            return Response(content=content, media_type=content_type)
        else:
            # For other content (CSS, JS, images, API responses)
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=content_type
            )
            
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")

@app.get("/api/proxy/rabbitmq/{path:path}")
async def proxy_rabbitmq(path: str, request: Request, rabbitmq_session: Optional[str] = Cookie(None)):
    """Secure proxy for RabbitMQ with session-based auth"""
    if not session_manager.validate_session(rabbitmq_session):
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    try:
        client = await auth_client.get_rabbitmq_client()
        
        # Forward query parameters
        query_params = str(request.url.query)
        target_url = f"http://rabbitmq:15672/{path}"
        if query_params:
            target_url += f"?{query_params}"
        
        # Forward the request
        response = await client.get(target_url)
        
        # Return response with appropriate content type
        content_type = response.headers.get("content-type", "text/html")
        
        if "text/html" in content_type:
            # For HTML responses, modify any absolute URLs to go through proxy
            content = response.text
            content = content.replace('href="/', 'href="/api/proxy/rabbitmq/')
            content = content.replace('src="/', 'src="/api/proxy/rabbitmq/')
            return Response(content=content, media_type=content_type)
        else:
            # For other content (CSS, JS, images, API responses)
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=content_type
            )
            
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")

@app.get("/api/auth/status")
async def auth_status(grafana_session: Optional[str] = Cookie(None), 
                     rabbitmq_session: Optional[str] = Cookie(None)):
    """Check authentication status for all services"""
    return {
        "grafana": session_manager.validate_session(grafana_session),
        "rabbitmq": session_manager.validate_session(rabbitmq_session)
    }

@app.post("/api/auth/logout")
async def logout(response: Response, grafana_session: Optional[str] = Cookie(None),
                rabbitmq_session: Optional[str] = Cookie(None)):
    """Logout and clear all sessions"""
    
    # Remove sessions
    if grafana_session and grafana_session in session_manager.sessions:
        del session_manager.sessions[grafana_session]
    if rabbitmq_session and rabbitmq_session in session_manager.sessions:
        del session_manager.sessions[rabbitmq_session]
    
    # Clear cookies
    response.delete_cookie("grafana_session")
    response.delete_cookie("rabbitmq_session")
    
    return {"status": "logged_out"}

# Background task to cleanup expired sessions
@app.on_event("startup")
async def startup_event():
    async def cleanup_sessions():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            session_manager.cleanup_expired_sessions()
    
    asyncio.create_task(cleanup_sessions())

@app.post("/api/test/workflow")
async def test_didientity_workflow():
    """Test the complete DIDentity workflow end-to-end"""
    try:
        timestamp = int(time.time())
        test_user = {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        
        results = {
            "user": test_user["username"],
            "steps": []
        }
        
        async with httpx.AsyncClient() as client:
            # Step 1: User Registration
            try:
                auth_response = await client.post(
                    "http://auth-service:8000/signup",
                    json=test_user,
                    timeout=30
                )
                if auth_response.status_code != 200:
                    raise Exception(f"Auth failed with status {auth_response.status_code}")
                auth_data = auth_response.json()
                token = auth_data["access_token"]
                results["steps"].append({"step": 1, "status": "success", "message": "User registration successful"})
            except Exception as e:
                results["steps"].append({"step": 1, "status": "error", "message": f"User registration failed: {str(e)}"})
                return {"status": "error", "results": results}
            
            # Step 2: DID Creation
            try:
                # Generate a valid Base58 identifier for the key method
                base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
                identifier = ''.join(random.choice(base58_chars) for _ in range(16))
                
                did_response = await client.post(
                    "http://did-service:8000/dids",
                    json={"method": "key", "identifier": identifier},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30
                )
                if did_response.status_code != 200:
                    raise Exception(f"DID creation failed with status {did_response.status_code}")
                did_data = did_response.json()
                did = did_data["id"]
                results["did"] = did
                results["steps"].append({"step": 2, "status": "success", "message": f"DID created: {did}"})
            except Exception as e:
                results["steps"].append({"step": 2, "status": "error", "message": f"DID creation failed: {str(e)}"})
                return {"status": "error", "results": results}
            
            # Step 3: Credential Issuance
            try:
                credential_data = {
                    "holder_did": did,
                    "credential_data": {
                        "name": "Test User",
                        "degree": "Bachelor of Science",
                        "institution": "DIDentity University",
                        "graduation_year": 2024
                    }
                }
                cred_response = await client.post(
                    "http://credential-service:8000/credentials/issue",
                    json=credential_data,
                    timeout=30
                )
                if cred_response.status_code != 200:
                    raise Exception(f"Credential issuance failed with status {cred_response.status_code}")
                cred_data = cred_response.json()
                credential_id = cred_data["credential_id"]
                results["credential"] = credential_id
                results["steps"].append({"step": 3, "status": "success", "message": f"Credential issued: {credential_id}"})
            except Exception as e:
                results["steps"].append({"step": 3, "status": "error", "message": f"Credential issuance failed: {str(e)}"})
                return {"status": "error", "results": results}
            
            # Step 4: Credential Verification
            try:
                verify_response = await client.post(
                    "http://verification-service:8000/credentials/verify",
                    json={"credential_id": credential_id},
                    timeout=30
                )
                if verify_response.status_code != 200:
                    raise Exception(f"Verification failed with status {verify_response.status_code}")
                verify_data = verify_response.json()
                results["verification"] = verify_data.get("status", "unknown")
                results["steps"].append({"step": 4, "status": "success", "message": "Credential verification successful"})
            except Exception as e:
                results["steps"].append({"step": 4, "status": "error", "message": f"Verification failed: {str(e)}"})
                return {"status": "error", "results": results}
        
        return {"status": "success", "results": results}
        
    except Exception as e:
        logger.error(f"Workflow test failed: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)