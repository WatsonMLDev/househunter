import sys
import os
from sqlmodel import Session
from sqlalchemy import text

# Adjust path to include project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine

def verify_lookup():
    # Coordinate from scripts/test.json: -78.107976, 38.749434 (inside contour 75)
    lat = 38.749434
    lon = -78.107976
    
    print(f"Testing lookup for ({lat}, {lon})")
    
    with Session(engine) as session:
        statement = text("SELECT tier, contour FROM match_listing_zone(:lon, :lat)")
        result = session.exec(statement, params={"lon": lon, "lat": lat}).first()
        
        if result:
            print(f"SUCCESS: Found zone - Tier: {result.tier}, Contour: {result.contour}")
        else:
            print("FAILURE: No zone found.")

if __name__ == "__main__":
    verify_lookup()
