from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, text, select
from app.database import init_db, engine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scraper import scrape_and_store_properties
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("househunter")

# Scheduler Instance
scheduler = AsyncIOScheduler()

def run_scraper_job():
    # Full list of target locations
    locations = [
        "Amherst County, VA", "Nelson County, VA", "Charlottesville city, VA", "Powhatan County, VA", 
        "Lexington city, VA", "Highland County, VA", "Rockbridge County, VA", "Lynchburg city, VA", 
        "Augusta County, VA", "Buckingham County, VA", "Harrisonburg city, VA", "Shenandoah County, VA", 
        "Page County, VA", "Rockingham County, VA", "Albemarle County, VA", "Madison County, VA", 
        "Orange County, VA", "Louisa County, VA", "Henrico County, VA", "Fauquier County, VA", 
        "Cumberland County, VA", "Fluvanna County, VA", "Culpeper County, VA", "Spotsylvania County, VA", 
        "Appomattox County, VA", "Greene County, VA", "Rappahannock County, VA", "Chesterfield County, VA", 
        "Waynesboro city, VA", "Campbell County, VA", "Richmond city, VA", "Hanover County, VA", 
        "Buena Vista city, VA", "Staunton city, VA", "Prince Edward County, VA", "Goochland County, VA"
    ]
    logger.info("Triggering scheduled scraper job...")
    scrape_and_store_properties(locations=locations, listing_type=["for_sale"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Init DB and Scheduler
    logger.info("Initializing Database...")
    init_db()
    
    logger.info("Starting Scheduler...")
    scheduler.add_job(run_scraper_job, 'interval', hours=3)
    scheduler.start()
    
    # Run a job immediately on startup for verification (optional, can be removed)
    # scheduler.add_job(run_scraper_job) 
    
    yield
    
    # Shutdown
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()

app = FastAPI(title="The Hunter Toolbelt", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development convenience. In prod, restrict to specific domains.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hunter Toolbelt is active. The Muscle is ready."}

@app.get("/zone")
def get_zone(lat: float, lon: float):
    """
    Match a location (lat, lon) to a Hunter Zone using the database stored procedure.
    Prioritizes the smallest contour (best tier).
    """
    try:
        with Session(engine) as session:
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

@app.get("/properties")
def get_properties():
    """
    Get all active properties with their GIS info.
    """
    try:
        with Session(engine) as session:
            from app.models import PropertyListing
            from geoalchemy2.shape import to_shape
            
            # Select specific fields to keep payload light
            statement = select(PropertyListing)
            results = session.exec(statement).all()
            
            # Fetch history mapping
            from app.models import PropertyChangeLog
            from sqlalchemy import func
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
                    "gis_tier": prop.gis_tier,
                    "gis_contour": prop.gis_contour,
                    "lat": point.y,
                    "lon": point.x,
                    "created_at": prop.created_at,
                    "latest_change": history_map.get(str(prop.id))
                })
            return properties
    except Exception as e:
        logger.error(f"Error fetching properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/properties/{property_id}/history")
def get_property_history(property_id: str):
    """
    Get change history for a specific property.
    """
    try:
        with Session(engine) as session:
            from app.models import PropertyChangeLog
            from uuid import UUID
            
            # Sort by timestamp descending (newest first)
            statement = select(PropertyChangeLog).where(PropertyChangeLog.property_id == UUID(property_id)).order_by(PropertyChangeLog.timestamp.desc())
            history = session.exec(statement).all()
            
            return history
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/zones")
def get_zones():
    """
    Get all Hunter Zones as GeoJSON
    """
    try:
        with Session(engine) as session:
            from app.models import HunterZone
            import json
            from geoalchemy2.shape import to_shape
            from shapely.geometry import mapping
            
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
        logger.error(f"Error fetching zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
