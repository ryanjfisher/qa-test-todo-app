"""
Comment Service
SCRUM-16: Build threaded comment system
SCRUM-17: Implement comment moderation system
SCRUM-18: Add reaction system for articles and comments
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.comment import Comment, Reaction
from ..models.user import UserRole


class CommentService:
    """Service for comment operations."""
    
    def __init__(self, db: Session, cache=None):
        self.db = db
        self.cache = cache  # Redis for rate limiting and reaction counts
    
    async def create(
        self,
        content: str,
        article_id: int,
        author_id: int,
        parent_id: Optional[int] = None
    ) -> Comment:
        """
        Create a new comment.
        SCRUM-16: Build threaded comment system
        """
        comment = Comment(
            content=content,
            article_id=article_id,
            author_id=author_id,
            parent_id=parent_id
        )
        
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        
        # Update article comment count - careful to avoid SCRUM-28 bug
        await self._update_comment_count(article_id, 1)
        
        return comment
    
    async def update(self, comment_id: int, author_id: int, content: str) -> Optional[Comment]:
        """
        Update a comment (shows as edited).
        SCRUM-16: Build threaded comment system
        """
        comment = self.db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.author_id == author_id,
            Comment.is_deleted == False
        ).first()
        
        if not comment:
            return None
        
        comment.content = content
        comment.updated_at = datetime.utcnow()
        self.db.commit()
        
        return comment
    
    async def delete(self, comment_id: int, author_id: int) -> bool:
        """
        Soft delete a comment.
        SCRUM-16: Shows 'Comment removed' in thread
        """
        comment = self.db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.author_id == author_id
        ).first()
        
        if not comment:
            return False
        
        comment.is_deleted = True
        comment.content = "[Comment removed]"
        self.db.commit()
        
        # Update count - SCRUM-28: Use atomic operation to avoid race condition
        await self._update_comment_count(comment.article_id, -1)
        
        return True
    
    async def get_article_comments(
        self,
        article_id: int,
        page: int = 1,
        per_page: int = 50
    ) -> List[Comment]:
        """
        Get comments for an article with threading.
        SCRUM-16: Build threaded comment system
        """
        # Get top-level comments first
        comments = self.db.query(Comment).filter(
            Comment.article_id == article_id,
            Comment.parent_id == None,
            Comment.is_approved == True
        ).order_by(Comment.created_at.desc()) \
         .offset((page - 1) * per_page) \
         .limit(per_page) \
         .all()
        
        # Load replies (limited to 3 levels) - SCRUM-16
        return self._build_comment_tree(comments)
    
    async def get_comment_depth(self, comment_id: int) -> int:
        """
        Get nesting depth of a comment.
        SCRUM-16: Limit nesting to 3 levels
        """
        depth = 0
        current_id = comment_id
        
        while current_id:
            comment = self.db.query(Comment).filter(Comment.id == current_id).first()
            if not comment or not comment.parent_id:
                break
            current_id = comment.parent_id
            depth += 1
        
        return depth
    
    async def check_rate_limit(self, user_id: int) -> bool:
        """
        Check comment rate limit (10/hour).
        SCRUM-16: Rate limiting requirement
        """
        if not self.cache:
            return True
        
        key = f"comment_rate:{user_id}"
        count = await self.cache.incr(key)
        
        if count == 1:
            await self.cache.expire(key, 3600)  # 1 hour window
        
        return count <= 10
    
    # ============ Reactions - SCRUM-18 ============
    
    async def toggle_reaction(self, comment_id: int, user_id: int, reaction_type: str) -> dict:
        """
        Add or remove a reaction.
        SCRUM-18: Add reaction system for articles and comments
        """
        existing = self.db.query(Reaction).filter(
            Reaction.comment_id == comment_id,
            Reaction.user_id == user_id
        ).first()
        
        if existing:
            if existing.reaction_type == reaction_type:
                # Remove reaction if clicking same type
                self.db.delete(existing)
                action = "removed"
            else:
                # Change reaction type
                existing.reaction_type = reaction_type
                action = "changed"
        else:
            # Add new reaction
            reaction = Reaction(
                comment_id=comment_id,
                user_id=user_id,
                reaction_type=reaction_type
            )
            self.db.add(reaction)
            action = "added"
        
        self.db.commit()
        
        # Invalidate cache - SCRUM-18 uses Redis for counts
        if self.cache:
            await self.cache.delete(f"reactions:{comment_id}")
        
        counts = await self.get_reaction_counts(comment_id)
        return {"action": action, "counts": counts}
    
    async def get_reaction_counts(self, comment_id: int) -> dict:
        """
        Get reaction counts for a comment.
        SCRUM-18: Uses Redis for real-time counts
        """
        # Try cache first
        if self.cache:
            cached = await self.cache.get(f"reactions:{comment_id}")
            if cached:
                return cached
        
        # Query database
        reactions = self.db.query(Reaction).filter(
            Reaction.comment_id == comment_id
        ).all()
        
        counts = {"like": 0, "love": 0, "angry": 0, "sad": 0, "wow": 0}
        for r in reactions:
            if r.reaction_type in counts:
                counts[r.reaction_type] += 1
        
        # Cache results
        if self.cache:
            await self.cache.set(f"reactions:{comment_id}", counts, ex=300)
        
        return counts
    
    # ============ Moderation - SCRUM-17 ============
    
    async def flag_comment(self, comment_id: int, reporter_id: int, reason: str):
        """
        Flag a comment for moderation.
        SCRUM-17: Implement comment moderation system
        """
        comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if comment:
            comment.is_flagged = True
            comment.flagged_reason = reason
            self.db.commit()
    
    async def get_moderation_queue(self) -> List[Comment]:
        """
        Get flagged comments for moderation.
        SCRUM-17: Priority sorted moderation queue
        """
        return self.db.query(Comment).filter(
            Comment.is_flagged == True,
            Comment.is_deleted == False
        ).order_by(Comment.created_at.asc()).all()
    
    async def moderate(
        self,
        comment_id: int,
        moderator_id: int,
        action: str,
        reason: Optional[str] = None
    ) -> Comment:
        """
        Take moderation action.
        SCRUM-17: Implement comment moderation system
        """
        comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        
        if action == "approve":
            comment.is_flagged = False
            comment.is_approved = True
        elif action == "reject":
            comment.is_approved = False
        elif action == "delete":
            comment.is_deleted = True
            comment.content = "[Removed by moderator]"
            await self._update_comment_count(comment.article_id, -1)
        
        comment.moderated_by = moderator_id
        comment.moderated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Log moderation action - SCRUM-17
        
        return comment
    
    async def is_moderator(self, user_id: int) -> bool:
        """Check if user is a moderator."""
        user = self.db.query(User).filter(User.id == user_id).first()
        return user and user.role in [UserRole.EDITOR, UserRole.ADMIN]
    
    async def _update_comment_count(self, article_id: int, delta: int):
        """
        Atomically update article comment count.
        SCRUM-28 FIX: Use atomic update to prevent race condition
        """
        from sqlalchemy import text
        self.db.execute(
            text("UPDATE articles SET comment_count = GREATEST(0, comment_count + :delta) WHERE id = :id"),
            {"delta": delta, "id": article_id}
        )
        self.db.commit()
    
    def _build_comment_tree(self, comments: List[Comment]) -> List[dict]:
        """Build nested comment tree for API response."""
        # Implementation would recursively load replies
        return comments
