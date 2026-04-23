from fastapi import APIRouter, UploadFile, File, HTTPException, status, Request
from fastapi.responses import JSONResponse
from app.core.config import settings
import cloudinary
import cloudinary.uploader
import os
from pathlib import Path
from uuid import uuid4

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
    "image/heic",
    "image/heif",
}

EXTENSION_MAP = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/heic": ".heic",
    "image/heif": ".heif",
}

@router.post("/image")
async def upload_image(request: Request, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    contents = await file.read()

    # Use Cloudinary when configured.
    cloudinary_ready = (
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    )

    if cloudinary_ready:
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )

    # Upload to Cloudinary, fallback to local uploads on failure/unavailable config
    try:
        if cloudinary_ready:
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="ias-uploads",
                resource_type="image",
                overwrite=False,
            )
            url = upload_result.get("secure_url") or upload_result.get("url")
            if url:
                return JSONResponse({"url": url})

        uploads_dir = Path(os.getcwd()) / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        extension = EXTENSION_MAP.get(file.content_type, ".jpg")
        filename = f"{uuid4().hex}{extension}"
        target_path = uploads_dir / filename

        with open(target_path, "wb") as out_file:
            out_file.write(contents)

        base_url = str(request.base_url).rstrip("/")
        return JSONResponse({"url": f"{base_url}/uploads/{filename}"})
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Image upload failed: {exc}")
