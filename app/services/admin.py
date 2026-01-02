import json
import logging
import requests
from typing import List, Dict, Any, Optional
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

    @staticmethod
    def generate_zones_from_valhalla(
        session: Session,
        lat: float,
        lon: float,
        contours: List[int], # e.g. [15, 30, 45]
        valhalla_url: str = "https://valhalla1.openstreetmap.de/isochrone",
        costing: str = "auto"
    ) -> int:
        """
        Calls Valhalla Isochrone API, parses response, seeds zones, and triggers backfill.
        """
        logger.info(f"Requests Valhalla Isochrones at {lat}, {lon} with contours {contours}")

        # 1. Prepare Request
        # Valhalla expects contours in minutes
        contest_list = [{"time": c} for c in contours]
        
        payload = {
            "locations": [{"lat": lat, "lon": lon}],
            "costing": costing,
            "contours": contest_list,
            "polygons": True
        }

        try:
            # 2. Call API
            resp = requests.post(valhalla_url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            # 3. Seed Zones (Reuse logic)
            # note: Valhalla returns a FeatureCollection. 
            # We need to map the 'contour' (minutes) to our 'tier' logic.
            # However, our seed_zones_from_geojson logic relies on AppConfig for tiers.
            # To support dynamic custom contours effectively, we might need to override 
            # or ensure the seed logic respects the order.
            
            # The seed_zones_from_geojson logic uses hardcoded config check. 
            # Let's do a refined insertion here specifically for this generation flow
            # to ensure strict mapping: Smallest = Gold, Middle = Silver, Largest = Bronze.
            
            # Sort contours to be sure
            contours.sort()
            
            # Mapping logic:
            # contours[0] -> Gold
            # contours[1] -> Silver
            # contours[2] -> Bronze
            # Any others -> Bronze or ignore? User said 3 tiers + Zinc (fallback).
            # We assume the user sends exactly 3 contours for the 3 tiers.
            
            tier_map = {}
            if len(contours) >= 1: tier_map[contours[0]] = 'gold'
            if len(contours) >= 2: tier_map[contours[1]] = 'silver'
            if len(contours) >= 3: tier_map[contours[2]] = 'bronze'
            
            features = data.get('features', [])
            zones_to_insert = []
            
            for feature in features:
                props = feature.get('properties', {})
                contour_val = props.get('contour')
                if contour_val is None: 
                    continue
                
                contour_int = int(contour_val)
                tier = tier_map.get(contour_int)
                
                if not tier:
                    # Fallback if valhalla returns slightly different float or something
                    # Find closest? For now exact match or skip.
                    logger.warning(f"Contour {contour_int} not in map {tier_map}. Skipping.")
                    continue
                    
                geom_shape = shape(feature['geometry'])
                geom_wkb = from_shape(geom_shape, srid=4326)
                
                zone = HunterZone(
                    tier=tier,
                    contour=contour_int,
                    geom=geom_wkb
                )
                zones_to_insert.append(zone)
            
            if not zones_to_insert:
                logger.error("No valid zones parsed from Valhalla response.")
                return 0

            # Truncate and Insert
            session.exec(text("TRUNCATE TABLE hunter_zones CASCADE;"))
            session.add_all(zones_to_insert)
            session.commit()
            
            count = len(zones_to_insert)
            logger.info(f"Generated and inserted {count} zones from Valhalla.")
            
            # 4. Trigger Backfill
            logger.info("Triggering GIS Backfill after new zones...")
            AdminService.backfill_gis_data(session)
            
            return count

        except Exception as e:
            logger.error(f"Valhalla generation failed: {e}")
            raise e
