"""Add sentiment labels to comments that are missing them."""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "mca21_sentiment_analysis"

# Keywords to determine sentiment
POSITIVE_WORDS = ['excellent', 'outstanding', 'wonderful', 'brilliant', 'great', 'love',
                  'support', 'appreciate', 'fantastic', 'impressive', 'commendable',
                  'happy', 'endorse', 'positive', 'welcome', 'good', 'best', 'well done',
                  'fully support', 'strongly support', 'progressive', 'timely']

NEGATIVE_WORDS = ['disaster', 'terrible', 'worst', 'oppose', 'disappointing', 'draconian',
                  'impossible', 'absurd', 'nightmare', 'harmful', 'unacceptable', 'bad',
                  'strongly oppose', 'deeply concerned', 'appalled', 'frustrated',
                  'destroy', 'hurt', 'burden', 'excessive', 'poor', 'wrong', 'fail']


def classify(text: str) -> dict:
    text_lower = text.lower()
    pos_score = sum(1 for w in POSITIVE_WORDS if w in text_lower)
    neg_score = sum(1 for w in NEGATIVE_WORDS if w in text_lower)

    if pos_score > neg_score:
        label = 'positive'
        confidence = min(0.95, 0.70 + pos_score * 0.05)
    elif neg_score > pos_score:
        label = 'negative'
        confidence = min(0.95, 0.70 + neg_score * 0.05)
    else:
        label = 'neutral'
        confidence = 0.65

    return {
        'label': label,
        'confidence_score': round(confidence, 2),
        'model_version': 'keyword-classifier-v1',
        'processed_at': datetime.utcnow()
    }


async def fix():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Find all comments without sentiment
    cursor = db.comments.find({'sentiment': {'$exists': False}})
    updated = 0
    async for doc in cursor:
        sentiment = classify(doc['comment_text'])
        await db.comments.update_one(
            {'_id': doc['_id']},
            {'$set': {'sentiment': sentiment, 'processed_at': datetime.utcnow()}}
        )
        updated += 1

    print(f"Updated {updated} comments with sentiment labels")

    # Show distribution
    pipeline = [{'$group': {'_id': '$sentiment.label', 'count': {'$sum': 1}}}]
    async for doc in db.comments.aggregate(pipeline):
        print(f"  {doc['_id']}: {doc['count']}")

    client.close()

asyncio.run(fix())
