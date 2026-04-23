"""
Script to create an admin user in the database
Run this once to create the admin account
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI", os.getenv("MONGO_URI"))
    db_name = os.getenv("DB_NAME", "ias_blog")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    # Admin credentials
    admin_email = "admin@iasuuwu.com"
    admin_password = "Admin@123"
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"email": admin_email})
    
    if existing_admin:
        print(f"Admin user already exists: {admin_email}")
        # Update to make sure they're admin
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"is_superuser": True, "is_active": True}}
        )
        print("Updated admin privileges")
    else:
        # Create admin user
        admin_user = {
            "email": admin_email,
            "full_name": "IAS UWU Admin",
            "hashed_password": pwd_context.hash(admin_password[:72]),
            "is_active": True,
            "is_superuser": True,
            "created_at": datetime.utcnow()
        }
        
        result = await db.users.insert_one(admin_user)
        print(f"Admin user created successfully!")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print(f"ID: {result.inserted_id}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin())
