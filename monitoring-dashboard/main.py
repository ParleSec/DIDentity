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
    "grafana": {"name": "Grafana", "url": "http://grafana:3000", "port": 3000, "embed_path": "/d/didservices/dididentity-services?orgId=1&refresh=5s&kiosk"},
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
                return {
                    "name": tool_info["name"],
                    "status": "healthy",
                    "url": f"http://localhost:{tool_info['port']}",
                    "embed_url": f"http://localhost:{tool_info['port']}{tool_info.get('embed_path', '')}",
                    "port": tool_info["port"]
                }
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)