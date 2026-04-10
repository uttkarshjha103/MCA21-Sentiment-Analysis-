"""
Clean up test database.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup_database():
    """Clean up test database."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["mca21_sentiment_analysis"]
    
    try:
        # Delete all users
        result = await db.users.delete_many({})
        print(f"✓ Deleted {result.deleted_count} users")
        
        # Delete all comments
        result = await db.comments.delete_many({})
        print(f"✓ Deleted {result.deleted_count} comments")
        
        print("✅ Database cleaned up")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    print("Cleaning up database...")
    asyncio.run(cleanup_database())