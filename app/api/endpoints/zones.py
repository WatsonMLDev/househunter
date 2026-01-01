from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, text
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
import json

from app.core.database import engine
from app.core.models import HunterZone

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

@router.get("/match")
def get_zone(lat: float, lon: float, session: Session = Depends(get_session)):
    """
    Match a location (lat, lon) to a Hunter Zone using the database stored procedure.
    Prioritizes the smallest contour (best tier).
    """
    try:
        # Call the stored procedure
        statement = text("SELECT tier, contour FROM match_listing_zone(:lon, :lat)")
        params = {"lon": lon, "lat": lat}
        result = session.exec(statement, params=params).first()
        
        if result:
            return {"tier": result.tier, "contour": result.contour}
        else:
            return {"tier": None, "contour": None, "message": "No zone found for these coordinates."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def get_zones(session: Session = Depends(get_session)):
    """
    Get all Hunter Zones as GeoJSON
    """
    try:
        zones = session.exec(select(HunterZone)).all()
        
        features = []
        for zone in zones:
            # Convert WKBElement to Shapely geometry
            shapely_geom = to_shape(zone.geom)
            # Convert to GeoJSON geometry
            geojson_geom = mapping(shapely_geom)
            
            features.append({
                "type": "Feature",
                "geometry": geojson_geom,
                "properties": {
                    "id": str(zone.id),
                    "tier": zone.tier,
                    "contour": zone.contour
                }
            })
            
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
