from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

class HunterBase(SQLModel):
    pass

class HunterZone(HunterBase, table=True):
    __tablename__ = "hunter_zones"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tier: str  # 'gold', 'silver', 'bronze'
    contour: int # minutes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Critical: GeoAlchemy2 Geometry
    geom: Any = Field(sa_column=Column(Geometry("POLYGON", srid=4326)))

    class Config:
        arbitrary_types_allowed = True

class PropertyListing(HunterBase, table=True):
    __tablename__ = "property_listings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    external_id: str = Field(unique=True, index=True)
    address: str
    price: Optional[float] = None
    status: str
    listing_type: str 
    
    # New fields
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None
    property_url: Optional[str] = None
    mls: Optional[str] = None
    price_tier: Optional[str] = None
    gis_tier: Optional[str] = None
    gis_contour: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)



    
    # Critical: GeoAlchemy2 Geometry
    location: Any = Field(sa_column=Column(Geometry("POINT", srid=4326)))

    class Config:
        arbitrary_types_allowed = True

class PropertyChangeLog(HunterBase, table=True):
    __tablename__ = "property_change_log"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    property_id: UUID = Field(foreign_key="property_listings.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    changes: Dict[str, Any] = Field(sa_column=Column(JSONB))

