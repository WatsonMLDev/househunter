import asyncio
import json
import logging
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from typing import List
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Search URL for Charlottesville, VA with filters:
# Price < 275k, Houses, Townhomes, Condos, Multi-family, Mobile.
# URL constructed manually from Zillow search.
# "Charlottesville, VA"
# Price Max: 275,000
BASE_SEARCH_URL = "https://www.zillow.com/charlottesville-va/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22usersSearchTerm%22%3A%22Charlottesville%2C%20VA%22%2C%22mapBounds%22%3A%7B%22west%22%3A-78.605202%2C%22east%22%3A-78.361922%2C%22south%22%3A37.962076%2C%22north%22%3A38.096355%7D%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A44561%2C%22regionType%22%3A6%7D%5D%2C%22isMapVisible%22%3Atrue%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22ah%22%3A%7B%22value%22%3Atrue%7D%2C%22price%22%3A%7B%22max%22%3A275000%7D%2C%22mp%22%3A%7B%22max%22%3A275000%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Atrue%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%7D"

async def test_zillow_crawl():
    logger.info("Starting Zillow Crawl PoC...")
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        logger.info(f"Visiting: {BASE_SEARCH_URL}")
        
        # 1. Crawl Search Page
        # Zillow loads data dynamically. We might need js_code to scroll or wait.
        result = await crawler.arun(
            url=BASE_SEARCH_URL,
            bypass_cache=True,
            # magic=True, # Attempt to handle anti-bot? crawl4ai might have this.
        )
        
        if not result.success:
            logger.error(f"Failed to crawl search page: {result.error_message}")
            return

        if "Captcha" in result.markdown.raw_markdown or "Security Check" in result.markdown.raw_markdown:
            logger.warning("Likely blocked by Zillow Security/Captcha.")
        else:
            logger.info("Search successful. Found listings.")
            
            # Extract first listing URL using simple string manipulation or regex
            # Markdown link format: [address](url)
            # Find first link containing "homedetails"
            import re
            links = re.findall(r'https://www.zillow.com/homedetails/[^\)]+', result.markdown.raw_markdown)
            
            if links:
                first_url = links[0]
                logger.info(f"Navigating to first property: {first_url}")
                
                # Crawl the property page
                prop_result = await crawler.arun(
                    url=first_url,
                    bypass_cache=True,
                )
                
                if not prop_result.success:
                    logger.error("Failed to crawl property page.")
                else:
                    prop_title = prop_result.metadata.get('title', 'Unknown')
                    logger.info(f"Property Page Title: {prop_title}")
                    
                    # Save property page HTML to file for inspection
                    with open("zillow_block.html", "w") as f:
                        f.write(prop_result.html)
                    logger.info("Saved property page content to zillow_block.html")
                    
                    # Basic check for price/details
                    if "$" in prop_result.markdown.raw_markdown:
                        logger.info("Price found in property page.")
                    else:
                        logger.warning("Price NOT found in property page (might be captcha blocks on detail pages).")
            else:
                logger.warning("No property links found in search results.")

if __name__ == "__main__":
    asyncio.run(test_zillow_crawl())
