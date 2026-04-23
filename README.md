# IAS UWU Blog Backend (FastAPI + MongoDB)

A minimal, production-friendly backend for the React frontend, built with FastAPI and MongoDB (Motor).

## Features
- FastAPI app with CORS for Vite dev (`localhost:5173`)
- Articles CRUD (list, read by slug, create, update, delete)
- MongoDB indexes (unique `slug`)
- Environment-based config

## Getting Started

### 1) Create and activate a virtual environment
```powershell
cd "G:\GitHub\New folder (2)\IEEE-IAS-Chapter\IAS\my-project-backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies
```powershell
pip install -r requirements.txt
```

### 3) Configure environment
Copy `.env.example` to `.env` and adjust as needed. Key variables:

- Database: `MONGODB_URI`, `DB_NAME`
- CORS: `FRONTEND_URL` (single or comma-separated origins)
- Security: `JWT_SECRET`, `JWT_REFRESH_SECRET`
- Services: `GOOGLE_CLIENT_ID`, `STRIPE_SECRET_KEY`, `LAOZHANG_API_KEY`, `LAOZHANG_API_URL`
- Email: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_FROM`
- PayHere: `PAYHERE_MERCHANT_ID`, `PAYHERE_MERCHANT_SECRET`
- Cloudinary: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

Minimal local example:
```
MONGODB_URI=mongodb://localhost:27017
DB_NAME=ias_blog
FRONTEND_URL=http://localhost:5173
```

### 4) Run the server (dev)
```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Server runs at: http://localhost:8000

Health check: http://localhost:8000/health

### Notes
- For cloud deployment, use MongoDB Atlas and set `MONGO_URI` accordingly.
- Keep images out of the database; store links only (e.g., Cloudinary/S3) and use CDN.
- Plan indexes early for query patterns (`slug`, `category`, `isFeatured`).
