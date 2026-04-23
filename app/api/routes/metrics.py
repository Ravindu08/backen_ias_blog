from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from app.db.mongo import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/metrics")
async def get_public_metrics(db=Depends(get_db)):
    """Public metrics for landing page using only real database data.

    Returns keys that can be computed from current collections:
    - active_contributors: distinct authors with at least one approved article
    - published_articles: total approved articles
    - featured_authors: distinct authors with at least one featured & approved article
    - article_categories: distinct categories among approved articles
    - average_review_time_days: avg days from submission to approval (approved only)
    - published_last_30_days: approved articles created in last 30 days
    """
    try:
        articles = db[settings.articles_collection]

        # Approved articles count
        published_articles = await articles.count_documents({"status": "approved"})

        # Distinct contributors (approved articles authors)
        contributor_emails = await articles.distinct(
            "authorEmail", {"status": "approved", "authorEmail": {"$ne": None}}
        )
        active_contributors = len([e for e in contributor_emails if e])

        # Featured authors (authors with at least one featured approved article)
        featured_author_emails = await articles.distinct(
            "authorEmail",
            {"status": "approved", "isFeatured": True, "authorEmail": {"$ne": None}},
        )
        featured_authors = len([e for e in featured_author_emails if e])

        # Distinct categories among approved articles
        categories = await articles.distinct("category", {"status": "approved", "category": {"$ne": None}})
        article_categories = len([c for c in categories if c])

        # Approved in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        published_last_30_days = await articles.count_documents(
            {"status": "approved", "createdAt": {"$gte": thirty_days_ago}}
        )

        # Average review time (approved only): updatedAt - createdAt
        pipeline = [
            {"$match": {"status": "approved", "createdAt": {"$exists": True}, "updatedAt": {"$exists": True}}},
            {"$project": {"diffMs": {"$subtract": ["$updatedAt", "$createdAt"]}}},
            {"$group": {"_id": None, "avgMs": {"$avg": "$diffMs"}, "count": {"$sum": 1}}},
        ]
        avg_result = await articles.aggregate(pipeline).to_list(length=1)
        average_review_time_days = None
        if avg_result:
            avg_ms = avg_result[0].get("avgMs") or 0
            if avg_ms and avg_ms > 0:
                average_review_time_days = round(float(avg_ms) / (1000 * 60 * 60 * 24), 1)

        return {
            "active_contributors": active_contributors,
            "published_articles": published_articles,
            "featured_authors": featured_authors,
            "article_categories": article_categories,
            "published_last_30_days": published_last_30_days,
            # Only include when computable
            **({"average_review_time_days": average_review_time_days} if average_review_time_days is not None else {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
