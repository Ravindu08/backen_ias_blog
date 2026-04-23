"""
Script to add admin user
Run: python add_admin_user.py
"""

import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_admin_user():
    """Add admin user to MongoDB"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.mongo_uri)
        db = client[settings.db_name]
        
        logger.info("Connected to MongoDB")
        
        # Check if admin already exists
        admin = await db[settings.users_collection].find_one({"email": "admin@iasuuwu.com"})
        if admin:
            logger.warning("❌ Admin user already exists!")
            logger.info(f"Email: {admin['email']}")
            logger.info(f"Name: {admin['full_name']}")
            client.close()
            return
        
        # Create admin user
        admin_doc = {
            "email": "admin@iasuuwu.com",
            "full_name": "IAS Admin",
            "hashed_password": get_password_hash("passwordadmin"),
            "is_active": True,
            "is_superuser": True,
            "created_at": datetime.utcnow(),
        }
        
        result = await db[settings.users_collection].insert_one(admin_doc)
        
        logger.info("\n" + "="*60)
        logger.info("✅ ADMIN USER CREATED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info("\n🔐 Admin Login Credentials:")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"  📧 Email:    admin@iasuuwu.com")
        logger.info(f"  🔑 Password: passwordadmin")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"\n✨ User ID: {result.inserted_id}")
        logger.info("\n✅ You can now login to the admin dashboard!")
        logger.info("   Navigate to: http://localhost:5173/admin\n")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error adding admin user: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(add_admin_user())
