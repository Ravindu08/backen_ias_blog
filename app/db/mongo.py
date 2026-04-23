from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

_client: AsyncIOMotorClient | None = None
_db = None

async def connect_to_mongo():
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _db = _client[settings.db_name]

async def close_mongo_connection():
    global _client
    if _client:
        _client.close()

def get_db():
    return _db
