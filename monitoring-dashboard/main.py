from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
import httpx
import asyncio
from typing import Dict, List
import os
import shutil

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

MONITORING_TOOLS = {
    "grafana": {
        "name": "Grafana", 
        "url": "http://grafana:3000", 
        "port": 3000, 
        "embed_path": "/d/didservices/dididentity-services?orgId=1&refresh=5s&kiosk=tv&theme=light",
        "embed_alternatives": [
            "/d-solo/didservices/dididentity-services?orgId=1&refresh=5s&kiosk=tv&theme=light&panelId=2",
            "/d/didservices/dididentity-services?orgId=1&refresh=5s&kiosk",
            "/d/didservices/dididentity-services?orgId=1&kiosk=tv",
            "/d/didservices/dididentity-services?orgId=1"
        ]
    },
    "prometheus": {"name": "Prometheus", "url": "http://prometheus:9090", "port": 9090, "embed_path": "/graph"},
    "jaeger": {"name": "Jaeger", "url": "http://jaeger:16686", "port": 16686, "embed_path": "/search?service=auth-service"},
    "rabbitmq": {"name": "RabbitMQ", "url": "http://rabbitmq:15672", "port": 15672, "embed_path": "/"},
}

async def check_service_health(service_name: str, service_info: Dict) -> Dict:
    """Check if a service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_info['url']}/health")
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": service_info["name"],
                    "status": "healthy",
                    "details": data,
                    "port": service_info["port"]
                }
    except Exception as e:
        pass
    
    return {
        "name": service_info["name"],
        "status": "unhealthy",
        "details": {"error": str(e) if 'e' in locals() else "Service unavailable"},
        "port": service_info["port"]
    }

async def check_monitoring_tool_health(tool_name: str, tool_info: Dict) -> Dict:
    """Check if a monitoring tool is accessible"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # For RabbitMQ, we need basic auth
            headers = {}
            if tool_name == "rabbitmq":
                headers = {"Authorization": "Basic Z3Vlc3Q6Z3Vlc3Q="}  # guest:guest in base64
            
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
                
                # Add additional RabbitMQ information
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
                                "management_version": api_data.get("management_version", "Unknown")
                            }
                            
                            # Get queue information
                            queues_response = await client.get(f"{tool_info['url']}/api/queues", headers=headers)
                            if queues_response.status_code == 200:
                                queues_data = queues_response.json()
                                result["rabbitmq_info"]["total_queues"] = len(queues_data)
                                result["rabbitmq_info"]["total_messages"] = sum(q.get("messages", 0) for q in queues_data)
                                
                    except Exception as e:
                        # API access failed, but basic connection works
                        result["rabbitmq_info"] = {"error": "API access limited", "note": "Management UI available"}
                
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
    service_health_tasks = [
        check_service_health(name, info) 
        for name, info in SERVICES.items()
    ]
    services_health = await asyncio.gather(*service_health_tasks)
    
    # Check monitoring tools health
    monitoring_health_tasks = [
        check_monitoring_tool_health(name, info)
        for name, info in MONITORING_TOOLS.items()
    ]
    monitoring_health = await asyncio.gather(*monitoring_health_tasks)
    
    # Count healthy services
    healthy_services = sum(1 for s in services_health if s["status"] == "healthy")
    healthy_monitoring = sum(1 for m in monitoring_health if m["status"] == "healthy")
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "services": services_health,
        "monitoring_tools": monitoring_health,
        "healthy_services": healthy_services,
        "total_services": len(services_health),
        "healthy_monitoring": healthy_monitoring,
        "total_monitoring": len(monitoring_health)
    })

@app.get("/api/health")
async def health_check():
    """Health check endpoint for the dashboard itself"""
    return {"status": "healthy", "service": "monitoring-dashboard"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)