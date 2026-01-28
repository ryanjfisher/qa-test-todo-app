"""
Article Service
SCRUM-7: Build article publishing workflow API
SCRUM-8: Create article listing and search functionality
SCRUM-9: Implement scheduled article publishing
"""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from ..models.article import Article, ArticleStatus
from ..core.config import settings


class ArticleService:
    """Service for article operations."""
    
    def __init__(self, db: Session, cache=None, search_client=None):
        self.db = db
        self.cache = cache  # Redis - SCRUM-20
        self.search = search_client  # Elasticsearch - SCRUM-21
    
    async def create(
        self,
        author_id: int,
        title: str,
        content: str,
        **kwargs
    ) -> Article:
        """
        Create a new article draft.
        SCRUM-6: Implement rich text editor for article creation
        """
        slug = self._generate_slug(title)
        
        article = Article(
            title=title,
            slug=slug,
            content=content,
            author_id=author_id,
            status=ArticleStatus.DRAFT,
            **kwargs
        )
        
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        
        return article
    
    async def submit_for_review(self, article_id: int, author_id: int) -> Optional[Article]:
        """
        Submit article for editorial review.
        SCRUM-7: Build article publishing workflow API
        State: draft -> pending_review
        """
        article = self.db.query(Article).filter(
            Article.id == article_id,
            Article.author_id == author_id,
            Article.status == ArticleStatus.DRAFT
        ).first()
        
        if not article:
            return None
        
        article.submit_for_review()
        self.db.commit()
        
        # TODO: Notify editors - SCRUM-7
        
        return article
    
    async def publish(self, article_id: int) -> Optional[Article]:
        """
        Publish an article immediately.
        SCRUM-7: Build article publishing workflow API
        State: pending_review -> published
        """
        article = self.db.query(Article).filter(
            Article.id == article_id,
            Article.status == ArticleStatus.PENDING_REVIEW
        ).first()
        
        if not article:
            return None
        
        article.publish()
        self.db.commit()
        
        # Invalidate cache - SCRUM-20
        if self.cache:
            await self.cache.delete(f"article:{article.slug}")
        
        # Index in Elasticsearch - SCRUM-21
        if self.search:
            await self._index_article(article)
        
        return article
    
    async def schedule_publish(self, article_id: int, publish_at: datetime) -> Optional[Article]:
        """
        Schedule article for future publishing.
        SCRUM-9: Implement scheduled article publishing
        """
        article = self.db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return None
        
        article.scheduled_for = publish_at
        self.db.commit()
        
        # Schedule background job - SCRUM-9
        # celery_app.send_task('publish_article', args=[article_id], eta=publish_at)
        
        return article
    
    async def cancel_schedule(self, article_id: int) -> Optional[Article]:
        """
        Cancel scheduled publishing.
        SCRUM-9: Return article to draft status
        """
        article = self.db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return None
        
        article.scheduled_for = None
        article.status = ArticleStatus.DRAFT
        self.db.commit()
        
        return article
    
    async def list_published(
        self,
        page: int = 1,
        per_page: int = 20,
        category: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> Tuple[List[Article], int]:
        """
        List published articles with pagination.
        SCRUM-8: Create article listing and search functionality
        """
        query = self.db.query(Article).filter(Article.status == ArticleStatus.PUBLISHED)
        
        if category:
            query = query.join(Article.category).filter(Category.slug == category)
        
        if search_query:
            # Basic search - for full-text, use Elasticsearch
            query = query.filter(Article.title.ilike(f"%{search_query}%"))
        
        total = query.count()
        articles = query.order_by(Article.published_at.desc()) \
            .offset((page - 1) * per_page) \
            .limit(per_page) \
            .all()
        
        return articles, total
    
    async def search(self, query: str, page: int = 1, per_page: int = 20):
        """
        Full-text search using Elasticsearch.
        SCRUM-8: Create article listing and search functionality
        SCRUM-21: Set up Elasticsearch for article search
        """
        if not self.search:
            # Fallback to DB search
            return await self.list_published(page=page, per_page=per_page, search_query=query)
        
        # Elasticsearch query
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content", "excerpt^2"],
                    "fuzziness": "AUTO"
                }
            },
            "from": (page - 1) * per_page,
            "size": per_page
        }
        
        results = await self.search.search(index="articles", body=body)
        return results
    
    async def get_by_slug(self, slug: str) -> Optional[Article]:
        """Get article by slug with caching."""
        # Try cache first - SCRUM-20
        if self.cache:
            cached = await self.cache.get(f"article:{slug}")
            if cached:
                return cached
        
        article = self.db.query(Article).filter(
            Article.slug == slug,
            Article.status == ArticleStatus.PUBLISHED
        ).first()
        
        # Cache for 5 minutes - SCRUM-20
        if article and self.cache:
            await self.cache.set(f"article:{slug}", article, ex=settings.CACHE_TTL)
        
        return article
    
    async def increment_views(self, article_id: int):
        """Increment article view count."""
        self.db.query(Article).filter(Article.id == article_id).update(
            {"view_count": Article.view_count + 1}
        )
        self.db.commit()
    
    async def check_premium_access(self, user_id: int) -> bool:
        """
        Check if user can access premium content.
        SCRUM-13, SCRUM-29: Premium content accessible without subscription (BUG)
        """
        # This needs to be checked BEFORE serving content to fix SCRUM-29
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        return user.can_access_premium()
    
    async def is_editor(self, user_id: int) -> bool:
        """Check if user is an editor."""
        user = self.db.query(User).filter(User.id == user_id).first()
        return user and user.role in [UserRole.EDITOR, UserRole.ADMIN]
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL-safe slug from title."""
        import re
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return f"{slug}-{datetime.now().strftime('%Y%m%d')}"
    
    async def _index_article(self, article: Article):
        """Index article in Elasticsearch - SCRUM-21"""
        doc = {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "excerpt": article.excerpt,
            "author_id": article.author_id,
            "category": article.category.name if article.category else None,
            "published_at": article.published_at.isoformat()
        }
        await self.search.index(index="articles", id=article.id, document=doc)
