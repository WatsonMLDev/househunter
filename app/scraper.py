import logging
from typing import List
import pandas as pd
from homeharvest import scrape_property
from sqlmodel import Session

from app.database import engine
from app.zillow_scraper import ZillowScraper
from app.property_processor import PropertyProcessor
from app.gis import GISService
from app.storage import PropertyStorage

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_and_store_properties(locations: list[str], listing_type: list[str] = ["for_sale", "pending"], past_days: int = 1):
    """
    Scrapes properties for a list of locations using HomeHarvest and Zillow, then stores them.
    Orchestrates: Scraping -> Processing -> GIS Lookup -> Storage.
    """
    logger.info(f"Starting scrape job for {len(locations)} locations. Past days: {past_days}")
    
    total_new = 0
    total_updated = 0
    
    target_property_types = ['single_family', 'multi_family', 'condos', 'townhomes', 'mobile', 'condo_townhome']

    for location in locations:
        logger.info(f"Scraping location: {location}")
        try:
            dfs = []
            
            # 1. HomeHarvest Scrape
            try:
                hh_df = scrape_property(
                    location=location,
                    listing_type=listing_type,
                    past_days=past_days,
                    price_max=275000,
                    property_type=target_property_types
                )
                if not hh_df.empty:
                    dfs.append(hh_df)
            except Exception as e:
                logger.error(f"HomeHarvest scrape failed for {location}: {e}")

            # 2. Zillow Direct Scrape
            # try:
            #     z_df = ZillowScraper.scrape(location)
            #     if not z_df.empty:
            #         dfs.append(z_df)
            # except Exception as e:
            #     logger.error(f"Zillow direct scrape failed for {location}: {e}")

            if not dfs:
                logger.info(f"No properties found for {location} from any source.")
                continue
                
            properties = pd.concat(dfs, ignore_index=True)

            # Log source distribution
            if 'site_name' in properties.columns:
                 logger.info(f"Sources for {location}: {properties['site_name'].unique()}")
            elif 'property_url' in properties.columns:
                 sites = properties['property_url'].apply(lambda x: 'zillow' if 'zillow.com' in str(x) else ('realtor' if 'realtor.com' in str(x) else 'other')).unique()
                 logger.info(f"inferred Sources for {location}: {sites}")

            # 3. Process & Store
            with Session(engine) as session:
                count_loc_new = 0
                count_loc_updated = 0
                
                for _, prop in properties.iterrows():
                    try:
                        # Clean Data
                        data = PropertyProcessor.process_listing(prop)
                        if not data:
                            continue
                        
                        # GIS Lookup
                        tier, contour = GISService.lookup_zone(session, data['lat'], data['lon'])
                        data['gis_tier'] = tier
                        data['gis_contour'] = contour
                        
                        # Store (Upsert)
                        is_new = PropertyStorage.upsert_property(session, data, listing_type)
                        
                        if is_new:
                            count_loc_new += 1
                        else:
                            count_loc_updated += 1
                            
                    except Exception as e:
                        import traceback
                        logger.error(f"Error processing property in {location}: {e} {traceback.format_exc()}")
                        continue
                
                session.commit()
                logger.info(f"Initial processing for {location}: {count_loc_new} new, {count_loc_updated} updated.")
                total_new += count_loc_new
                total_updated += count_loc_updated

        except Exception as e:
            logger.error(f"Failed to scrape {location}: {e}")
            continue

    logger.info(f"Scraping job complete. New: {total_new}, Updated: {total_updated}")
