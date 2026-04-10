"""
Database connection and configuration for MongoDB using Motor async driver.
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database connection manager."""
    
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None


db = Database()


async def connect_to_mongo():
    """Create database connection."""
    try:
        db.client = AsyncIOMotorClient(settings.mongodb_url)
        db.database = db.client[settings.database_name]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {settings.mongodb_url}")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection."""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")


async def create_indexes():
    """Create database indexes for optimal performance."""
    try:
        # User collection indexes
        await db.database.users.create_index("email", unique=True)
        await db.database.users.create_index("created_at")
        
        # Comment collection indexes
        await db.database.comments.create_index("user_id")
        await db.database.comments.create_index("date_submitted")
        await db.database.comments.create_index("processed_at")
        await db.database.comments.create_index("sentiment.label")
        await db.database.comments.create_index("original_language")
        await db.database.comments.create_index("source")
        
        # Compound indexes for common queries
        await db.database.comments.create_index([
            ("user_id", 1),
            ("date_submitted", -1)
        ])
        await db.database.comments.create_index([
            ("sentiment.label", 1),
            ("date_submitted", -1)
        ])
        
        # Report collection indexes
        await db.database.reports.create_index("generated_by")
        await db.database.reports.create_index("generated_at")
        await db.database.reports.create_index("status")
        
        # Upload progress tracking collection indexes
        await db.database.upload_progress.create_index("upload_id", unique=True)
        await db.database.upload_progress.create_index("user_id")
        await db.database.upload_progress.create_index("created_at")
        await db.database.upload_progress.create_index("status")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"Failed to create some indexes: {e}")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    return db.database