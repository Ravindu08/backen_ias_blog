from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    profile_image: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class UserInDB(UserBase):
    id: str
    hashed_password: str
    bio: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime
