"""
Dashboard API endpoints for analytics, visualization, and real-time updates.
Provides aggregated stats, trends, word cloud, recent comments, and topic clusters.
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.cache import dashboard_cache, keyword_cache
from app.services.dashboard import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_dashboard_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> DashboardService:
    return DashboardService(db)


# ---------------------------------------------------------------------------
# Task 8.1 – Aggregation endpoints
# ---------------------------------------------------------------------------

@router.get("/stats", summary="Comment statistics and sentiment distribution")
async def get_stats(
    date_from: Optional[datetime] = Query(None, description="Filter from date (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO 8601)"),
    sentiment: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$"),
    keywords: Optional[List[str]] = Query(None, description="Filter by keyword list"),
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Return total comment count and sentiment distribution.
    Supports filtering by date range, sentiment label, and keywords.

    **Validates: Requirements 6.1, 6.4, 6.5**
    """
    return await service.get_stats(
        date_from=date_from,
        date_to=date_to,
        sentiment=sentiment,
        keywords=keywords,
    )


@router.get("/trends", summary="Sentiment trends over time")
async def get_trends(
    period: str = Query("day", pattern="^(day|week|month)$", description="Grouping period"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back (ignored if date_from set)"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sentiment: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$"),
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Return sentiment counts grouped by day/week/month for trend charts.

    **Validates: Requirements 6.2, 6.5**
    """
    return await service.get_trends(
        period=period,
        days=days,
        date_from=date_from,
        date_to=date_to,
        sentiment=sentiment,
    )


@router.get("/recent", summary="Recent comments with sentiment")
async def get_recent_comments(
    limit: int = Query(20, ge=1, le=100),
    sentiment: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    keywords: Optional[List[str]] = Query(None),
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Return the most recent comments with their sentiment classifications.

    **Validates: Requirements 6.4, 6.5**
    """
    return await service.get_recent_comments(
        limit=limit,
        sentiment=sentiment,
        date_from=date_from,
        date_to=date_to,
        keywords=keywords,
    )


# ---------------------------------------------------------------------------
# Task 8.2 – Visualization data endpoints
# ---------------------------------------------------------------------------

@router.get("/wordcloud", summary="Word cloud frequency data")
async def get_wordcloud(
    limit: int = Query(100, ge=10, le=500),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sentiment: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$"),
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Return word frequency data for word cloud rendering.
    Each item has `text` and `value` (frequency) fields.

    **Validates: Requirements 6.3**
    """
    return await service.get_wordcloud_data(
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        sentiment=sentiment,
    )


@router.get("/topics", summary="Topic cluster visualization data")
async def get_topics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sentiment: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$"),
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Return topic cluster data for visualization.

    **Validates: Requirements 6.3**
    """
    return await service.get_topic_clusters(
        date_from=date_from,
        date_to=date_to,
        sentiment=sentiment,
    )


@router.get("/chart/sentiment", summary="Chart-ready sentiment distribution data")
async def get_sentiment_chart(
    chart_type: str = Query("pie", pattern="^(pie|bar|doughnut)$"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Return Chart.js-compatible sentiment distribution data.

    **Validates: Requirements 6.2**
    """
    return await service.get_sentiment_chart_data(
        chart_type=chart_type,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/cache/stats", summary="In-memory cache statistics")
async def get_cache_stats():
    """
    Return hit/miss statistics for the in-memory dashboard and keyword caches.

    **Validates: Requirements 9.1, 9.5**
    """
    return {
        "dashboard_cache": dashboard_cache.stats(),
        "keyword_cache": keyword_cache.stats(),
    }


@router.delete("/cache", summary="Invalidate dashboard caches", status_code=204)
async def invalidate_cache():
    """
    Clear all in-memory dashboard and keyword caches.
    Useful after bulk data imports to force fresh aggregations.

    **Validates: Requirements 9.1, 9.5**
    """
    dashboard_cache.clear()
    keyword_cache.clear()
    return None


# ---------------------------------------------------------------------------
# Task 8.2 – WebSocket for real-time updates (Requirement 6.6)
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Manages active WebSocket connections for real-time dashboard updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.

    Clients connect and receive live updates when new comments are processed.
    The server sends a snapshot of current stats on connect, then pushes
    incremental updates as data changes.

    **Validates: Requirements 6.6**
    """
    db = get_database()
    service = DashboardService(db)

    await manager.connect(websocket)
    try:
        # Send initial stats snapshot on connect
        stats = await service.get_stats()
        await websocket.send_json({"event": "snapshot", "data": stats})

        # Keep connection alive; listen for client messages (e.g. filter changes)
        while True:
            data = await websocket.receive_json()
            event = data.get("event", "")

            if event == "get_stats":
                filters = data.get("filters", {})
                result = await service.get_stats(
                    date_from=_parse_dt(filters.get("date_from")),
                    date_to=_parse_dt(filters.get("date_to")),
                    sentiment=filters.get("sentiment"),
                    keywords=filters.get("keywords"),
                )
                await websocket.send_json({"event": "stats", "data": result})

            elif event == "get_trends":
                filters = data.get("filters", {})
                result = await service.get_trends(
                    period=filters.get("period", "day"),
                    days=int(filters.get("days", 30)),
                    date_from=_parse_dt(filters.get("date_from")),
                    date_to=_parse_dt(filters.get("date_to")),
                )
                await websocket.send_json({"event": "trends", "data": result})

            elif event == "ping":
                await websocket.send_json({"event": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 datetime string, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
