"""
Article models.
SCRUM-19: Set up PostgreSQL database schema for articles
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from ..core.database import Base


class ArticleStatus(str, Enum):
    """Article publishing status - SCRUM-7"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Category(Base):
    """News category (Politics, Sports, etc.)"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    slug = Column(String(100), unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    articles = relationship("Article", back_populates="category")


class Article(Base):
    """
    News article model.
    SCRUM-19: Database schema for articles
    SCRUM-7: Publishing workflow support
    """
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    slug = Column(String(500), unique=True, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    
    # Author and category
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Publishing status - SCRUM-7
    status = Column(SQLEnum(ArticleStatus), default=ArticleStatus.DRAFT, index=True)
    
    # Media
    featured_image_url = Column(String(500), nullable=True)
    
    # SEO
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    scheduled_for = Column(DateTime, nullable=True)  # SCRUM-9: Scheduled publishing
    
    # Metrics
    view_count = Column(Integer, default=0)
    
    # Premium content - SCRUM-13
    is_premium = Column(Integer, default=False)
    
    # Relationships
    author = relationship("User", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    comments = relationship("Comment", back_populates="article", cascade="all, delete-orphan")

    def publish(self):
        """Publish the article - SCRUM-7"""
        self.status = ArticleStatus.PUBLISHED
        self.published_at = datetime.utcnow()

    def submit_for_review(self):
        """Submit article for editorial review - SCRUM-7"""
        if self.status == ArticleStatus.DRAFT:
            self.status = ArticleStatus.PENDING_REVIEW
