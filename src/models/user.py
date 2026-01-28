"""
User models.
SCRUM-10: User Authentication & Profiles
SCRUM-13: Build subscription tier management
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship

from ..core.database import Base


class UserRole(str, Enum):
    """User roles in the system."""
    READER = "reader"
    JOURNALIST = "journalist"
    EDITOR = "editor"
    ADMIN = "admin"


class SubscriptionTier(str, Enum):
    """Subscription tiers - SCRUM-13"""
    FREE = "free"           # 5 articles/month
    PREMIUM = "premium"     # $9.99/mo - unlimited articles
    VIP = "vip"             # $19.99/mo - unlimited + exclusive content


class User(Base):
    """
    User model for readers, journalists, and editors.
    SCRUM-10: User Authentication & Profiles
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Null for social login
    
    # Profile - SCRUM-14
    display_name = Column(String(100), nullable=False)
    bio = Column(String(500), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Role and permissions
    role = Column(SQLEnum(UserRole), default=UserRole.READER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Subscription - SCRUM-13
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(100), nullable=True)
    
    # Social login - SCRUM-12
    google_id = Column(String(100), nullable=True, index=True)
    apple_id = Column(String(100), nullable=True, index=True)
    
    # Preferences - SCRUM-14
    preferred_categories = Column(String(500), nullable=True)  # JSON array
    email_notifications = Column(Boolean, default=True)
    dark_mode = Column(Boolean, default=False)  # SCRUM-35
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Reading tracking - SCRUM-34
    articles_read_this_month = Column(Integer, default=0)
    
    # Relationships
    articles = relationship("Article", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    bookmarks = relationship("Bookmark", back_populates="user")

    def can_access_premium(self) -> bool:
        """Check if user can access premium content - SCRUM-13"""
        if self.subscription_tier in [SubscriptionTier.PREMIUM, SubscriptionTier.VIP]:
            if self.subscription_expires_at and self.subscription_expires_at > datetime.utcnow():
                return True
        return False

    def can_read_article(self) -> bool:
        """Check if user can read another article this month - SCRUM-13"""
        if self.subscription_tier != SubscriptionTier.FREE:
            return True
        return self.articles_read_this_month < 5


class Subscription(Base):
    """Subscription history - SCRUM-13"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tier = Column(SQLEnum(SubscriptionTier), nullable=False)
    stripe_subscription_id = Column(String(100), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
