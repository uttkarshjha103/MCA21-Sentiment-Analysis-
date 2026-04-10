"""
Dashboard Service for aggregating analytics data from MongoDB.
Provides sentiment distribution, trend analysis, word cloud, and topic cluster data.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.cache import dashboard_cache, keyword_cache

logger = logging.getLogger(__name__)


class DashboardService:
    """Aggregates dashboard analytics from MongoDB using Motor async queries."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.comments = db["comments"]

    # ------------------------------------------------------------------
    # Task 8.1 – Stats and Trends
    # ------------------------------------------------------------------

    def _stats_cache_key(
        self,
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        sentiment: Optional[str],
        keywords: Optional[List[str]],
    ) -> str:
        kw_part = ",".join(sorted(keywords)) if keywords else ""
        df = date_from.isoformat() if date_from else ""
        dt = date_to.isoformat() if date_to else ""
        return f"stats:{df}:{dt}:{sentiment or ''}:{kw_part}"

    async def get_stats(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sentiment: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Return total comment count and sentiment distribution.
        Supports filtering by date range, sentiment label, and keywords.
        Validates: Requirements 6.1, 6.4, 6.5
        """
        # Check cache first (TTL 5 min)
        cache_key = self._stats_cache_key(date_from, date_to, sentiment, keywords)
        cached = dashboard_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return cached

        match: Dict[str, Any] = {}
        self._apply_filters(match, date_from, date_to, sentiment, keywords)

        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": "$sentiment.label",
                    "count": {"$sum": 1},
                }
            },
        ]

        cursor = self.comments.aggregate(pipeline)
        distribution: Dict[str, int] = {"positive": 0, "negative": 0, "neutral": 0}
        async for doc in cursor:
            label = doc["_id"] or "neutral"
            distribution[label] = doc["count"]

        total = sum(distribution.values())

        # Average confidence score
        conf_pipeline = [
            {"$match": {**match, "sentiment.confidence_score": {"$exists": True}}},
            {"$group": {"_id": None, "avg_confidence": {"$avg": "$sentiment.confidence_score"}}},
        ]
        avg_conf = 0.0
        async for doc in self.comments.aggregate(conf_pipeline):
            avg_conf = round(doc.get("avg_confidence", 0.0), 4)

        result = {
            "total_comments": total,
            "sentiment_distribution": distribution,
            "average_confidence": avg_conf,
            "filters_applied": {
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "sentiment": sentiment,
                "keywords": keywords,
            },
        }
        dashboard_cache.set(cache_key, result)
        return result

    async def get_trends(
        self,
        period: str = "day",
        days: int = 30,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sentiment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return sentiment counts grouped by time period (day/week/month).
        Validates: Requirements 6.2, 6.5
        """
        if date_from is None:
            date_from = datetime.utcnow() - timedelta(days=days)
        if date_to is None:
            date_to = datetime.utcnow()

        # Cache key for trends
        cache_key = f"trends:{period}:{date_from.isoformat()}:{date_to.isoformat()}:{sentiment or ''}"
        cached = dashboard_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return cached

        match: Dict[str, Any] = {
            "date_submitted": {"$gte": date_from, "$lte": date_to}
        }
        if sentiment:
            match["sentiment.label"] = sentiment

        # Build date truncation expression
        period_formats = {
            "day": "%Y-%m-%d",
            "week": "%Y-%U",
            "month": "%Y-%m",
        }
        date_format = period_formats.get(period, "%Y-%m-%d")

        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": {
                        "period": {
                            "$dateToString": {
                                "format": date_format,
                                "date": "$date_submitted",
                            }
                        },
                        "sentiment": "$sentiment.label",
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id.period": 1}},
        ]

        cursor = self.comments.aggregate(pipeline)
        # Collect into a nested dict: period -> sentiment -> count
        period_data: Dict[str, Dict[str, int]] = {}
        async for doc in cursor:
            p = doc["_id"]["period"]
            s = doc["_id"]["sentiment"] or "neutral"
            if p not in period_data:
                period_data[p] = {"positive": 0, "negative": 0, "neutral": 0}
            period_data[p][s] = doc["count"]

        # Convert to sorted list for chart consumption
        trend_points = [
            {
                "period": p,
                "positive": v.get("positive", 0),
                "negative": v.get("negative", 0),
                "neutral": v.get("neutral", 0),
                "total": sum(v.values()),
            }
            for p, v in sorted(period_data.items())
        ]

        result = {
            "period": period,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "data_points": trend_points,
        }
        dashboard_cache.set(cache_key, result)
        return result

    async def get_recent_comments(
        self,
        limit: int = 20,
        sentiment: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Return recent comments with their sentiment classifications.
        Validates: Requirements 6.4, 6.5
        """
        match: Dict[str, Any] = {}
        self._apply_filters(match, date_from, date_to, sentiment, keywords)

        cursor = (
            self.comments.find(
                match,
                {
                    "_id": 1,
                    "comment_text": 1,
                    "sentiment": 1,
                    "date_submitted": 1,
                    "source": 1,
                    "original_language": 1,
                },
            )
            .sort("date_submitted", -1)
            .limit(limit)
        )

        comments = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            comments.append(doc)

        return {"total": len(comments), "comments": comments}

    # ------------------------------------------------------------------
    # Task 8.2 – Visualization data
    # ------------------------------------------------------------------

    async def get_wordcloud_data(
        self,
        limit: int = 100,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sentiment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return word frequency data suitable for word cloud rendering.
        Validates: Requirements 6.3
        """
        df = date_from.isoformat() if date_from else ""
        dt = date_to.isoformat() if date_to else ""
        cache_key = f"wordcloud:{limit}:{df}:{dt}:{sentiment or ''}"
        cached = keyword_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return cached
        match: Dict[str, Any] = {"keywords": {"$exists": True, "$ne": []}}
        if date_from or date_to:
            match["date_submitted"] = {}
            if date_from:
                match["date_submitted"]["$gte"] = date_from
            if date_to:
                match["date_submitted"]["$lte"] = date_to
        if sentiment:
            match["sentiment.label"] = sentiment

        pipeline = [
            {"$match": match},
            {"$unwind": "$keywords"},
            {
                "$group": {
                    "_id": "$keywords.text",
                    "value": {"$sum": "$keywords.frequency"},
                    "avg_tfidf": {"$avg": "$keywords.tfidf_score"},
                }
            },
            {"$sort": {"value": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "text": "$_id",
                    "value": 1,
                    "avg_tfidf": {"$round": ["$avg_tfidf", 4]},
                }
            },
        ]

        words = []
        async for doc in self.comments.aggregate(pipeline):
            words.append(doc)

        wordcloud_result = {"words": words, "total_words": len(words)}
        keyword_cache.set(cache_key, wordcloud_result)
        return wordcloud_result

    async def get_topic_clusters(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sentiment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return topic cluster visualization data.
        Validates: Requirements 6.3
        """
        match: Dict[str, Any] = {"keywords": {"$exists": True, "$ne": []}}
        if date_from or date_to:
            match["date_submitted"] = {}
            if date_from:
                match["date_submitted"]["$gte"] = date_from
            if date_to:
                match["date_submitted"]["$lte"] = date_to
        if sentiment:
            match["sentiment.label"] = sentiment

        pipeline = [
            {"$match": match},
            {"$unwind": "$keywords"},
            {"$match": {"keywords.topic_cluster": {"$exists": True, "$ne": None}}},
            {
                "$group": {
                    "_id": "$keywords.topic_cluster",
                    "keywords": {"$addToSet": "$keywords.text"},
                    "comment_count": {"$sum": 1},
                    "avg_tfidf": {"$avg": "$keywords.tfidf_score"},
                }
            },
            {"$sort": {"comment_count": -1}},
        ]

        clusters = []
        async for doc in self.comments.aggregate(pipeline):
            clusters.append(
                {
                    "cluster_id": doc["_id"],
                    "keywords": doc["keywords"][:20],  # cap for UI
                    "comment_count": doc["comment_count"],
                    "avg_tfidf": round(doc.get("avg_tfidf", 0.0), 4),
                }
            )

        return {"clusters": clusters, "total_clusters": len(clusters)}

    async def get_sentiment_chart_data(
        self,
        chart_type: str = "pie",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Return chart-ready data for sentiment distribution (pie/bar).
        Validates: Requirements 6.2
        """
        stats = await self.get_stats(date_from=date_from, date_to=date_to)
        dist = stats["sentiment_distribution"]

        labels = list(dist.keys())
        values = list(dist.values())
        colors = {
            "positive": "#4CAF50",
            "negative": "#F44336",
            "neutral": "#9E9E9E",
        }

        return {
            "chart_type": chart_type,
            "labels": labels,
            "datasets": [
                {
                    "data": values,
                    "backgroundColor": [colors.get(l, "#607D8B") for l in labels],
                }
            ],
            "total": stats["total_comments"],
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_filters(
        self,
        match: Dict[str, Any],
        date_from: Optional[datetime],
        date_to: Optional[datetime],
        sentiment: Optional[str],
        keywords: Optional[List[str]],
    ) -> None:
        """Mutate *match* dict in-place with common filter conditions."""
        if date_from or date_to:
            match["date_submitted"] = {}
            if date_from:
                match["date_submitted"]["$gte"] = date_from
            if date_to:
                match["date_submitted"]["$lte"] = date_to
        if sentiment:
            match["sentiment.label"] = sentiment
        if keywords:
            match["keywords.text"] = {"$in": keywords}
