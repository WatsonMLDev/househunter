import os
from sqlmodel import create_engine, SQLModel, Session, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def init_db():
    with engine.connect() as conn:
        # 1. Create PostGIS extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()
    
    # 2. Create Tables
    SQLModel.metadata.create_all(engine)
    
    # 3. Create 'Bouncer' Stored Procedure
    create_procedure_sql = text("""
    CREATE OR REPLACE FUNCTION match_listing_zone(lon float, lat float)
    RETURNS TABLE(tier text, contour int) AS $$
    BEGIN
        RETURN QUERY
        SELECT hz.tier::text, hz.contour 
        FROM hunter_zones hz
        WHERE ST_Contains(hz.geom, ST_SetSRID(ST_MakePoint(lon, lat), 4326))
        ORDER BY hz.contour ASC 
        LIMIT 1;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    with engine.connect() as conn:
        conn.execute(create_procedure_sql)
        conn.commit()
