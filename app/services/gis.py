from sqlmodel import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class GISService:
    @staticmethod
    def lookup_zone(session: Session, lat: float, lon: float):
        """
        Calls the stored procedure `match_listing_zone` to find the tier and contour.
        Returns (tier, contour) tuple or (None, None).
        """
        try:
            statement = text("SELECT tier, contour FROM match_listing_zone(:lon, :lat)")
            gis_result = session.exec(statement, params={"lon": lon, "lat": lat}).first()
            if gis_result:
                return gis_result.tier, gis_result.contour
        except Exception as e:
            logger.error(f"GIS Lookup failed for lat={lat}, lon={lon}: {e}")
        
        return None, None
