from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from sqlmodel import Session
import json

from app.core.database import engine
from app.services.scraper import scrape_and_store_properties
from app.services.admin import AdminService

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/populate")
def populate_db(background_tasks: BackgroundTasks):
    """
    Trigger the scraper to populate the database.
    Running in background to avoid timeout.
    """
    from app.core.config import AppConfig
    
    locations = AppConfig.get_locations()
    scraper_settings = AppConfig.get_scraper_settings()
    listing_types = scraper_settings.get("listing_types", ["for_sale"])
    past_days = scraper_settings.get("default_past_days", 30)
    
    background_tasks.add_task(scrape_and_store_properties, locations=locations, listing_type=listing_types, past_days=past_days)
    return {"message": "Scraper job started in background.", "locations_count": len(locations)}

@router.post("/backfill-gis")
def backfill_gis(background_tasks: BackgroundTasks):
    """
    Trigger backfill of GIS data for all properties.
    """
    def _backfill_task():
        with Session(engine) as session:
            AdminService.backfill_gis_data(session)

    background_tasks.add_task(_backfill_task)
    return {"message": "GIS Backfill started in background."}

@router.post("/seed-zones")
async def seed_zones(file: UploadFile = File(...)):
    """
    Seed Hunter Zones from an uploaded GeoJSON file.
    """
    try:
        content = await file.read()
        geojson_data = json.loads(content)
        
        with Session(engine) as session:
            count = AdminService.seed_zones_from_geojson(geojson_data, session)
            
        return {"message": f"Successfully seeded {count} zones."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
