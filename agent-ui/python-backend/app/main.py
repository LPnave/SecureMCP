"""
FastAPI application entry point for the sanitization service
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router, set_validator
from app.core.config import settings
from app.core.security import ZeroShotSecurityValidator
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI
    Handles model loading on startup and cleanup on shutdown
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting SecureMCP Python Backend")
    logger.info("=" * 60)
    logger.info(f"Loading ML models...")
    
    start = time.time()
    try:
        # Initialize the security validator with ML models
        validator = ZeroShotSecurityValidator(settings.security_level)
        set_validator(validator)
        
        load_time = time.time() - start
        logger.info(f"✓ Models loaded successfully in {load_time:.2f} seconds")
        logger.info(f"✓ Security level: {settings.security_level.value}")
        logger.info(f"✓ CORS origins: {settings.cors_origins_list}")
        logger.info(f"✓ Server: {settings.HOST}:{settings.PORT}")
        logger.info("=" * 60)
        logger.info("Server ready to accept requests!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Failed to load models: {e}")
        logger.error("Server starting without models - health checks will fail")
    
    yield
    
    # Shutdown
    logger.info("Shutting down server...")


# Create FastAPI application
app = FastAPI(
    title="SecureMCP Sanitization API",
    description="ML-based prompt sanitization service with zero-shot classification",
    version="1.0.0",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SecureMCP Sanitization API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
