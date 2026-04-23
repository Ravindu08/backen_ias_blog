from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.core.config import settings
from app.db.mongo import get_db
from app.schemas.user import UserOut
from app.schemas.token import Token
from app.core.security import create_access_token
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

router = APIRouter()

@router.post("/google", response_model=Token)
async def google_login(request: Request, db=Depends(get_db)):
    """Login or register user with Google ID token"""
    data = await request.json()
    token = data.get("credential")
    if not token:
        raise HTTPException(status_code=400, detail="Missing Google credential")
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.google_client_id)
        email = idinfo["email"]
        full_name = idinfo.get("name", "")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")

    user = await db[settings.users_collection].find_one({"email": email})
    if not user:
        # Register new user
        user_dict = {
            "email": email,
            "full_name": full_name,
            "hashed_password": None,
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.utcnow()
        }
        result = await db[settings.users_collection].insert_one(user_dict)
        user = user_dict
        user["id"] = str(result.inserted_id)
    else:
        user["id"] = str(user["_id"])

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
