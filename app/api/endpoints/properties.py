from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List, Any
from uuid import UUID
from sqlalchemy import func
from geoalchemy2.shape import to_shape

from app.core.database import engine
from app.core.models import PropertyListing, PropertyChangeLog

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

@router.get("/", response_model=List[Any])
def get_properties(session: Session = Depends(get_session)):
    """
    Get all active properties with their GIS info.
    """
    try:
        # Select specific fields to keep payload light
        statement = select(PropertyListing)
        results = session.exec(statement).all()
        
        # Fetch history mapping
        history_stmt = select(PropertyChangeLog.property_id, func.max(PropertyChangeLog.timestamp)).group_by(PropertyChangeLog.property_id)
        history_results = session.exec(history_stmt).all()
        history_map = {str(row[0]): row[1] for row in history_results}
        
        properties = []
        for prop in results:
            # Convert GeoAlchemy element to Shapely point then to lat/lon
            point = to_shape(prop.location)
            
            properties.append({
                "id": str(prop.id),
                "address": prop.address,
                "price": prop.price,
                "beds": prop.beds,
                "baths": prop.baths,
                "sqft": prop.sqft,
                "status": prop.status,
                "property_url": prop.property_url,
                "gis_tier": prop.gis_tier,
                "gis_contour": prop.gis_contour,
                "lat": point.y,
                "lon": point.x,
                "created_at": prop.created_at,
                "latest_change": history_map.get(str(prop.id))
            })
        return properties
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{property_id}/history")
def get_property_history(property_id: str, session: Session = Depends(get_session)):
    """
    Get change history for a specific property.
    """
    try:
        # Sort by timestamp descending (newest first)
        statement = select(PropertyChangeLog).where(PropertyChangeLog.property_id == UUID(property_id)).order_by(PropertyChangeLog.timestamp.desc())
        history = session.exec(statement).all()
        
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
