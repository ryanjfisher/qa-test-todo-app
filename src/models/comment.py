"""
Comment models.
SCRUM-15: Comments & Community
SCRUM-16: Build threaded comment system
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..core.database import Base


class Comment(Base):
    """
    Threaded comment model.
    SCRUM-16: Build threaded comment system
    """
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    
    # Relationships
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # Threading
    
    # Moderation - SCRUM-17
    is_approved = Column(Boolean, default=True)  # Auto-approved unless flagged
    is_deleted = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    flagged_reason = Column(String(200), nullable=True)
    moderated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderated_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    article = relationship("Article", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id], back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])
    reactions = relationship("Reaction", back_populates="comment", cascade="all, delete-orphan")


class Reaction(Base):
    """
    Reactions on articles and comments.
    SCRUM-18: Add reaction system for articles and comments
    """
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, index=True)
    reaction_type = Column(String(20), nullable=False)  # like, love, angry, sad, wow
    
    # Can be on article OR comment (one must be null)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    comment = relationship("Comment", back_populates="reactions")


class Bookmark(Base):
    """
    User bookmarks for reading later.
    SCRUM-32: Add article bookmarking feature
    """
    __tablename__ = "bookmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="bookmarks")
