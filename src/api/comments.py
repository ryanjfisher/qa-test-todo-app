"""
Comments API endpoints.
SCRUM-16: Build threaded comment system
SCRUM-17: Implement comment moderation system
SCRUM-18: Add reaction system for articles and comments
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..services.comment_service import CommentService
from ..api.auth import oauth2_scheme
from ..core.security import decode_token

router = APIRouter()


class CreateCommentRequest(BaseModel):
    """SCRUM-16: Threaded comment"""
    content: str
    article_id: int
    parent_id: Optional[int] = None  # For replies


class UpdateCommentRequest(BaseModel):
    content: str


class AddReactionRequest(BaseModel):
    """SCRUM-18: Reaction types"""
    reaction_type: str  # like, love, angry, sad, wow


class ModerationActionRequest(BaseModel):
    """SCRUM-17: Moderation actions"""
    action: str  # approve, reject, delete
    reason: Optional[str] = None


class CommentResponse(BaseModel):
    id: int
    content: str
    article_id: int
    author_id: int
    author_name: str
    parent_id: Optional[int]
    is_edited: bool
    created_at: datetime
    replies: List["CommentResponse"] = []
    
    class Config:
        from_attributes = True


@router.get("/article/{article_id}")
async def get_article_comments(
    article_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    comment_service: CommentService = Depends()
):
    """
    Get comments for an article with threading.
    SCRUM-16: Build threaded comment system
    """
    comments = await comment_service.get_article_comments(
        article_id=article_id,
        page=page,
        per_page=per_page
    )
    return {"comments": comments, "article_id": article_id}


@router.post("/", response_model=CommentResponse)
async def create_comment(
    request: CreateCommentRequest,
    token: str = Depends(oauth2_scheme),
    comment_service: CommentService = Depends()
):
    """
    Create a new comment or reply.
    SCRUM-16: Build threaded comment system
    """
    payload = decode_token(token)
    author_id = payload.get("sub")
    
    # Rate limiting - max 10 comments per hour
    can_comment = await comment_service.check_rate_limit(author_id)
    if not can_comment:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Comment rate limit exceeded. Try again later."
        )
    
    # Check nesting depth (max 3 levels) - SCRUM-16
    if request.parent_id:
        depth = await comment_service.get_comment_depth(request.parent_id)
        if depth >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum reply depth reached"
            )
    
    comment = await comment_service.create(
        content=request.content,
        article_id=request.article_id,
        author_id=author_id,
        parent_id=request.parent_id
    )
    
    return comment


@router.put("/{comment_id}")
async def update_comment(
    comment_id: int,
    request: UpdateCommentRequest,
    token: str = Depends(oauth2_scheme),
    comment_service: CommentService = Depends()
):
    """Edit a comment (shows as edited) - SCRUM-16"""
    payload = decode_token(token)
    author_id = payload.get("sub")
    
    comment = await comment_service.update(comment_id, author_id, request.content)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return comment


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    token: str = Depends(oauth2_scheme),
    comment_service: CommentService = Depends()
):
    """Delete own comment - SCRUM-16"""
    payload = decode_token(token)
    author_id = payload.get("sub")
    
    success = await comment_service.delete(comment_id, author_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return {"message": "Comment deleted"}


# ============ Reactions - SCRUM-18 ============

@router.post("/{comment_id}/reactions")
async def add_reaction(
    comment_id: int,
    request: AddReactionRequest,
    token: str = Depends(oauth2_scheme),
    comment_service: CommentService = Depends()
):
    """
    Add or toggle a reaction on a comment.
    SCRUM-18: Add reaction system for articles and comments
    """
    if request.reaction_type not in ["like", "love", "angry", "sad", "wow"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reaction type")
    
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    result = await comment_service.toggle_reaction(comment_id, user_id, request.reaction_type)
    return result


@router.get("/{comment_id}/reactions")
async def get_reactions(
    comment_id: int,
    comment_service: CommentService = Depends()
):
    """Get reaction counts for a comment - SCRUM-18"""
    reactions = await comment_service.get_reaction_counts(comment_id)
    return reactions


# ============ Moderation - SCRUM-17 ============

@router.post("/{comment_id}/flag")
async def flag_comment(
    comment_id: int,
    reason: str = Query(...),
    token: str = Depends(oauth2_scheme),
    comment_service: CommentService = Depends()
):
    """Flag a comment for moderation - SCRUM-17"""
    payload = decode_token(token)
    reporter_id = payload.get("sub")
    
    await comment_service.flag_comment(comment_id, reporter_id, reason)
    return {"message": "Comment flagged for review"}


@router.get("/moderation/queue")
async def get_moderation_queue(
    token: str = Depends(oauth2_scheme),
    comment_service: CommentService = Depends()
):
    """
    Get flagged comments for moderation.
    SCRUM-17: Implement comment moderation system
    """
    payload = decode_token(token)
    moderator_id = payload.get("sub")
    
    # Verify moderator role
    if not await comment_service.is_moderator(moderator_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    queue = await comment_service.get_moderation_queue()
    return {"flagged_comments": queue}


@router.post("/{comment_id}/moderate")
async def moderate_comment(
    comment_id: int,
    request: ModerationActionRequest,
    token: str = Depends(oauth2_scheme),
    comment_service: CommentService = Depends()
):
    """
    Take moderation action on a comment.
    SCRUM-17: Implement comment moderation system
    """
    payload = decode_token(token)
    moderator_id = payload.get("sub")
    
    if not await comment_service.is_moderator(moderator_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    if request.action not in ["approve", "reject", "delete"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")
    
    result = await comment_service.moderate(
        comment_id=comment_id,
        moderator_id=moderator_id,
        action=request.action,
        reason=request.reason
    )
    
    return {"message": f"Comment {request.action}d", "comment_id": comment_id}
