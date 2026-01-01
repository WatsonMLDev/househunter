import requests
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class ZillowRegionResolver:
    URL = "https://www.zillow.com/zg-graph"
    HEADERS = {
        "authority": "www.zillow.com",
        "method": "POST",
        "path": "/zg-graph",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://www.zillow.com",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    }
    
    QUERY = """
    query GetQueryUnderstandingResults($query: String!, $queryOptions: SearchAssistanceQueryOptions, $querySource: SearchAssistanceQuerySource = UNKNOWN, $resultType: [SearchAssistanceResultType], $shouldRequestSpellCorrectedMetadata: Boolean = false) {
      searchAssistanceResult: zgsQueryUnderstandingRequest(
        query: $query
        queryOptions: $queryOptions
        querySource: $querySource
        resultType: $resultType
      ) {
        requestId
        results {
          ...SearchAssistanceResultFields
          ...RegionResultFields
          ...SemanticResultFields
          ...RentalCommunityResultFields
          ...SchoolResultFields
          ...AddressResultFields
        }
      }
    }

    fragment SearchAssistanceResultFields on SearchAssistanceResult {
      __typename
      id
      spellCorrectedMetadata @include(if: $shouldRequestSpellCorrectedMetadata) {
        ...SpellCorrectedFields
      }
    }

    fragment SpellCorrectedFields on SpellCorrectedMetadata {
      isSpellCorrected
      spellCorrectedQuery
      userQuery
    }

    fragment RegionResultFields on SearchAssistanceRegionResult {
      regionId
      subType
      state
      county
      city
    }

    fragment SemanticResultFields on SearchAssistanceSemanticResult {
      nearMe
      regionIds
      regionTypes
      regionDisplayIds
      queryResolutionStatus
      schoolDistrictIds
      schoolIds
      viewLatitudeDelta
      filters {
        basementStatusType
        baths {
          min
          max
        }
        beds {
          min
          max
        }
        excludeTypes
        hoaFeesPerMonth {
          min
          max
        }
        homeType
        keywords
        listingStatusType
        livingAreaSqft {
          min
          max
        }
        lotSizeSqft {
          min
          max
        }
        parkingSpots {
          min
          max
        }
        price {
          min
          max
        }
        searchRentalFilters {
          monthlyPayment {
            min
            max
          }
          petsAllowed
          rentalAvailabilityDate {
            min
            max
          }
        }
        searchSaleFilters {
          daysOnZillow {
            min
            max
          }
        }
        showOnlyType
        view
        yearBuilt {
          min
          max
        }
      }
    }

    fragment RentalCommunityResultFields on SearchAssistanceRentalCommunityResult {
      location {
        latitude
        longitude
      }
    }

    fragment SchoolResultFields on SearchAssistanceSchoolResult {
      id
      schoolDistrictId
      schoolId
    }

    fragment AddressResultFields on SearchAssistanceAddressResult {
      zpid
      addressSubType: subType
      location {
        latitude
        longitude
      }
    }
    """

    @classmethod
    def resolve(cls, location: str) -> Optional[Dict[str, Any]]:
        """
        Resolves a locaion string to Zillow region info.
        Returns a dict with regionId, regionType, etc. or None.
        """
        payload = {
            "operationName": "GetQueryUnderstandingResults",
            "variables": {
                "query": location,
                "queryOptions": {
                    "maxResults": 5,
                    "userSearchContext": "FOR_SALE",
                    "spellCheck": True,
                    "userIdentity": {"abKey": "65124e2d-cd1c-4069-b86b-4eb471047b63"}
                },
                "querySource": "MANUAL",
                "resultType": ["REGIONS", "FORSALE", "RENTALS", "SOLD", "COMMUNITIES", "SCHOOLS", "SCHOOL_DISTRICTS", "SEMANTIC_REGIONS"]
            },
            "query": cls.QUERY
        }

        # Add query params to URL as seen in HAR
        params = {
            "query": location,
            "operationName": "GetQueryUnderstandingResults",
            "querySource": "MANUAL"
        }

        try:
            response = requests.post(cls.URL, headers=cls.HEADERS, json=payload, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('data', {}).get('searchAssistanceResult', {}).get('results', [])
            if results:
                # Prioritize region results
                for res in results:
                    if res.get('__typename') == 'SearchAssistanceRegionResult':
                        logger.info(f"Resolved '{location}' to Region: {res.get('id')} (ID: {res.get('regionId')})")
                        return {
                            "regionId": res.get("regionId"),
                            "regionType": cls._map_subtype_to_type(res.get("subType")),
                            "displayName": res.get("id")
                        }
            
            logger.warning(f"Could not resolve location '{location}' to a specific Zillow region.")
            return None

        except Exception as e:
            logger.error(f"Zillow region resolution failed: {e}")
            if 'response' in locals():
                logger.error(f"Response: {response.text}")
            return None

    @staticmethod
    def _map_subtype_to_type(subtype: str) -> int:
        # Map subType string to regionType integer used in search API
        # This mapping might need expansion based on more HAR data
        mapping = {
            "CITY": 6,
            "COUNTY": 4,
            "STATE": 2,
            "ZIP": 7,
            "NEIGHBORHOOD": 8 # Guessing, check HAR if possible
        }
        return mapping.get(subtype, 6) # Default to city? or maybe generic
