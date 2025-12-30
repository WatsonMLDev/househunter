import sys
import os
from sqlmodel import Session, select
from geoalchemy2.shape import to_shape

# Adjust path to include project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine
from app.models import PropertyListing
from app.gis import GISService

def backfill_gis_data():
    print("Starting GIS data backfill...")
    
    with Session(engine) as session:
        # Fetch all listings
        statement = select(PropertyListing)
        listings = session.exec(statement).all()
        
        print(f"Found {len(listings)} listings to check.")
        
        updated_count = 0
        
        for listing in listings:
            if listing.location is None:
                print(f"Skipping listing {listing.id} (No location)")
                continue

            # Extract Lat/Lon from GeoAlchemy2 WKBElement
            point = to_shape(listing.location)
            lon = point.x
            lat = point.y
            
            # Lookup Zone
            tier, contour = GISService.lookup_zone(session, lat, lon)
            
            # Update if changed
            if listing.gis_tier != tier or listing.gis_contour != contour:
                print(f"Updating {listing.id}: {listing.gis_tier} -> {tier}, {listing.gis_contour} -> {contour}")
                listing.gis_tier = tier
                listing.gis_contour = contour
                session.add(listing)
                updated_count += 1
        
        session.commit()
        print(f"Backfill complete. Updated {updated_count} listings.")

if __name__ == "__main__":
    backfill_gis_data()
