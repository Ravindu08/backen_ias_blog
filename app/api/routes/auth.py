from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta, datetime
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.schemas.token import Token
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.db.mongo import get_db
from app.api.dependencies import get_current_active_user

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db=Depends(get_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await db[settings.users_collection].find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user document
        user_dict = {
            "email": user.email,
            "full_name": user.full_name,
            "profile_image": user.profile_image,
            "hashed_password": get_password_hash(user.password),
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.utcnow()
        }
        
        result = await db[settings.users_collection].insert_one(user_dict)
        
        # Return user without hashed_password
        return UserOut(
            id=str(result.inserted_id),
            email=user.email,
            full_name=user.full_name,
            profile_image=user.profile_image,
            is_active=True,
            is_superuser=False,
            created_at=user_dict["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db=Depends(get_db)):
    """Login and get access token"""
    # Find user by email
    user = await db[settings.users_collection].find_one({"email": user_credentials.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active (supports legacy isActive field)
    is_active = user.get("is_active")
    if is_active is None:
        is_active = user.get("isActive", True)
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserOut)
async def get_current_user_info(current_user=Depends(get_current_active_user)):
    """Get current user info (requires authentication)"""
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        profile_image=getattr(current_user, 'profile_image', None),
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at
    )
