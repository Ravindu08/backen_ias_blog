from pydantic import BaseModel, EmailStr
from typing import Optional

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserProfileOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    is_superuser: bool = False

    class Config:
        from_attributes = True
