from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional
from datetime import datetime, timedelta
from app.schemas.user import UserInDB, UserOut
from app.api.dependencies import get_current_superuser
from app.db.mongo import get_db
from app.core.config import settings
from bson import ObjectId

router = APIRouter()

# ==================== DASHBOARD STATS ====================
@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_admin: UserInDB = Depends(get_current_superuser),
    db = Depends(get_db)
):
    """Get admin dashboard statistics"""
    try:
        # User stats
        total_users = await db[settings.users_collection].count_documents({})
        active_users = await db[settings.users_collection].count_documents({"is_active": True})
        admin_users = await db[settings.users_collection].count_documents({"is_superuser": True})
        
        # Get new users in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users = await db[settings.users_collection].count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Article stats
        total_articles = await db[settings.articles_collection].count_documents({})
        approved_articles = await db[settings.articles_collection].count_documents({"status": "approved"})
        pending_articles = await db[settings.articles_collection].count_documents({"status": "pending"})
        rejected_articles = await db[settings.articles_collection].count_documents({"status": "rejected"})
        featured_articles = await db[settings.articles_collection].count_documents({"isFeatured": True})
        
        # Comment stats
        total_comments = await db[settings.comments_collection].count_documents({})
        
        # Get recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_articles = await db[settings.articles_collection].count_documents({
            "createdAt": {"$gte": seven_days_ago}
        })
        recent_comments = await db[settings.comments_collection].count_documents({
            "created_at": {"$gte": seven_days_ago}
        })
        
        # Category distribution
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_stats = await db[settings.articles_collection].aggregate(pipeline).to_list(100)
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "admins": admin_users,
                "new_this_month": new_users
            },
            "articles": {
                "total": total_articles,
                "approved": approved_articles,
                "pending": pending_articles,
                "rejected": rejected_articles,
                "featured": featured_articles
            },
            "comments": {
                "total": total_comments
            },
            "recent_activity": {
                "articles_last_7_days": recent_articles,
                "comments_last_7_days": recent_comments
            },
            "category_distribution": [
                {"category": item["_id"], "count": item["count"]} 
                for item in category_stats
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== USER MANAGEMENT ====================
@router.get("/users", response_model=dict)
async def get_all_users(
    current_admin: UserInDB = Depends(get_current_superuser),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    db = Depends(get_db)
):
    """Get all users with pagination and search"""
    try:
        filter_query = {}
        if search:
            filter_query = {
                "$or": [
                    {"email": {"$regex": search, "$options": "i"}},
                    {"full_name": {"$regex": search, "$options": "i"}}
                ]
            }
        
        cursor = db[settings.users_collection].find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
        users = await cursor.to_list(length=limit)
        total = await db[settings.users_collection].count_documents(filter_query)
        
        # Convert _id to id and remove sensitive data
        for user in users:
            user["id"] = str(user.pop("_id"))
            user.pop("hashed_password", None)
        
        return {
            "users": users,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: Optional[dict] = Body(default=None),
    is_active: Optional[bool] = None,
    is_superuser: Optional[bool] = None,
    current_admin: UserInDB = Depends(get_current_superuser),
    db = Depends(get_db)
):
    """Update user status (activate/deactivate, promote/demote admin)"""
    try:
        user = await db[settings.users_collection].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent admin from deactivating themselves
        if user_id == current_admin.id and is_active is False:
            raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
        
        # Support both JSON body updates (preferred) and query-param updates (legacy).
        if payload and is_active is None and "is_active" in payload:
            is_active = payload.get("is_active")
        if payload and is_superuser is None and "is_superuser" in payload:
            is_superuser = payload.get("is_superuser")

        update_data = {}
        if is_active is not None:
            update_data["is_active"] = is_active
        if is_superuser is not None:
            update_data["is_superuser"] = is_superuser
        
        if update_data:
            await db[settings.users_collection].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
        
        updated_user = await db[settings.users_collection].find_one({"_id": ObjectId(user_id)})
        updated_user["id"] = str(updated_user.pop("_id"))
        updated_user.pop("hashed_password", None)
        
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_admin: UserInDB = Depends(get_current_superuser),
    db = Depends(get_db)
):
    """Delete a user (admin only)"""
    try:
        user = await db[settings.users_collection].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent admin from deleting themselves
        if user_id == current_admin.id:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
        # Delete user
        await db[settings.users_collection].delete_one({"_id": ObjectId(user_id)})
        
        # Also delete user's articles and comments
        await db[settings.articles_collection].delete_many({"authorId": user_id})
        await db[settings.comments_collection].delete_many({"author_id": user_id})
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ARTICLE MANAGEMENT ====================
@router.get("/articles")
async def get_all_articles_admin(
    current_admin: UserInDB = Depends(get_current_superuser),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db = Depends(get_db)
):
    """Get all articles for admin (all statuses)"""
    try:
        filter_query = {}
        
        if status_filter:
            filter_query["status"] = status_filter
        
        if category and category != "All":
            filter_query["category"] = category
        
        if search:
            filter_query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"author": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = db[settings.articles_collection].find(filter_query).skip(skip).limit(limit).sort("createdAt", -1)
        articles = await cursor.to_list(length=limit)
        total = await db[settings.articles_collection].count_documents(filter_query)
        
        for article in articles:
            article["id"] = str(article.pop("_id"))
        
        return {
            "articles": articles,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/articles/{slug}/approve")
async def approve_article(
    slug: str,
    current_admin: UserInDB = Depends(get_current_superuser),
    db = Depends(get_db)
):
    """Approve an article"""
    try:
        article = await db[settings.articles_collection].find_one({"slug": slug})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        await db[settings.articles_collection].update_one(
            {"slug": slug},
            {"$set": {"status": "approved", "updatedAt": datetime.utcnow()}}
        )
        
        return {"message": "Article approved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/articles/{slug}/reject")
async def reject_article(
    slug: str,
    reason: Optional[str] = None,
    current_admin: UserInDB = Depends(get_current_superuser),
    db = Depends(get_db)
):
    """Reject an article"""
    try:
        article = await db[settings.articles_collection].find_one({"slug": slug})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        update_data = {"status": "rejected", "updatedAt": datetime.utcnow()}
        if reason:
            update_data["rejection_reason"] = reason
        
        await db[settings.articles_collection].update_one(
            {"slug": slug},
            {"$set": update_data}
        )
        
        return {"message": "Article rejected successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/articles/{slug}/feature")
async def toggle_feature_article(
    slug: str,
    is_featured: bool,
    current_admin: UserInDB = Depends(get_current_superuser),
    db = Depends(get_db)
):
    """Toggle article featured status"""
    try:
        article = await db[settings.articles_collection].find_one({"slug": slug})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        await db[settings.articles_collection].update_one(
            {"slug": slug},
            {"$set": {"isFeatured": is_featured, "updatedAt": datetime.utcnow()}}
        )
        
        return {"message": f"Article {'featured' if is_featured else 'unfeatured'} successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== COMMENT MODERATION ====================
@router.get("/comments")
async def get_all_comments_admin(
    current_admin: UserInDB = Depends(get_current_superuser),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    article_id: Optional[str] = None,
    db = Depends(get_db)
):
    """Get all comments for moderation"""
    try:
        filter_query = {}
        if article_id:
            filter_query["article_id"] = article_id
        
        cursor = db[settings.comments_collection].find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
        comments = await cursor.to_list(length=limit)
        total = await db[settings.comments_collection].count_documents(filter_query)
        
        for comment in comments:
            comment["id"] = str(comment.pop("_id"))
        
        return {
            "comments": comments,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_admin(
    comment_id: str,
    current_admin: UserInDB = Depends(get_current_superuser),
    db = Depends(get_db)
):
    """Delete a comment (admin)"""
    try:
        comment = await db[settings.comments_collection].find_one({"_id": ObjectId(comment_id)})
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        await db[settings.comments_collection].delete_one({"_id": ObjectId(comment_id)})
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DATABASE STATS ====================
@router.get("/database/stats")
async def get_database_stats(
    current_admin: UserInDB = Depends(get_current_superuser),
    db = Depends(get_db)
):
    """Get database statistics"""
    try:
        # Collection counts
        users_count = await db[settings.users_collection].count_documents({})
        articles_count = await db[settings.articles_collection].count_documents({})
        comments_count = await db[settings.comments_collection].count_documents({})
        
        # Get collection sizes (estimated)
        stats = await db.command("dbStats")
        
        # Get recent growth
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        users_growth = await db[settings.users_collection].count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        articles_growth = await db[settings.articles_collection].count_documents({
            "createdAt": {"$gte": thirty_days_ago}
        })
        comments_growth = await db[settings.comments_collection].count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        return {
            "database_name": settings.db_name,
            "collections": {
                "users": {
                    "count": users_count,
                    "growth_30_days": users_growth
                },
                "articles": {
                    "count": articles_count,
                    "growth_30_days": articles_growth
                },
                "comments": {
                    "count": comments_count,
                    "growth_30_days": comments_growth
                }
            },
            "total_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
            "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
            "indexes_size_mb": round(stats.get("indexSize", 0) / (1024 * 1024), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SETTINGS ====================
@router.get("/settings")
async def get_admin_settings(
    current_admin: UserInDB = Depends(get_current_superuser),
    db = Depends(get_db)
):
    """Get admin settings"""
    try:
        # Check if settings collection exists, if not create default
        settings_doc = await db["settings"].find_one({"type": "admin"})
        
        if not settings_doc:
            # Create default settings
            default_settings = {
                "type": "admin",
                "site_name": "IAS UWU Blog",
                "site_description": "IEEE Industry Applications Society - Uva Wellassa University Student Branch Chapter",
                "allow_registration": True,
                "require_email_verification": False,
                "auto_approve_articles": False,
                "featured_articles_limit": 5,
                "articles_per_page": 10,
                "enable_comments": True,
                "updated_at": datetime.utcnow()
            }
            await db["settings"].insert_one(default_settings)
            settings_doc = default_settings
        
        settings_doc["id"] = str(settings_doc.pop("_id", ""))
        return settings_doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_admin_settings(
    settings_update: dict,
    current_admin: UserInDB = Depends(get_current_superuser),
    db = Depends(get_db)
):
    """Update admin settings"""
    try:
        # Remove _id if present
        settings_update.pop("_id", None)
        settings_update.pop("id", None)
        settings_update["updated_at"] = datetime.utcnow()
        
        await db["settings"].update_one(
            {"type": "admin"},
            {"$set": settings_update},
            upsert=True
        )
        
        return {"message": "Settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
