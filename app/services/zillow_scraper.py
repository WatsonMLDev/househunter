import requests
import json
import logging
import pandas as pd
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ZillowScraper:
    BASE_URL = "https://www.zillow.com/async-create-search-page-state"
    HEADERS = {
        "authority": "www.zillow.com",
        "method": "PUT",
        "path": "/async-create-search-page-state",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-GB,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://www.zillow.com",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    }

    @staticmethod
    def scrape(location: str, price_max: int = 275000) -> pd.DataFrame:
        """
        Scrapes Zillow for properties in the given location.
        Returns a DataFrame compatible with the existing scraper logic.
        """
        logger.info(f"Directly scraping Zillow API for {location}")
        
        # Note: regionId 2608 is for Albemarle County. 
        # For a generic location, we'd need to first resolve the location to a regionId.
        # However, Zillow API often accepts "usersSearchTerm" and tries to resolve it.
        # But we must be careful. The HAR showed "regionSelection": [{"regionId": 2608}].
        # If we omit regionSelection, Zillow might rely on usersSearchTerm.
        
        payload = {
            "searchQueryState": {
                "isMapVisible": False,
                "mapBounds": {
                    "west": -124.848974, # Default bounds (US?) or arbitrary if not using map search
                    "east": -66.885444,
                    "south": 24.396308,
                    "north": 49.384358
                },
                "filterState": {
                    "sortSelection": {"value": "globalrelevanceex"},
                    "isAcceptingBackupOffersSelected": {"value": True},
                    "isPendingListingsSelected": {"value": True},
                    "price": {"min": 0, "max": price_max},
                    "monthlyPayment": {"min": 0, "max": price_max // 200}, # Rough estimate
                    "isLotLand": {"value": False},
                    "isApartment": {"value": False}
                },
                "isListVisible": True,
                "mapZoom": 6,
                "usersSearchTerm": location,
                # "regionSelection": [{"regionId": 2608}] # Omitted to let Zillow resolve term
            },
            "wants": {
                "cat1": ["listResults"],
                "cat2": ["total"],
                "abTrials": ["total"]
            },
            "requestId": 1,
            "isDebugRequest": False
        }

        try:
            response = requests.put(ZillowScraper.BASE_URL, headers=ZillowScraper.HEADERS, json=payload)
            response.raise_for_status()
            data = response.json()
            
            list_results = data.get('cat1', {}).get('searchResults', {}).get('listResults', [])
            logger.info(f"Found {len(list_results)} properties via direct API.")
            
            listings = []
            for item in list_results:
                hdp = item.get('hdpData', {}).get('homeInfo', {})
                address = item.get('address')
                price = item.get('unformattedPrice')
                zpid = item.get('zpid')
                
                listing = {
                    'property_url': f"https://www.zillow.com/homedetails/{zpid}_zpid/" if zpid else None,
                    'mls': None, # content not always available
                    'formatted_address': address,
                    'address': item.get('addressStreet'),
                    'city': item.get('addressCity'),
                    'state': item.get('addressState'),
                    'zip': item.get('addressZipcode'),
                    'list_price': price,
                    'latitude': hdp.get('latitude'),
                    'longitude': hdp.get('longitude'),
                    'beds': hdp.get('bedrooms'),
                    'full_baths': hdp.get('bathrooms'),
                    'sqft': hdp.get('livingArea'),
                    'year_built': None, # Not in search results usually
                    'status': item.get('statusText'),
                    'site_name': 'zillow'
                }
                listings.append(listing)
                
            return pd.DataFrame(listings)

        except Exception as e:
            logger.error(f"Zillow direct scrape failed: {e}")
            return pd.DataFrame()
