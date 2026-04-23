from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    # Database
    mongo_uri: str = os.getenv("MONGODB_URI", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db_name: str = os.getenv("DB_NAME", "ias_blog")
    articles_collection: str = "articles"
    users_collection: str = "users"
    comments_collection: str = "comments"

    # Security (JWT)
    secret_key: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    jwt_refresh_secret: str | None = os.getenv("JWT_REFRESH_SECRET")

    # Frontend / CORS
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Third-party services
    google_client_id: str | None = os.getenv("GOOGLE_CLIENT_ID")
    stripe_secret_key: str | None = os.getenv("STRIPE_SECRET_KEY")
    laozhang_api_key: str | None = os.getenv("LAOZHANG_API_KEY")
    laozhang_api_url: str | None = os.getenv("LAOZHANG_API_URL")

    # Email
    email_host: str | None = os.getenv("EMAIL_HOST")
    email_port: int | None = int(os.getenv("EMAIL_PORT", "0")) if os.getenv("EMAIL_PORT") else None
    email_user: str | None = os.getenv("EMAIL_USER")
    email_pass: str | None = os.getenv("EMAIL_PASS")
    email_from: str | None = os.getenv("EMAIL_FROM")

    # Payment (PayHere)
    payhere_merchant_id: str | None = os.getenv("PAYHERE_MERCHANT_ID")
    payhere_merchant_secret: str | None = os.getenv("PAYHERE_MERCHANT_SECRET")

    # Cloudinary
    cloudinary_cloud_name: str | None = os.getenv("CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str | None = os.getenv("CLOUDINARY_API_KEY")
    cloudinary_api_secret: str | None = os.getenv("CLOUDINARY_API_SECRET")


settings = Settings()
