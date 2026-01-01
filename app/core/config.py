import yaml
import os
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AppConfig:
    _config: Dict[str, Any] = None
    _config_path: str = "config.yaml"

    @classmethod
    def load(cls):
        """
        Load configuration from YAML file.
        """
        try:
            # Look for config in root directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, cls._config_path)
            
            with open(config_path, 'r') as f:
                cls._config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Fallback or raise error? For now, we'll raise to fail fast
            raise e

    @classmethod
    def get_locations(cls) -> List[str]:
        if not cls._config:
            cls.load()
        return cls._config.get('locations', [])

    @classmethod
    def get_scheduler_interval(cls) -> int:
        if not cls._config:
            cls.load()
        return cls._config.get('scheduler', {}).get('interval_hours', 3)

    @classmethod
    def get_scraper_settings(cls) -> Dict[str, Any]:
        if not cls._config:
            cls.load()
        return cls._config.get('scraper', {})

    @classmethod
    def get_zone_tiers(cls) -> Dict[str, int]:
        if not cls._config:
            cls.load()
        return cls._config.get('zones', {}).get('tiers', {})

# Load on module import to ensure availability
try:
    AppConfig.load()
except Exception:
    pass # Will retry when accessing properties
