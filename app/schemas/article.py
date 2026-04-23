from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime

class ArticleBase(BaseModel):
    title: str
    category: str
    tags: List[str] = []
    featuredImage: Optional[HttpUrl] = None
    shortDescription: Optional[str] = None
    content: str

class ArticleCreate(ArticleBase):
    """Schema for creating a new article (user submits)"""
    pass

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    featuredImage: Optional[HttpUrl] = None
    shortDescription: Optional[str] = None
    content: Optional[str] = None
    isFeatured: Optional[bool] = None
    status: Optional[str] = None  # For admin to approve/reject

class ArticleOut(BaseModel):
    id: str
    slug: str
    title: str
    author: str  # Author name from user
    authorEmail: str  # Author email
    authorId: str  # User ID
    category: str
    tags: List[str]
    readingTime: str
    featuredImage: Optional[str] = None
    shortDescription: Optional[str] = None
    content: str
    status: str  # pending, approved, rejected
    isFeatured: bool = False
    # Accept snake_case from DB but expose camelCase to clients
    createdAt: datetime = Field(alias="created_at")
    updatedAt: datetime = Field(alias="updated_at")
    likesCount: int = 0
    viewCount: int = 0
    likes: List[str] = []  # List of IP/identifier of who liked

    class Config:
        from_attributes = True
        populate_by_name = True
