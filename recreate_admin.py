import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import get_password_hash
from datetime import datetime

async def recreate_admin():
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.db_name]
    
    # Delete old admin
    result = await db[settings.users_collection].delete_one({'email': 'admin@iasuuwu.com'})
    print(f'Deleted old admin: {result.deleted_count} records')
    
    # Create new admin with fresh password
    new_password = 'Admin@123'
    admin_doc = {
        'email': 'admin@iasuuwu.com',
        'full_name': 'IAS Admin',
        'hashed_password': get_password_hash(new_password),
        'is_active': True,
        'is_superuser': True,
        'created_at': datetime.utcnow(),
    }
    
    result = await db[settings.users_collection].insert_one(admin_doc)
    
    print('\n✅ NEW ADMIN CREATED')
    print('='*50)
    print(f'Email:    admin@iasuuwu.com')
    print(f'Password: {new_password}')
    print(f'ID:       {result.inserted_id}')
    print('='*50)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(recreate_admin())
