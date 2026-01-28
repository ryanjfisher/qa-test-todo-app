"""
Article API endpoints.
SCRUM-6: Implement rich text editor for article creation
SCRUM-7: Build article publishing workflow API
SCRUM-8: Create article listing and search functionality
SCRUM-9: Implement scheduled article publishing
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..models.article import ArticleStatus
from ..services.article_service import ArticleService
from ..api.auth import oauth2_scheme
from ..core.security import decode_token

router = APIRouter()


class CreateArticleRequest(BaseModel):
    """SCRUM-6: Rich text editor content"""
    title: str
    content: str  # HTML from rich text editor
    excerpt: Optional[str] = None
    category_id: Optional[int] = None
    featured_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_premium: bool = False


class UpdateArticleRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    category_id: Optional[int] = None
    featured_image_url: Optional[str] = None
    is_premium: Optional[bool] = None


class SchedulePublishRequest(BaseModel):
    """SCRUM-9: Scheduled publishing"""
    publish_at: datetime


class ArticleResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    status: str
    author_id: int
    category_id: Optional[int]
    featured_image_url: Optional[str]
    is_premium: bool
    view_count: int
    created_at: datetime
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    page: int
    per_page: int


@router.get("/", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    article_service: ArticleService = Depends()
):
    """
    List published articles with pagination.
    SCRUM-8: Create article listing and search functionality
    """
    articles, total = await article_service.list_published(
        page=page,
        per_page=per_page,
        category=category,
        search_query=search
    )
    
    return ArticleListResponse(
        articles=articles,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/search")
async def search_articles(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    article_service: ArticleService = Depends()
):
    """
    Full-text search for articles.
    SCRUM-8: Uses Elasticsearch for search
    SCRUM-21: Set up Elasticsearch for article search
    """
    results = await article_service.search(
        query=q,
        page=page,
        per_page=per_page
    )
    return results


@router.get("/{slug}", response_model=ArticleResponse)
async def get_article(
    slug: str,
    token: Optional[str] = Depends(oauth2_scheme),
    article_service: ArticleService = Depends()
):
    """Get a single article by slug."""
    article = await article_service.get_by_slug(slug)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    # Check premium access - SCRUM-13, SCRUM-29
    if article.is_premium:
        if not token:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Premium content requires subscription")
        
        user_id = decode_token(token).get("sub")
        can_access = await article_service.check_premium_access(user_id)
        if not can_access:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Upgrade to access premium content")
    
    # Increment view count
    await article_service.increment_views(article.id)
    
    return article


@router.post("/", response_model=ArticleResponse)
async def create_article(
    request: CreateArticleRequest,
    token: str = Depends(oauth2_scheme),
    article_service: ArticleService = Depends()
):
    """
    Create a new article draft.
    SCRUM-6: Implement rich text editor for article creation
    """
    payload = decode_token(token)
    author_id = payload.get("sub")
    
    article = await article_service.create(
        author_id=author_id,
        title=request.title,
        content=request.content,
        excerpt=request.excerpt,
        category_id=request.category_id,
        featured_image_url=request.featured_image_url,
        meta_title=request.meta_title,
        meta_description=request.meta_description,
        is_premium=request.is_premium
    )
    
    return article


@router.post("/{article_id}/submit")
async def submit_for_review(
    article_id: int,
    token: str = Depends(oauth2_scheme),
    article_service: ArticleService = Depends()
):
    """
    Submit article for editorial review.
    SCRUM-7: Build article publishing workflow API
    """
    payload = decode_token(token)
    author_id = payload.get("sub")
    
    article = await article_service.submit_for_review(article_id, author_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    return {"message": "Article submitted for review", "status": article.status.value}


@router.post("/{article_id}/publish")
async def publish_article(
    article_id: int,
    token: str = Depends(oauth2_scheme),
    article_service: ArticleService = Depends()
):
    """
    Publish an article (editor only).
    SCRUM-7: Build article publishing workflow API
    """
    payload = decode_token(token)
    editor_id = payload.get("sub")
    
    # Verify editor role
    if not await article_service.is_editor(editor_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only editors can publish")
    
    article = await article_service.publish(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return {"message": "Article published", "published_at": article.published_at}


@router.post("/{article_id}/schedule")
async def schedule_publish(
    article_id: int,
    request: SchedulePublishRequest,
    token: str = Depends(oauth2_scheme),
    article_service: ArticleService = Depends()
):
    """
    Schedule article for future publishing.
    SCRUM-9: Implement scheduled article publishing
    """
    if request.publish_at <= datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scheduled time must be in the future")
    
    article = await article_service.schedule_publish(article_id, request.publish_at)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return {"message": "Article scheduled", "scheduled_for": article.scheduled_for}


@router.delete("/{article_id}/schedule")
async def cancel_scheduled_publish(
    article_id: int,
    token: str = Depends(oauth2_scheme),
    article_service: ArticleService = Depends()
):
    """
    Cancel scheduled publishing.
    SCRUM-9: Return article to draft status
    """
    article = await article_service.cancel_schedule(article_id)
    return {"message": "Schedule cancelled", "status": article.status.value}
