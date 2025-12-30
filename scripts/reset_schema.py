from sqlmodel import text
from app.database import engine

def reset_schema():
    print("Dropping property_listings table...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS property_listings CASCADE;"))
        conn.commit()
    print("Table dropped. init_db() in verify_scraper.py will recreate it.")

if __name__ == "__main__":
    reset_schema()
