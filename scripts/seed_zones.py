import sys
import os
import json
import argparse
from typing import List, Dict, Any
from shapely.geometry import shape
from geoalchemy2.shape import from_shape
from sqlmodel import Session, text, select

# Adjust path to include project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, init_db
from app.models import HunterZone

def seed_zones(json_path: str):
    if not os.path.exists(json_path):
        print(f"Error: File not found at {json_path}")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Handle potential array wrapper
    if isinstance(data, list):
        if len(data) > 0 and 'features' in data[0]:
             # Assuming valhalla sometimes returns [ { "type": "FeatureCollection" ... } ]
             features = data[0]['features']
        else:
             # Or maybe just a list of features? Unlikely for Top-level GeoJSON but possible
             print("Warning: unexpected JSON structure. Expecting FeatureCollection or List[FeatureCollection].")
             features = []
    elif isinstance(data, dict) and 'features' in data:
        features = data['features']
    else:
        print("Error: Could not find 'features' list in JSON.")
        return

    zones_to_insert: List[HunterZone] = []

    for feature in features:
        props = feature.get('properties', {})
        contour = props.get('contour')
        
        if contour is None:
            continue
            
        contour = int(contour)

        # Tier Logic
        tier = None
        if contour <= 40:
            tier = 'gold'
        elif contour <= 60:
            tier = 'silver'
        elif contour <= 75:
            tier = 'bronze'
        else:
            # Ignore > 75
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
            print(f"Skipping feature due to error: {e}")
            continue

    if not zones_to_insert:
        print("No valid zones found to insert.")
        return

    with Session(engine) as session:
        # Truncate existing zones (MVP)
        print("Truncating existing zones...")
        session.exec(text("TRUNCATE TABLE hunter_zones CASCADE;"))
        session.commit()

        # Insert new zones
        print(f"Inserting {len(zones_to_insert)} zones...")
        session.add_all(zones_to_insert)
        session.commit()
        print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Hunter Zones from GeoJSON")
    parser.add_argument("json_file", help="Path to the JSON file containing isochrones")
    args = parser.parse_args()
    
    # Ensure DB is init (creates table if not exists)
    init_db()
    
    seed_zones(args.json_file)
