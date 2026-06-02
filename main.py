"""Application entry point - FastAPI application initialization"""

from app import app

if __name__ == "__main__":
    import uvicorn
    from app.config.settings import settings
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
