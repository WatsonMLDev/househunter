from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.api.deps import get_session
from app.core.models import User, UserSettings, UserInteraction
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID

router = APIRouter()

class InteractionUpdate(BaseModel):
    property_id: str
    is_favorite: Optional[bool] = None
    is_rejected: Optional[bool] = None
    is_undecided: Optional[bool] = None
    is_viewed: Optional[bool] = None

class SettingsUpdate(BaseModel):
    max_scrape_price: Optional[int] = None
    # Add other fields as needed

class SyncRequest(BaseModel):
    account_id: str
    interactions: List[InteractionUpdate]
    settings: Optional[SettingsUpdate] = None

@router.post("/sync")
def sync_user_data(req: SyncRequest, session: Session = Depends(get_session)):
    # 1. Get User
    user = session.exec(select(User).where(User.account_id == req.account_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 2. Sync Interactions
    # Fetch existing interactions for this user
    existing_interactions = session.exec(select(UserInteraction).where(UserInteraction.user_id == user.id)).all()
    existing_map = {str(i.property_id): i for i in existing_interactions}
    
    for item in req.interactions:
        # Check if interaction exists in DB
        if item.property_id in existing_map:
            # Update existing
            interaction = existing_map[item.property_id]
            if item.is_favorite is not None: interaction.is_favorite = item.is_favorite
            if item.is_rejected is not None: interaction.is_rejected = item.is_rejected
            if item.is_undecided is not None: interaction.is_undecided = item.is_undecided
            if item.is_viewed is not None: interaction.is_viewed = item.is_viewed
            session.add(interaction)
        else:
            # Create new
            try:
                interaction = UserInteraction(
                    user_id=user.id, 
                    property_id=UUID(item.property_id),
                    is_favorite=item.is_favorite or False,
                    is_rejected=item.is_rejected or False,
                    is_undecided=item.is_undecided or False,
                    is_viewed=item.is_viewed or False
                )
                session.add(interaction)
            except ValueError:
                continue # Skip invalid UUIDs
            
    # 3. Sync Settings
    if req.settings:
         settings = session.exec(select(UserSettings).where(UserSettings.user_id == user.id)).first()
         if settings:
             if req.settings.max_scrape_price is not None:
                 settings.max_scrape_price = req.settings.max_scrape_price
             session.add(settings)
    
    session.commit()
    
    return {"status": "synced"}

@router.get("/{account_id}")
def get_user_data(account_id: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.account_id == account_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interactions = session.exec(select(UserInteraction).where(UserInteraction.user_id == user.id)).all()
    settings = session.exec(select(UserSettings).where(UserSettings.user_id == user.id)).first()
    
    # Format interactions for frontend
    # Frontend expects: favorites: [id, id], rejected: [id, id], etc.
    favorites = [str(i.property_id) for i in interactions if i.is_favorite]
    rejected = [str(i.property_id) for i in interactions if i.is_rejected]
    undecided = [str(i.property_id) for i in interactions if i.is_undecided]
    viewed = [str(i.property_id) for i in interactions if i.is_viewed]
    
    return {
        "account_id": user.account_id,
        "favorites": favorites,
        "rejected": rejected,
        "undecided": undecided,
        "viewed": viewed,
        "settings": settings
    }
