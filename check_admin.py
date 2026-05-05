import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def check_admin():
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.db_name]
    
    # Check admin
    admin = await db[settings.users_collection].find_one({'email': 'admin@iasuuwu.com'})
    
    if admin:
        print('✅ Admin found:')
        print(f'   Email: {admin.get("email")}')
        print(f'   Name: {admin.get("full_name")}')
        print(f'   Active: {admin.get("is_active")}')
        print(f'   Superuser: {admin.get("is_superuser")}')
        print(f'   ID: {admin.get("_id")}')
    else:
        print('❌ Admin account NOT FOUND')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_admin())
