import json
import logging
from typing import List, Dict, Any
from sqlmodel import Session, select, text
from shapely.geometry import shape
from geoalchemy2.shape import from_shape, to_shape
from app.core.database import engine
from app.core.models import HunterZone, PropertyListing
from app.services.gis import GISService
from app.core.config import AppConfig

logger = logging.getLogger(__name__)

class AdminService:
    @staticmethod
    def backfill_gis_data(session: Session):
        """
        Iterates over all properties and re-calculates their GIS zone.
        """
        logger.info("Starting GIS data backfill...")
        
        # Fetch all listings
        listings = session.exec(select(PropertyListing)).all()
        logger.info(f"Found {len(listings)} listings to check.")
        
        updated_count = 0
        
        for listing in listings:
            if listing.location is None:
                continue

            # Extract Lat/Lon from GeoAlchemy2 WKBElement
            point = to_shape(listing.location)
            lon = point.x
            lat = point.y
            
            # Lookup Zone
            tier, contour = GISService.lookup_zone(session, lat, lon)
            
            # Update if changed
            if listing.gis_tier != tier or listing.gis_contour != contour:
                listing.gis_tier = tier
                listing.gis_contour = contour
                session.add(listing)
                updated_count += 1
        
        session.commit()
        logger.info(f"Backfill complete. Updated {updated_count} listings.")
        return updated_count

    @staticmethod
    def seed_zones_from_geojson(geojson_content: Dict[str, Any], session: Session):
        """
        Parses GeoJSON content and seeds the HunterZone table.
        Truncates existing zones.
        """
        logger.info("Seeding zones from GeoJSON...")
        
        features = []
        # Handle FeatureCollection or list of features
        if isinstance(geojson_content, dict):
            if geojson_content.get('type') == 'FeatureCollection':
                features = geojson_content.get('features', [])
            elif 'features' in geojson_content:
                 features = geojson_content['features']
        elif isinstance(geojson_content, list):
             # Try to find features in the list if it's a list of collections or features
             if len(geojson_content) > 0 and 'features' in geojson_content[0]:
                 features = geojson_content[0]['features']
             else:
                 features = geojson_content # Assume list of features

        zones_to_insert = []

        for feature in features:
            props = feature.get('properties', {})
            contour = props.get('contour')
            
            if contour is None:
                continue
                
            contour = int(contour)

            # Tier Logic (same as script)
            # Tier Logic (from config)
            # Default thresholds if not in config
            tiers_config = AppConfig.get_zone_tiers()
            gold_thresh = tiers_config.get('gold', 40)
            silver_thresh = tiers_config.get('silver', 60)
            bronze_thresh = tiers_config.get('bronze', 75)
            
            tier = None
            if contour <= gold_thresh:
                tier = 'gold'
            elif contour <= silver_thresh:
                tier = 'silver'
            elif contour <= bronze_thresh:
                tier = 'bronze'
            else:
                continue

            try:
                # Parse Geometry
                geom_shape = shape(feature['geometry'])
                # Convert to WKBElement (srid=4326)
                geom_wkb = from_shape(geom_shape, srid=4326)
                
                zone = HunterZone(
                    tier=tier,
                    contour=contour,
                    geom=geom_wkb
                )
                zones_to_insert.append(zone)
            except Exception as e:
                logger.error(f"Skipping feature due to error: {e}")
                continue

        if not zones_to_insert:
            logger.warning("No valid zones found to insert.")
            return 0

        # Truncate existing zones
        session.exec(text("TRUNCATE TABLE hunter_zones CASCADE;"))
        
        # Insert new zones
        session.add_all(zones_to_insert)
        session.commit()
        
        count = len(zones_to_insert)
        logger.info(f"Done. Inserted {count} zones.")
        return count
