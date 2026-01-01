import sys
import os
from uuid import uuid4

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, text
from app.database import engine, init_db
from app.core.models import PropertyListing, PropertyChangeLog
from app.storage import PropertyStorage

def test_history_flow():
    print("Starting History Verification...")
    
    # 1. Setup Mock Data
    prop_url = f"http://test-history-{uuid4()}.com"
    initial_data = {
        'prop_url': prop_url,
        'address': '123 History Lane',
        'price': 300000,
        'status': 'active',
        'beds': 3,
        'baths': 2,
        'sqft': 1500,
        'year_built': 2000,
        'mls': 'TEST1234',
        'price_tier': 'silver',
        'gis_tier': 'gold',
        'gis_contour': 10,
        'lat': 38.0,
        'lon': -78.0
    }
    
    listing_type = ["for_sale"]
    
    with Session(engine) as session:
        # 2. Insert Initial Property
        print("Inserting initial property...")
        is_new = PropertyStorage.upsert_property(session, initial_data, listing_type)
        session.commit()
        
        if not is_new:
            print("ERROR: Property should be new")
            return

        # 3. Fetch ID
        prop = session.exec(select(PropertyListing).where(PropertyListing.external_id == prop_url)).first()
        prop_id = prop.id
        print(f"Property created with ID: {prop_id}")
        
        # 4. Update Property (Price Drop + Status Change)
        print("Updating property...")
        updated_data = initial_data.copy()
        updated_data['price'] = 290000 # Price drop
        updated_data['status'] = 'pending' # Status change
        
        PropertyStorage.upsert_property(session, updated_data, listing_type)
        session.commit()
        
        # 5. Verify History
        print("Verifying history log...")
        history = session.exec(select(PropertyChangeLog).where(PropertyChangeLog.property_id == prop_id)).all()
        
        if len(history) == 1:
            log = history[0]
            print(f"SUCCESS: History record found. Timestamp: {log.timestamp}")
            print(f"Changes: {log.changes}")
            
            # Verify details
            changes = log.changes
            if changes.get('price') == {'old': 300000.0, 'new': 290000.0} and \
               changes.get('status') == {'old': 'active', 'new': 'pending'}:
                print("SUCCESS: Log content matches expected changes.")
            else:
                print(f"FAILURE: Log content mismatch: {changes}")
        else:
            print(f"FAILURE: Expected 1 history record, found {len(history)}")
            
        # 6. Cleanup
        print("Cleaning up test data...")
        # Delete history first (FK constraint)
        session.exec(text(f"DELETE FROM property_change_log WHERE property_id = '{prop_id}'"))
        session.exec(text(f"DELETE FROM property_listings WHERE id = '{prop_id}'"))
        session.commit()
        print("Cleanup complete.")

if __name__ == "__main__":
    init_db()
    test_history_flow()
