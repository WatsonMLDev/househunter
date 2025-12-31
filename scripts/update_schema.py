import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db
# Import models so they are registered in SQLModel.metadata
from app import models 

if __name__ == "__main__":
    print("Updating database schema...")
    init_db()
    print("Database schema updated.")
