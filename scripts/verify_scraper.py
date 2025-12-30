import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, init_db
from app.models import PropertyListing
from app.scraper import scrape_and_store_properties
from sqlmodel import Session, select

def verify_scraper():
    print("Initializing Database...")
    init_db()
    
    print("Running Scraper (this may take a few seconds)...")
    # Verify with a small subset
    test_locations = ["Charlottesville city, VA", "Albemarle County, VA"]
    scrape_and_store_properties(locations=test_locations, listing_type=["for_sale", "pending"])
    
    print("Verifying Database...")
    with Session(engine) as session:
        statement = select(PropertyListing)
        results = session.exec(statement).all()
        
        print(f"Total Properties in DB: {len(results)}")
        if len(results) > 0:
            prop = results[0]
            print(f"Sample Property: {prop.address} - ${prop.price}")
            print(f"Details: {prop.beds} beds, {prop.baths} baths, {prop.sqft} sqft")
            print(f"Price Tier: {prop.price_tier}")
            print(f"GIS Tier: {prop.gis_tier}, Contour: {prop.gis_contour}")

        else:
            print("No properties found in DB.")

if __name__ == "__main__":
    verify_scraper()
