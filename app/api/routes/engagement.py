from fastapi import APIRouter, HTTPException, Depends, Request
from app.db.mongo import get_db
from app.core.config import settings
from datetime import datetime
from pymongo import ReturnDocument

router = APIRouter()

ARTICLES = lambda db: db[settings.articles_collection]


def get_client_identifier(request: Request) -> str:
    """Get client IP for tracking likes/views without auth"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host or "unknown"


@router.post("/{slug}/like")
async def toggle_like(slug: str, request: Request, db=Depends(get_db)):
    """Toggle like on an article (guest-friendly, tracked by IP)"""
    try:
        client_id = get_client_identifier(request)
        articles = ARTICLES(db)
        
        article = await articles.find_one({"slug": slug})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        likes = article.get("likes", []) or []
        
        # Toggle like
        if client_id in likes:
            likes.remove(client_id)
            liked = False
        else:
            likes.append(client_id)
            liked = True
        
        # Update article
        result = await articles.find_one_and_update(
            {"slug": slug},
            {
                "$set": {
                    "likes": likes,
                    "likesCount": len(likes),
                    "updatedAt": datetime.utcnow(),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        
        return {
            "liked": liked,
            "likesCount": result.get("likesCount", 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{slug}/view")
async def record_view(slug: str, request: Request, db=Depends(get_db)):
    """Record a view on an article (guest-friendly). Increments on each hit for simplicity."""
    try:
        articles = ARTICLES(db)
        
        article = await articles.find_one({"slug": slug})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        view_count = article.get("viewCount", 0) + 1
        result = await articles.find_one_and_update(
            {"slug": slug},
            {
                "$set": {
                    "viewCount": view_count,
                    "updatedAt": datetime.utcnow(),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        
        return {
            "viewCount": result.get("viewCount", view_count),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{slug}/stats")
async def get_article_stats(slug: str, db=Depends(get_db)):
    """Get engagement stats for an article (likes, views)"""
    try:
        articles = ARTICLES(db)
        article = await articles.find_one({"slug": slug})
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return {
            "slug": slug,
            "likesCount": article.get("likesCount", 0),
            "viewCount": article.get("viewCount", 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
