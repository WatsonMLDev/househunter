from sqlmodel import Session, select
from app.models import PropertyListing
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from typing import Dict, Any, List

class PropertyStorage:
    @staticmethod
    def upsert_property(session: Session, data: Dict[str, Any], listing_type: List[str]) -> bool:
        """
        Upserts a property listing into the database.
        Returns True if a new listing was created, False if updated.
        """
        prop_url = data['prop_url']
        
        existing = session.exec(select(PropertyListing).where(PropertyListing.external_id == prop_url)).first()
        
        is_new = False
        if existing:
            # Update
            existing.price = data['price']
            existing.status = data['status']
            existing.price_tier = data['price_tier']
            existing.gis_tier = data['gis_tier']
            existing.gis_contour = data['gis_contour']
            existing.beds = data['beds']
            existing.baths = data['baths']
            existing.sqft = data['sqft']
            session.add(existing)
        else:
            # Create
            listing = PropertyListing(
                external_id=str(prop_url),
                address=data['address'],
                price=data['price'],
                status=data['status'],
                listing_type=listing_type,
                beds=data['beds'],
                baths=data['baths'],
                sqft=data['sqft'],
                year_built=data['year_built'],
                property_url=str(prop_url),
                mls=data['mls'],
                price_tier=data['price_tier'],
                gis_tier=data['gis_tier'],
                gis_contour=data['gis_contour'],
                location=from_shape(Point(data['lon'], data['lat']), srid=4326)
            )
            session.add(listing)
            is_new = True
            
        return is_new
