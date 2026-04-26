from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, Request, Body
from fastapi.responses import HTMLResponse
from app.db.mongo import get_db
from app.core.config import settings
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleOut
from app.api.dependencies import get_current_active_user, get_current_superuser, get_current_user_optional
from app.schemas.user import UserInDB
from bson import ObjectId
from datetime import datetime
import re
import logging
import html
from urllib.parse import urlparse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

COLLECTION = lambda: get_db()[settings.articles_collection]


def clean_author_name(name: str) -> str:
    """Normalize author display names (remove possessive suffixes and duplicate tokens)."""
    if not name:
        return "Anonymous"
    normalized = re.sub(r"\b([A-Za-z]+)'s\b", r"\1", name).strip()
    tokens = [t for t in normalized.split() if t]
    deduped = []
    for token in tokens:
        if not deduped or deduped[-1].lower() != token.lower():
            deduped.append(token)
    return " ".join(deduped) if deduped else "Anonymous"


async def enrich_articles_with_author_profile(items: list, db) -> list:
    """Attach clean author name and profile image to article docs."""
    author_ids = [doc.get("authorId") for doc in items if doc.get("authorId")]
    author_profiles = {}

    if author_ids:
        try:
            oids = []
            for aid in author_ids:
                try:
                    oids.append(ObjectId(aid))
                except Exception:
                    continue
            if oids:
                users = await db[settings.users_collection].find(
                    {"_id": {"$in": oids}},
                    {"full_name": 1, "profile_image": 1, "email": 1}
                ).to_list(length=len(oids))
                author_profiles = {str(u["_id"]): u for u in users}
        except Exception:
            author_profiles = {}

    for doc in items:
        author_id = doc.get("authorId")
        profile = author_profiles.get(author_id)
        if profile:
            display_name = profile.get("full_name") or doc.get("author") or profile.get("email", "")
            doc["author"] = clean_author_name(display_name)
            if profile.get("profile_image"):
                doc["authorImage"] = profile.get("profile_image")
        else:
            doc["author"] = clean_author_name(doc.get("author", ""))
    return items


def serialize(doc: dict) -> dict:
    if not doc:
        return doc
    doc["_id"] = str(doc.get("_id"))
    return doc

def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug

def calculate_reading_time(content: str) -> str:
    """Calculate estimated reading time (200 words per minute)"""
    word_count = len(content.split())
    minutes = max(1, round(word_count / 200))
    return f"{minutes} min read"


def normalize_featured_image_url(image_url: str | None, request: Request) -> str | None:
    """Rewrite localhost upload URLs to the current backend host for deployed clients."""
    if not image_url:
        return image_url

    value = str(image_url).strip()
    if not value:
        return value

    local_prefixes = (
        "http://127.0.0.1:8000/uploads/",
        "http://localhost:8000/uploads/",
        "https://127.0.0.1:8000/uploads/",
        "https://localhost:8000/uploads/",
    )

    if value.startswith("/uploads/"):
        return f"{str(request.base_url).rstrip('/')}{value}"

    for prefix in local_prefixes:
        if value.startswith(prefix):
            filename = value.split("/uploads/", 1)[1]
            return f"{str(request.base_url).rstrip('/')}/uploads/{filename}"

    return value


def _ensure_absolute_url(value: str, default_scheme: str = "https") -> str:
    """Ensure configured URL strings are absolute and normalized."""
    raw = (value or "").strip().rstrip("/")
    if not raw:
        return ""
    if not re.match(r"^https?://", raw, flags=re.IGNORECASE):
        raw = f"{default_scheme}://{raw}"
    return raw


def _is_local_or_private_host(hostname: str) -> bool:
    """Detect non-public hosts that should not be used for social share redirects."""
    host = (hostname or "").lower()
    return (
        host in {"localhost", "127.0.0.1", "0.0.0.0"}
        or host.startswith("10.")
        or host.startswith("192.168.")
        or bool(re.match(r"^172\.(1[6-9]|2\d|3[0-1])\.", host))
    )


def get_public_frontend_base(request: Request) -> str:
    """Pick a public frontend base URL and avoid localhost/private values in production shares."""
    frontend = settings.frontend_url or "http://localhost:5173"
    first = frontend.split(",")[0].strip() if frontend else "http://localhost:5173"
    normalized = _ensure_absolute_url(first)

    parsed = urlparse(normalized)
    if parsed.hostname and not _is_local_or_private_host(parsed.hostname):
        return normalized

    request_base = str(request.base_url).rstrip("/")
    parsed_request = urlparse(request_base)
    if parsed_request.hostname and _is_local_or_private_host(parsed_request.hostname):
        return ""
    return request_base


def get_public_request_url(request: Request) -> str:
    """Build a public-facing absolute URL from proxy-aware headers when available."""
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}{request.url.path}"
    return str(request.url)


@router.get("/share/{slug}", response_class=HTMLResponse)
async def article_share_preview(slug: str, request: Request):
    """Return Open Graph metadata so Facebook can render rich share cards."""
    db = get_db()
    doc = await COLLECTION().find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")

    title = html.escape(doc.get("title") or "IAS Blog Article")
    short_description = (
        doc.get("shortDescription")
        or doc.get("short_description")
        or doc.get("description")
        or ""
    )
    fallback_content = (doc.get("content") or "").strip().replace("\n", " ")
    description_text = (short_description or fallback_content[:220] or "Read this article on IAS Blog").strip()
    description = html.escape(description_text)

    raw_image_url = (
        doc.get("featuredImage")
        or doc.get("featured_image")
        or doc.get("image")
        or ""
    ).strip()
    if raw_image_url.startswith("http://") or raw_image_url.startswith("https://"):
        image_url_raw = raw_image_url
    elif raw_image_url.startswith("/"):
        image_url_raw = f"{str(request.base_url).rstrip('/')}{raw_image_url}"
    else:
        image_url_raw = raw_image_url
    image_url = html.escape(image_url_raw)

    frontend_base = get_public_frontend_base(request)
    canonical_article_url = f"{frontend_base}/article/{slug}" if frontend_base else ""

    # Prefer the canonical article URL so scrapers do not lock onto localhost URLs.
    share_url = html.escape(canonical_article_url or _ensure_absolute_url(get_public_request_url(request)))
    redirect_meta = f'<meta http-equiv="refresh" content="0;url={canonical_article_url}" />' if canonical_article_url else ""
    redirect_script = f"<script>window.location.replace({canonical_article_url!r});</script>" if canonical_article_url else ""
    read_link = f'<p><a href="{canonical_article_url}">Continue to article</a></p>' if canonical_article_url else ""
    html_page = f"""
<!doctype html>
<html lang=\"en\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>{title}</title>
        <meta property=\"og:type\" content=\"article\" />
        <meta property=\"og:site_name\" content=\"IAS Blog\" />
        <meta property=\"og:title\" content=\"{title}\" />
        <meta property=\"og:description\" content=\"{description}\" />
        <meta property=\"og:url\" content=\"{share_url}\" />
        <meta property=\"og:image\" content=\"{image_url}\" />
        <meta property=\"og:image:secure_url\" content=\"{image_url}\" />
        <meta name=\"description\" content=\"{description}\" />
        <meta name=\"twitter:card\" content=\"summary_large_image\" />
        <meta name=\"twitter:title\" content=\"{title}\" />
        <meta name=\"twitter:description\" content=\"{description}\" />
        <meta name=\"twitter:image\" content=\"{image_url}\" />
        {redirect_meta}
    </head>
    <body>
        <h1>{title}</h1>
        <p>{description}</p>
        {read_link}
        <p>Redirecting to article...</p>
        {redirect_script}
    </body>
</html>
"""
    return HTMLResponse(content=html_page)

@router.get("/", response_model=dict)
async def list_articles(
    request: Request,
    category: Optional[str] = Query(default=None),
    featured: Optional[bool] = Query(default=None),
    status: Optional[str] = Query(default="approved"),  # Default show only approved
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List articles (public sees approved only, admins can see all)"""
    filt = {}
    if category and category != "All":
        filt["category"] = category
    if featured is not None:
        filt["isFeatured"] = featured
    if status:
        filt["status"] = status

    db = get_db()
    cursor = COLLECTION().find(filt).skip(skip).limit(limit).sort("created_at", -1)
    items = [serialize(doc) async for doc in cursor]
    items = await enrich_articles_with_author_profile(items, db)
    for item in items:
        item["featuredImage"] = normalize_featured_image_url(item.get("featuredImage"), request)
    return {"items": items, "count": len(items)}


@router.get("/{slug}")
async def get_article(slug: str, request: Request):
    db = get_db()
    doc = await COLLECTION().find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    serialized = serialize(doc)
    enriched = await enrich_articles_with_author_profile([serialized], db)
    item = enriched[0] if enriched else serialized
    item["featuredImage"] = normalize_featured_image_url(item.get("featuredImage"), request)
    return item


@router.post("/", response_model=ArticleOut, status_code=201)
async def create_article(
    payload: ArticleCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new article (requires authentication)"""
    # Generate slug from title
    base_slug = generate_slug(payload.title)
    slug = base_slug
    
    # Ensure unique slug
    counter = 1
    while await COLLECTION().find_one({"slug": slug}):
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Calculate reading time
    reading_time = calculate_reading_time(payload.content)
    
    # Create article document
    now = datetime.utcnow()
    article_dict = {
        "slug": slug,
        "title": payload.title,
        "author": clean_author_name(current_user.full_name or current_user.email.split('@')[0]),
        "authorImage": getattr(current_user, 'profile_image', None),
        "authorEmail": current_user.email,
        "authorId": current_user.id,
        "category": payload.category,
        "tags": payload.tags,
        "readingTime": reading_time,
        "featuredImage": str(payload.featuredImage) if payload.featuredImage else None,
        "shortDescription": payload.shortDescription,
        "content": payload.content,
        "status": "pending",  # All articles start as pending
        "isFeatured": False,
        "viewCount": 0,
        "likesCount": 0,
        "likes": [],  # Track likers by IP/session
        "created_at": now,
        "updated_at": now
    }
    
    res = await COLLECTION().insert_one(article_dict)
    created = await COLLECTION().find_one({"_id": res.inserted_id})
    created["id"] = str(created.pop("_id"))
    
    return ArticleOut(**created)


@router.get("/my/articles", response_model=dict)
async def get_my_articles(
    current_user: UserInDB = Depends(get_current_active_user),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get current user's submitted articles"""
    logger.info(f"Fetching articles for user: {current_user.email} (ID: {current_user.id})")
    
    # Try to find articles by authorId OR authorEmail as fallback
    filt = {
        "$or": [
            {"authorId": current_user.id},
            {"authorEmail": current_user.email}
        ]
    }
    cursor = COLLECTION().find(filt).skip(skip).limit(limit).sort("createdAt", -1)
    items = [serialize(doc) async for doc in cursor]
    
    logger.info(f"Found {len(items)} articles for user {current_user.email}")
    
    return {"items": items, "count": len(items)}

@router.put("/{slug}")
async def update_article(
    slug: str,
    payload: ArticleUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update an article (author can edit own articles, admin can edit any)"""
    article = await COLLECTION().find_one({"slug": slug})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check permissions
    if not current_user.is_superuser and article.get("authorId") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this article")
    
    update = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}

    # Convert Pydantic URL types to plain strings for Mongo compatibility
    if "featuredImage" in update and update["featuredImage"] is not None:
        update["featuredImage"] = str(update["featuredImage"])
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update["updatedAt"] = datetime.utcnow()
    
    res = await COLLECTION().find_one_and_update(
        {"slug": slug},
        {"$set": update},
        return_document=True,
    )
    return serialize(res)

@router.delete("/{slug}")
async def delete_article(
    slug: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete an article (author can delete own articles, admin can delete any)"""
    article = await COLLECTION().find_one({"slug": slug})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check permissions
    if not current_user.is_superuser and article.get("authorId") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this article")
    
    res = await COLLECTION().delete_one({"slug": slug})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"deleted": True}

@router.patch("/{slug}/approve")
async def approve_article(
    slug: str,
    current_user: UserInDB = Depends(get_current_superuser)
):
    """Approve an article (admin only)"""
    res = await COLLECTION().find_one_and_update(
        {"slug": slug},
        {"$set": {"status": "approved", "updatedAt": datetime.utcnow()}},
        return_document=True,
    )
    if not res:
        raise HTTPException(status_code=404, detail="Article not found")
    return serialize(res)

@router.patch("/{slug}/reject")
async def reject_article(
    slug: str,
    current_user: UserInDB = Depends(get_current_superuser)
):
    """Reject an article (admin only)"""
    res = await COLLECTION().find_one_and_update(
        {"slug": slug},
        {"$set": {"status": "rejected", "updatedAt": datetime.utcnow()}},
        return_document=True,
    )
    if not res:
        raise HTTPException(status_code=404, detail="Article not found")
    return serialize(res)


@router.post("/{slug}/view")
async def track_view(slug: str):
    """Track article view (increment view count)"""
    article = await COLLECTION().find_one({"slug": slug})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    res = await COLLECTION().find_one_and_update(
        {"slug": slug},
        {"$inc": {"viewCount": 1}},
        return_document=True,
    )
    if not res:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"viewCount": res.get("viewCount", 0)}


@router.post("/{slug}/like")
async def toggle_like(
    slug: str,
    request: Request,
    payload: Optional[dict] = Body(default=None),
    request_ip: str = None,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """Toggle like on article (guest-friendly, tracked by IP/session)"""
    article = await COLLECTION().find_one({"slug": slug})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Prefer authenticated user identity; fallback to IP for guests.
    if current_user:
        liker_id = f"user:{current_user.id}"
    else:
        if payload and not request_ip:
            request_ip = payload.get("request_ip")
        client_ip = request_ip or (request.client.host if request.client else None)
        liker_id = f"ip:{client_ip}" if client_ip else "anonymous"

    likes = article.get("likes", [])
    
    if liker_id in likes:
        # Unlike
        await COLLECTION().find_one_and_update(
            {"slug": slug},
            {"$pull": {"likes": liker_id}, "$inc": {"likesCount": -1}},
            return_document=True,
        )
        return {"liked": False, "likesCount": max(0, article.get("likesCount", 1) - 1)}
    else:
        # Like
        await COLLECTION().find_one_and_update(
            {"slug": slug},
            {"$push": {"likes": liker_id}, "$inc": {"likesCount": 1}},
            return_document=True,
        )
        return {"liked": True, "likesCount": article.get("likesCount", 0) + 1}


@router.get("/{slug}/stats")
async def get_article_stats(slug: str):
    """Get article stats (views, likes)"""
    article = await COLLECTION().find_one({"slug": slug})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return {
        "viewCount": article.get("viewCount", 0),
        "likesCount": article.get("likesCount", 0),
    }
