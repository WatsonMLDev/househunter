from sqlmodel import Session, select, func
import sys
import os

# Adjust path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine
from app.models import HunterZone

def check_zones():
    with Session(engine) as session:
        count = session.exec(select(func.count(HunterZone.id))).one()
        print(f"HunterZone count: {count}")
        
        if count > 0:
            # Check Extent
            # ST_Extent returns a box2d, we might need ST_AsText or similar to read it easily via python if not mapped
            # Or just get one geom to verify
            print("Table has data.")

if __name__ == "__main__":
    check_zones()
