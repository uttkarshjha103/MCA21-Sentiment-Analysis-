"""
Main API router for version 1 of the MCA21 Sentiment Analysis System.
"""
from fastapi import APIRouter

# Create the main API router
api_router = APIRouter()

# Include individual route modules
from .endpoints import auth, audit, upload, sentiment, summarization, keywords, language, dashboard, comments
from .endpoints import reports

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["Sentiment Analysis"])
api_router.include_router(summarization.router, prefix="/summarization", tags=["Text Summarization"])
api_router.include_router(keywords.router, prefix="/keywords", tags=["Keyword Extraction"])
api_router.include_router(language.router, prefix="/language", tags=["Language Detection"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(comments.router, prefix="/comments", tags=["Comments"])

@api_router.get("/")
async def api_info():
    """API version information."""
    return {
        "message": "MCA21 Sentiment Analysis System API v1",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "audit": "/api/v1/audit",
            "upload": "/api/v1/upload",
            "sentiment": "/api/v1/sentiment",
            "summarization": "/api/v1/summarization",
            "comments": "/api/v1/comments",
            "analysis": "/api/v1/analysis",
            "reports": "/api/v1/reports",
            "dashboard": "/api/v1/dashboard"
        }
    }