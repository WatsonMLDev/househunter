import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, text
from app.database import engine

def clear_history():
    print("Clearing Property Change Log...")
    with Session(engine) as session:
        session.exec(text("DELETE FROM property_change_log"))
        session.commit()
    print("History table cleared. Ready for fresh tracking.")

if __name__ == "__main__":
    clear_history()
