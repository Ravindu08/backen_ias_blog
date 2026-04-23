from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routes.articles import router as articles_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.comments import router as comments_router
from app.api.routes.profile import router as profile_router
from app.api.routes.admin import router as admin_router
from app.api.routes.uploads import router as uploads_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.google_auth import router as google_auth_router
from app.api.routes.engagement import router as engagement_router
from app.db.mongo import connect_to_mongo, close_mongo_connection, get_db
import os
import cloudinary
import logging

# Set up logging
logger = logging.getLogger(__name__)

app = FastAPI(title="IAS UWU Blog API", version="0.1.0")

# Always allow localhost for development
all_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add environment-based origins if set
origins_env = settings.frontend_url or ""
if origins_env:
    # Handle both single URL and comma-separated list
    env_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    all_origins.extend(env_origins)

all_origins = list(set(all_origins))  # Remove duplicates

logger.info(f"CORS allowed origins: {all_origins}")

# Add CORS middleware FIRST (before other middleware/routes)
# Using allow_origin_regex for more flexible matching
app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.on_event("startup")
async def on_startup():
    try:
        await connect_to_mongo()
        logger.info("Connected to MongoDB")
        
        # Configure Cloudinary if credentials are available
        if settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret:
            cloudinary.config(
                cloud_name=settings.cloudinary_cloud_name,
                api_key=settings.cloudinary_api_key,
                api_secret=settings.cloudinary_api_secret,
                secure=True,
            )
            logger.info("Cloudinary configured successfully")
        else:
            logger.warning("Cloudinary credentials not fully configured")
        
        # Indexes for articles
        await get_db()[settings.articles_collection].create_index("slug", unique=True)
        await get_db()[settings.articles_collection].create_index("category")
        await get_db()[settings.articles_collection].create_index("isFeatured")
        logger.info("Article indexes created")
        
        # Indexes for users
        await get_db()[settings.users_collection].create_index("email", unique=True)
        logger.info("User indexes created")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def on_shutdown():
    await close_mongo_connection()

app.include_router(health_router, prefix="/health")
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(google_auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(articles_router, prefix="/articles", tags=["articles"])
app.include_router(comments_router, prefix="/comments", tags=["comments"])
app.include_router(profile_router, prefix="/profile", tags=["profile"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(uploads_router, prefix="/upload", tags=["upload"])
app.include_router(metrics_router, prefix="", tags=["metrics"])  # public metrics at /metrics
app.include_router(engagement_router, prefix="/articles", tags=["engagement"])  # likes/views at /articles/{slug}/like

# Serve uploaded files
UPLOADS_PATH = os.path.join(os.getcwd(), "uploads")
if not os.path.exists(UPLOADS_PATH):
    os.makedirs(UPLOADS_PATH, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_PATH), name="uploads")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
