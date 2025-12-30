import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db
from app.scraper import scrape_and_store_properties

def populate_database():
    print("Initializing Database...")
    init_db()
    
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
    
    print(f"Starting population for {len(locations)} locations. Fetching past 30 days of data...")
    # Scrape past 30 days to get active listings
    scrape_and_store_properties(locations=locations, listing_type=["for_sale"], past_days=30)
    print("Population complete.")

if __name__ == "__main__":
    populate_database()
