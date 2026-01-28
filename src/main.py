"""
Daily Tribune News API
Main FastAPI application entry point.
SCRUM-7: Build article publishing workflow API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import articles, auth, users, comments
from .core.config import settings

app = FastAPI(
    title="Daily Tribune API",
    description="Backend API for Daily Tribune news platform",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])
app.include_router(comments.router, prefix="/api/comments", tags=["Comments"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "daily-tribune-api"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Daily Tribune API",
        "version": "1.0.0",
        "docs": "/docs"
    }
