import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, text
from app.database import engine

def migrate():
    print("Migrating schema: Adding created_at to property_listings...")
    try:
        with Session(engine) as session:
            # Add column if it doesn't exist
            # We use IF NOT EXISTS logic implicitly by checking exception or just running it.
            # Postgres supports IF NOT EXISTS for ADD COLUMN in newer versions, or we can catch error.
            # Simple approach: ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...
            
            session.exec(text("ALTER TABLE property_listings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()"))
            session.commit()
            print("Migration successful.")
    except Exception as e:
        print(f"Migration failed (or column might exist): {e}")

if __name__ == "__main__":
    migrate()
