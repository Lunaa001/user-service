"""User Service - FastAPI Application"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.controllers import auth_controller, user_controller


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print(f"Starting User Service on {settings.host}:{settings.port}")
    print(f"Persistence Service URL: {settings.persistence_service_url}")

    # Register with Consul for Service Discovery
    # Tags are read from Consul KV automatically (no hardcoded labels)
    from app.consul_registration import register_service, deregister_service, fetch_kv_config
    kv_config = fetch_kv_config("user-service")
    if kv_config:
        # Override settings from Consul KV
        for key, value in kv_config.items():
            attr = key.lower()
            if hasattr(settings, attr):
                setattr(settings, attr, type(getattr(settings, attr))(value))

    register_service(
        service_name="user-service",
        service_port=settings.port,
        health_check_path="/health",
    )

    yield

    # Shutdown — deregister from Consul
    deregister_service("user-service", settings.port)
    print("Shutting down User Service")


# Initialize FastAPI application
app = FastAPI(
    title="User Service",
    description="Authentication and User Management Microservice for NotebookUM",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS Configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth_controller.router, prefix="/api/v1", tags=["auth"])
app.include_router(user_controller.router, prefix="/api/v1", tags=["users"])


# Health check endpoints
@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "user-service",
        "version": "1.0.0"
    }


@app.get("/ready", tags=["health"])
async def readiness():
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "service": "user-service"
    }


@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "User Service API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
