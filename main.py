from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from app.core.database import init_db
from app.services.scraper import scrape_and_store_properties
from app.api.api import api_router

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("househunter")

# Scheduler Instance
scheduler = AsyncIOScheduler()

from app.core.config import AppConfig

def run_scraper_job():
    locations = AppConfig.get_locations()
    scraper_settings = AppConfig.get_scraper_settings()
    listing_types = scraper_settings.get("listing_types", ["for_sale"])
    
    logger.info("Triggering scheduled scraper job...")
    scrape_and_store_properties(locations=locations, listing_type=listing_types)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Init DB and Scheduler
    logger.info("Initializing Database...")
    init_db()
    
    logger.info("Starting Scheduler...")
    interval = AppConfig.get_scheduler_interval()
    scheduler.add_job(run_scraper_job, 'interval', hours=interval)
    scheduler.start()
    
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

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Hunter Toolbelt is active. The Muscle is ready."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
