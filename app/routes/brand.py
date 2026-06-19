"""Brand voice profile routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.models import BrandProfile, User
from app.dependencies import get_db, require_user

router = APIRouter(prefix="/api/brand", tags=["brand"])

class BrandProfileRequest(BaseModel):
    brand_name: str = ""
    brand_description: str = ""
    tone: str = "professional"
    target_audience: str = ""
    key_topics: str = ""
    avoid_words: str = ""

@router.get("/profile")
async def get_profile(user: User = Depends(require_user), db=Depends(get_db)):
    """Get user's brand voice profile."""
    result = db.execute(select(BrandProfile).where(BrandProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        return {"brand_name": "", "brand_description": "", "tone": "professional", 
                "target_audience": "", "key_topics": "", "avoid_words": ""}
    return {
        "brand_name": profile.brand_name,
        "brand_description": profile.brand_description,
        "tone": profile.tone,
        "target_audience": profile.target_audience,
        "key_topics": profile.key_topics,
        "avoid_words": profile.avoid_words,
    }

@router.post("/profile")
async def save_profile(req: BrandProfileRequest, user: User = Depends(require_user), db=Depends(get_db)):
    """Save or update brand voice profile."""
    from datetime import datetime, timezone
    result = db.execute(select(BrandProfile).where(BrandProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = BrandProfile(user_id=user.id)
        db.add(profile)
    profile.brand_name = req.brand_name
    profile.brand_description = req.brand_description
    profile.tone = req.tone
    profile.target_audience = req.target_audience
    profile.key_topics = req.key_topics
    profile.avoid_words = req.avoid_words
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "品牌语调已保存", "tone": req.tone}
