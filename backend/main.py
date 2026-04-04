"""
Intelligo ID Certificate System - Main Application Entry Point
============================================================
Modular structure for better code organization and tracking.
"""
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import (
    APP_TITLE,
    APP_DESCRIPTION,
    APP_VERSION,
    CORS_ORIGINS,
    STATIC_DIRECTORY
)
from routes.submit import router as submit_router

# ============================================
# APP INITIALIZATION
# ============================================
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files setup
app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")

# Include routers
app.include_router(submit_router)


# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Intelligo ID Certificate API"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Intelligo ID Certificate System API",
        "version": APP_VERSION,
        "endpoints": {
            "submit": "POST /submit",
            "health": "GET /health"
        }
    }


# ============================================
# RUN SERVER
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
