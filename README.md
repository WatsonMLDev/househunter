# HouseHunter Backend

HouseHunter is a powerful geospatial real-estate intelligence engine designed to aggregate, analyze, and serve property data. It scrapes listings from various sources (via HomeHarvest), enriches them with GIS data (isochrones), and serves them via a FastAPI backend.

## 🚀 Features

- **Automated Scraping:** Scheduled jobs (APScheduler) to scrape listings from Zillow, Realtor.com, etc.
- **Geospatial Analysis:** PostGIS-powered zoning and isochrone analysis to grade properties (Gold/Silver/Bronze tiers) based on commute times.
- **REST API:** FastAPI endpoints for property retrieval, history tracking, and filtering.
- **Data Persistence:** Postgres + PostGIS database with robust data models using SQLModel.
- **History Tracking:** Tracks price and status changes over time.

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Database:** PostgreSQL + PostGIS extension
- **ORM:** SQLModel (SQLAlchemy + Pydantic)
- **Scraping:** HomeHarvest
- **Scheduler:** APScheduler

## 🔧 Installation

### Prerequisites
- Python 3.10 or higher
- PostgreSQL with PostGIS extension enabled
- `uv` or `pip` for package management

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/WatsonMLDev/househunter.git
    cd househunter
    ```

2.  **Create Virtual Environment:**
    ```bash
    pyenv virtualenv 3.10.12 househunter
    pyenv activate househunter
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables:**
    Create a `.env` file in the root directory:
    ```env
    DATABASE_URL=postgresql://user:password@localhost:5432/househunter
    ```

5.  **Initialize Database:**
    The application will automatically initialize tables on startup, but you may need to ensure PostGIS is enabled on your DB.

## 🏃 Usage

### Running the Server
Start the development server with auto-reload:
```bash
python main.py
```
Or directly via uvicorn:
```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.
Docs: `http://localhost:8000/docs`

### Running Scrapers
The scraper runs on a schedule, but you can trigger it manually or via scripts in the `scripts/` folder.

## 📂 Project Structure

- `app/`: Main application code
  - `api/`: API endpoints (`properties.py`, `zones.py`)
  - `core/`: Config and Database models (`models.py`, `database.py`)
  - `services/`: Business logic (`scraper.py`, `gis.py`, `storage.py`)
- `scripts/`: Utility scripts for maintenance and manual tasks