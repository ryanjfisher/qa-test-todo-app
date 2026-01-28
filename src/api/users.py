"""
User API endpoints.
SCRUM-14: Create user profile and preferences page
SCRUM-13: Build subscription tier management
SCRUM-32: Add article bookmarking feature
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..services.user_service import UserService
from ..services.subscription_service import SubscriptionService
from ..api.auth import oauth2_scheme
from ..core.security import decode_token

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    """SCRUM-14: Profile updates"""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UpdatePreferencesRequest(BaseModel):
    """SCRUM-14: User preferences"""
    preferred_categories: Optional[List[str]] = None
    email_notifications: Optional[bool] = None
    dark_mode: Optional[bool] = None  # SCRUM-35


class SubscribeRequest(BaseModel):
    """SCRUM-13: Subscription management"""
    tier: str  # premium, vip
    payment_method_id: str


class ProfileResponse(BaseModel):
    id: int
    email: str
    display_name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    subscription_tier: str
    preferred_categories: Optional[List[str]]
    dark_mode: bool
    
    class Config:
        from_attributes = True


@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Get current user's profile.
    SCRUM-14: Create user profile and preferences page
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return user


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Update user profile.
    SCRUM-14: Create user profile and preferences page
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    user = await user_service.update_profile(
        user_id=user_id,
        display_name=request.display_name,
        bio=request.bio,
        avatar_url=request.avatar_url
    )
    
    return user


@router.put("/me/preferences")
async def update_preferences(
    request: UpdatePreferencesRequest,
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Update user preferences.
    SCRUM-14: Create user profile and preferences page
    SCRUM-35: Add dark mode support
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    await user_service.update_preferences(
        user_id=user_id,
        preferred_categories=request.preferred_categories,
        email_notifications=request.email_notifications,
        dark_mode=request.dark_mode
    )
    
    return {"message": "Preferences updated"}


# ============ Subscriptions - SCRUM-13 ============

@router.get("/me/subscription")
async def get_subscription(
    token: str = Depends(oauth2_scheme),
    subscription_service: SubscriptionService = Depends()
):
    """
    Get current subscription status.
    SCRUM-13: Build subscription tier management
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    subscription = await subscription_service.get_user_subscription(user_id)
    return subscription


@router.post("/me/subscription")
async def subscribe(
    request: SubscribeRequest,
    token: str = Depends(oauth2_scheme),
    subscription_service: SubscriptionService = Depends()
):
    """
    Subscribe to a plan.
    SCRUM-13: Build subscription tier management
    """
    if request.tier not in ["premium", "vip"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tier")
    
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    subscription = await subscription_service.create_subscription(
        user_id=user_id,
        tier=request.tier,
        payment_method_id=request.payment_method_id
    )
    
    return {"message": f"Subscribed to {request.tier}", "subscription": subscription}


@router.delete("/me/subscription")
async def cancel_subscription(
    token: str = Depends(oauth2_scheme),
    subscription_service: SubscriptionService = Depends()
):
    """
    Cancel subscription (remains active until period end).
    SCRUM-13: Build subscription tier management
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    result = await subscription_service.cancel_subscription(user_id)
    return {"message": "Subscription cancelled", "expires_at": result.expires_at}


# ============ Bookmarks - SCRUM-32 ============

@router.get("/me/bookmarks")
async def get_bookmarks(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Get user's bookmarked articles.
    SCRUM-32: Add article bookmarking feature
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    bookmarks = await user_service.get_bookmarks(user_id)
    return {"bookmarks": bookmarks}


@router.post("/me/bookmarks/{article_id}")
async def add_bookmark(
    article_id: int,
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Bookmark an article.
    SCRUM-32: Add article bookmarking feature
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    await user_service.add_bookmark(user_id, article_id)
    return {"message": "Article bookmarked"}


@router.delete("/me/bookmarks/{article_id}")
async def remove_bookmark(
    article_id: int,
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Remove bookmark.
    SCRUM-32: Add article bookmarking feature
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    await user_service.remove_bookmark(user_id, article_id)
    return {"message": "Bookmark removed"}


# ============ Reading History - SCRUM-34 ============

@router.get("/me/history")
async def get_reading_history(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """Get user's reading history for recommendations - SCRUM-34"""
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    history = await user_service.get_reading_history(user_id)
    return {"history": history}
