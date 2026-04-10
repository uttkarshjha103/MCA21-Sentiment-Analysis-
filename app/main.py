"""
Main FastAPI application for MCA21 Sentiment Analysis System.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .core.config import settings
from .core.database import connect_to_mongo, close_mongo_connection
from .core.logging import setup_logging
from .core.exceptions import MCA21Exception

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting MCA21 Sentiment Analysis System")
    await connect_to_mongo()
    
    # Initialize audit log indexes
    from .core.database import get_database
    from .services.audit import AuditLogger
    try:
        db = get_database()
        audit_logger = AuditLogger(db)
        await audit_logger.create_indexes()
        logger.info("Audit log indexes initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize audit log indexes: {e}")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCA21 Sentiment Analysis System")
    await close_mongo_connection()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="MCA21 Sentiment Analysis System",
    description="AI-based Sentiment Analysis and Summarization System for MCA21 consultation comments",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(MCA21Exception)
async def mca21_exception_handler(request: Request, exc: MCA21Exception):
    """Handle custom MCA21 exceptions."""
    logger.error(f"MCA21 Exception: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": exc.message,
            "details": exc.details,
            "error_code": "MCA21_400"
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Validation error",
            "details": {"errors": exc.errors()},
            "error_code": "MCA21_422"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "details": {},
            "error_code": "MCA21_500"
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "timestamp": "2024-01-15T10:30:00Z"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "MCA21 Sentiment Analysis System API",
        "version": "1.0.0",
        "docs_url": "/docs" if settings.environment == "development" else None,
        "health_check": "/health"
    }


# Include API routers
from .api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )