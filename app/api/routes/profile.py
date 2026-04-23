from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.profile import UserProfileUpdate, PasswordChange, UserProfileOut
from app.api.dependencies import get_current_active_user
from app.schemas.user import UserInDB
from app.core.security import get_password_hash, verify_password
from app.db.mongo import get_db
from app.core.config import settings
from bson import ObjectId

router = APIRouter()

@router.get("/me", response_model=UserProfileOut)
async def get_my_profile(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name or "",
        "bio": getattr(current_user, 'bio', ''),
        "profile_image": getattr(current_user, 'profile_image', None),
        "is_superuser": current_user.is_superuser
    }

@router.put("/me", response_model=UserProfileOut)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Update current user profile"""
    try:
        update_data = {}
        if profile_update.full_name is not None:
            update_data["full_name"] = profile_update.full_name
        if profile_update.bio is not None:
            update_data["bio"] = profile_update.bio
        if profile_update.profile_image is not None:
            update_data["profile_image"] = profile_update.profile_image
        
        if update_data:
            await db[settings.users_collection].update_one(
                {"_id": ObjectId(current_user.id)},
                {"$set": update_data}
            )
        
        updated_user = await db[settings.users_collection].find_one({"_id": ObjectId(current_user.id)})
        
        return {
            "id": str(updated_user["_id"]),
            "email": updated_user["email"],
            "full_name": updated_user.get("full_name", ""),
            "bio": updated_user.get("bio", ""),
            "profile_image": updated_user.get("profile_image"),
            "is_superuser": updated_user.get("is_superuser", False)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/me/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: PasswordChange,
    current_user: UserInDB = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Change current user password"""
    try:
        # Verify current password
        if not verify_password(password_change.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        new_hashed_password = get_password_hash(password_change.new_password)
        await db[settings.users_collection].update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": {"hashed_password": new_hashed_password}}
        )
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
