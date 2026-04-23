from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import verify_token
from app.core.config import settings
from app.db.mongo import get_db
from app.schemas.user import UserInDB
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> UserInDB:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token and extract email
    email = verify_token(token)
    if email is None:
        raise credentials_exception
    
    # Find user in database
    user = await db[settings.users_collection].find_one({"email": email})
    if user is None:
        raise credentials_exception

    # Backward compatibility for legacy field name
    if "is_active" not in user and "isActive" in user:
        user["is_active"] = user.get("isActive")
    
    # Convert MongoDB _id to string id
    user["id"] = str(user.pop("_id"))
    
    return UserInDB(**user)

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get current active user (not disabled)"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db=Depends(get_db)
) -> Optional[UserInDB]:
    """Get current user if token is present and valid, else return None."""
    if not token:
        return None

    email = verify_token(token)
    if email is None:
        return None

    user = await db[settings.users_collection].find_one({"email": email})
    if user is None:
        return None

    # Backward compatibility for legacy field name
    if "is_active" not in user and "isActive" in user:
        user["is_active"] = user.get("isActive")

    user["id"] = str(user.pop("_id"))
    return UserInDB(**user)

async def get_current_superuser(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    """Get current superuser (admin)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
