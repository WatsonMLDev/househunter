import pandas as pd
from typing import Optional, Dict, Any

class PropertyProcessor:
    @staticmethod
    def get_safe(val: Any, cast_type=None) -> Any:
        if pd.isna(val) or val is None:
            return None
        try:
            return cast_type(val) if cast_type else val
        except:
            return None

    @staticmethod
    def calculate_price_tier(price: float) -> Optional[str]:
        if price is None:
            return None
        if price <= 220000:
            return 'gold'
        elif price <= 250000:
            return 'silver'
        elif price <= 275000:
            return 'bronze'
        return None

    @classmethod
    def process_listing(cls, prop: pd.Series) -> Dict[str, Any]:
        """
        Extracts and cleans data from a property row (pandas Series).
        Returns a dictionary of cleaned values or None if invalid.
        """
        prop_url = prop.get('property_url')
        if not prop_url:
            return None
            
        lat = prop.get('latitude')
        lon = prop.get('longitude')
        raw_price = prop.get('list_price')
        
        if pd.isna(lat) or pd.isna(lon):
            return None

        price = cls.get_safe(raw_price, float)
        
        return {
            'prop_url': prop_url,
            'lat': float(lat),
            'lon': float(lon),
            'price': price,
            'beds': cls.get_safe(prop.get('beds'), int),
            'baths': cls.get_safe(prop.get('full_baths'), float),
            'sqft': cls.get_safe(prop.get('sqft'), int),
            'year_built': cls.get_safe(prop.get('year_built'), int),
            'status': str(prop.get('status', 'unknown')),
            'mls': str(prop.get('mls')) if not pd.isna(prop.get('mls')) else None,
            'address': prop.get('formatted_address', f"{prop.get('street', '')}, {prop.get('city', '')}, {prop.get('state', '')}"),
            'price_tier': cls.calculate_price_tier(price)
        }
