from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from app.schemas.comment import CommentCreate, CommentUpdate, CommentOut
from app.db.mongo import get_db
from app.core.config import settings
from app.api.dependencies import get_current_active_user, get_current_user_optional
from app.schemas.user import UserInDB
from bson import ObjectId
from typing import Optional

router = APIRouter()

@router.post("/", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: CommentCreate,
    db = Depends(get_db),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """Create a new comment on an article (guest-friendly or authenticated)."""
    try:
        # Check if article exists
        try:
            article_oid = ObjectId(comment.article_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid article id")

        article = await db[settings.articles_collection].find_one({"_id": article_oid})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        author_name = comment.author or (current_user.full_name if current_user else "Guest")
        author_email = comment.author_email or (current_user.email if current_user else None)
        author_id = current_user.id if current_user else None

        comment_dict = {
            "content": comment.content,
            "article_id": comment.article_id,
            "author": author_name,
            "author_email": author_email,
            "author_id": author_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await db[settings.comments_collection].insert_one(comment_dict)
        comment_dict["_id"] = result.inserted_id

        # Convert _id to id
        comment_dict["id"] = str(comment_dict.pop("_id"))

        return comment_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/article/{article_id}", response_model=List[CommentOut])
async def get_article_comments(
    article_id: str,
    db = Depends(get_db)
):
    """Get all comments for an article"""
    try:
        cursor = db[settings.comments_collection].find({"article_id": article_id}).sort("created_at", -1)
        comments = await cursor.to_list(100)
        
        for comment in comments:
            comment["id"] = str(comment.pop("_id"))
        
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my/comments", response_model=List[CommentOut])
async def get_my_comments(
    current_user: UserInDB = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Get all comments by current user"""
    try:
        cursor = db[settings.comments_collection].find(
            {"author_id": current_user.id}
        ).sort("created_at", -1)
        comments = await cursor.to_list(100)
        
        for comment in comments:
            comment["id"] = str(comment.pop("_id"))
        
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{comment_id}", response_model=CommentOut)
async def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Update a comment"""
    try:
        existing_comment = await db[settings.comments_collection].find_one({"_id": ObjectId(comment_id)})
        if not existing_comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Check if user is the author
        if existing_comment["author_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
        
        update_data = {
            "content": comment_update.content,
            "updated_at": datetime.utcnow()
        }
        
        await db[settings.comments_collection].update_one(
            {"_id": ObjectId(comment_id)},
            {"$set": update_data}
        )
        
        updated_comment = await db[settings.comments_collection].find_one({"_id": ObjectId(comment_id)})
        updated_comment["id"] = str(updated_comment.pop("_id"))
        
        return updated_comment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Delete a comment"""
    try:
        existing_comment = await db[settings.comments_collection].find_one({"_id": ObjectId(comment_id)})
        if not existing_comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Check if user is the author or admin
        if existing_comment["author_id"] != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
        
        await db[settings.comments_collection].delete_one({"_id": ObjectId(comment_id)})
        
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
