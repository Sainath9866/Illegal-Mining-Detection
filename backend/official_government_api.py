"""
Official Indian Government Mining Data API Integration
Fetches live data from official government sources:
- IBM (Indian Bureau of Mines)
- Mines.gov.in
- Data.gov.in
- State Mining Departments
"""

import requests
import json
import logging
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# Try to import aiohttp, but make it optional
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logging.warning("aiohttp not available. Using synchronous requests.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OfficialGovernmentAPI:
    """Fetches live mining data from official Indian government sources"""
    
    def __init__(self):
        """Initialize government API client"""
        self.base_urls = {
            'ibm': 'https://ibm.gov.in',
            'mines_gov': 'https://mines.gov.in',
            'data_gov': 'https://api.data.gov.in',
            'geoserver': 'https://geoserver.mines.gov.in/geoserver'
        }
        
        # API endpoints for different data sources
        self.endpoints = {
            'mining_leases': '/api/mineral-concessions',
            'production_data': '/api/production-statistics',
            'lease_boundaries': '/geoserver/wms',
            'state_data': '/api/state-mining-data',
            'environmental_clearances': '/api/environmental-clearances'
        }
        
        self.session = None
        logger.info("Official Government API initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_ibm_mining_leases(self) -> Dict[str, Any]:
        """
        Fetch mining lease data from Indian Bureau of Mines
        
        Returns:
            Dict: IBM mining lease data
        """
        try:
            # IBM API endpoint for mineral concessions
            url = f"{self.base_urls['ibm']}{self.endpoints['mining_leases']}"
            
            params = {
                'format': 'json',
                'limit': 1000,
                'offset': 0,
                'state': 'all',
                'mineral': 'all',
                'status': 'active'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched {len(data.get('data', []))} leases from IBM")
                    return self._process_ibm_data(data)
                else:
                    logger.warning(f"IBM API returned status {response.status}")
                    return await self._fetch_fallback_data()
                    
        except Exception as e:
            logger.error(f"Error fetching IBM data: {e}")
            return await self._fetch_fallback_data()
    
    async def fetch_mines_gov_boundaries(self) -> Dict[str, Any]:
        """
        Fetch mining lease boundaries from Mines.gov.in WMS service
        
        Returns:
            Dict: Mining lease boundaries as GeoJSON
        """
        try:
            # WMS GetFeatureInfo request for mining lease boundaries
            wms_url = f"{self.base_urls['geoserver']}/wms"
            
            params = {
                'service': 'WMS',
                'version': '1.3.0',
                'request': 'GetFeatureInfo',
                'layers': 'mining:lease_boundaries',
                'crs': 'EPSG:4326',
                'bbox': '68.0,6.0,97.0,37.0',  # India bounding box
                'width': 1024,
                'height': 1024,
                'x': 512,
                'y': 512,
                'info_format': 'application/json'
            }
            
            async with self.session.get(wms_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched mining boundaries from WMS")
                    return self._process_wms_data(data)
                else:
                    logger.warning(f"WMS returned status {response.status}")
                    return await self._fetch_fallback_boundaries()
                    
        except Exception as e:
            logger.error(f"Error fetching WMS boundaries: {e}")
            return await self._fetch_fallback_boundaries()
    
    async def fetch_data_gov_mining_stats(self) -> Dict[str, Any]:
        """
        Fetch mining statistics from Data.gov.in
        
        Returns:
            Dict: Mining statistics data
        """
        try:
            # Data.gov.in API for mining statistics
            url = f"{self.base_urls['data_gov']}/rest/3/action/datastore_search"
            
            params = {
                'resource_id': 'mining-production-statistics',
                'limit': 1000,
                'filters': json.dumps({
                    'year': '2024',
                    'state': 'all'
                })
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Fetched mining statistics from Data.gov.in")
                    return self._process_data_gov_stats(data)
                else:
                    logger.warning(f"Data.gov.in returned status {response.status}")
                    return await self._fetch_fallback_stats()
                    
        except Exception as e:
            logger.error(f"Error fetching Data.gov.in stats: {e}")
            return await self._fetch_fallback_stats()
    
    async def fetch_state_mining_departments(self) -> Dict[str, Any]:
        """
        Fetch data from state mining departments
        
        Returns:
            Dict: State-specific mining data
        """
        try:
            state_apis = {
                'karnataka': 'https://karnataka.gov.in/api/mining',
                'odisha': 'https://odisha.gov.in/api/mining',
                'chhattisgarh': 'https://chhattisgarh.gov.in/api/mining',
                'rajasthan': 'https://rajasthan.gov.in/api/mining',
                'andhra_pradesh': 'https://ap.gov.in/api/mining'
            }
            
            all_state_data = {}
            
            for state, api_url in state_apis.items():
                try:
                    async with self.session.get(api_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            all_state_data[state] = self._process_state_data(data, state)
                            logger.info(f"Fetched data for {state}")
                        else:
                            logger.warning(f"State API {state} returned status {response.status}")
                except Exception as e:
                    logger.warning(f"Error fetching data for {state}: {e}")
                    continue
            
            return all_state_data
            
        except Exception as e:
            logger.error(f"Error fetching state data: {e}")
            return {}
    
    def _process_ibm_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process IBM API response data"""
        processed_data = {
            'source': 'IBM',
            'timestamp': datetime.now().isoformat(),
            'leases': [],
            'statistics': {}
        }
        
        if 'data' in data:
            for lease in data['data']:
                processed_lease = {
                    'lease_id': lease.get('concession_id', ''),
                    'lease_name': lease.get('concession_name', ''),
                    'state': lease.get('state', ''),
                    'district': lease.get('district', ''),
                    'mineral': lease.get('mineral', ''),
                    'area_hectares': float(lease.get('area_hectares', 0)),
                    'lease_type': lease.get('lease_type', ''),
                    'valid_from': lease.get('valid_from', ''),
                    'valid_to': lease.get('valid_to', ''),
                    'status': lease.get('status', ''),
                    'geometry': self._extract_geometry(lease)
                }
                processed_data['leases'].append(processed_lease)
        
        return processed_data
    
    def _process_wms_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process WMS response data"""
        geojson = {
            'type': 'FeatureCollection',
            'features': []
        }
        
        if 'features' in data:
            for feature in data['features']:
                geojson['features'].append({
                    'type': 'Feature',
                    'properties': feature.get('properties', {}),
                    'geometry': feature.get('geometry', {})
                })
        
        return geojson
    
    def _process_data_gov_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Data.gov.in statistics"""
        stats = {
            'source': 'Data.gov.in',
            'timestamp': datetime.now().isoformat(),
            'production': {},
            'states': {}
        }
        
        if 'result' in data and 'records' in data['result']:
            for record in data['result']['records']:
                state = record.get('state', 'Unknown')
                mineral = record.get('mineral', 'Unknown')
                
                if state not in stats['states']:
                    stats['states'][state] = {}
                
                stats['states'][state][mineral] = {
                    'quantity': float(record.get('quantity', 0)),
                    'value': float(record.get('value', 0)),
                    'unit': record.get('unit', 'tonnes')
                }
        
        return stats
    
    def _process_state_data(self, data: Dict[str, Any], state: str) -> Dict[str, Any]:
        """Process state-specific data"""
        return {
            'state': state,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
    
    def _extract_geometry(self, lease: Dict[str, Any]) -> Dict[str, Any]:
        """Extract geometry from lease data"""
        # Try to extract coordinates from various possible fields
        coords = lease.get('coordinates') or lease.get('geometry') or lease.get('boundary')
        
        if coords:
            return {
                'type': 'Polygon',
                'coordinates': coords
            }
        else:
            # Generate approximate coordinates based on state
            return self._generate_approximate_coordinates(lease.get('state', ''))
    
    def _generate_approximate_coordinates(self, state: str) -> Dict[str, Any]:
        """Generate approximate coordinates for a state"""
        state_coords = {
            'Karnataka': (15.3173, 75.7139),
            'Odisha': (20.9517, 85.0985),
            'Chhattisgarh': (21.2787, 81.8661),
            'Rajasthan': (27.0238, 74.2179),
            'Andhra Pradesh': (15.9129, 79.7400),
            'Madhya Pradesh': (22.9734, 78.6569),
            'Maharashtra': (19.7515, 75.7139),
            'Gujarat': (23.0225, 72.5714),
            'Jharkhand': (23.6102, 85.2799),
            'Tamil Nadu': (11.1271, 78.6569),
            'Telangana': (18.1124, 79.0193)
        }
        
        lat, lon = state_coords.get(state, (20.0, 77.0))
        
        # Generate a small polygon around the state center
        offset = 0.01
        return {
            'type': 'Polygon',
            'coordinates': [[
                [lon - offset, lat - offset],
                [lon + offset, lat - offset],
                [lon + offset, lat + offset],
                [lon - offset, lat + offset],
                [lon - offset, lat - offset]
            ]]
        }
    
    async def _fetch_fallback_data(self) -> Dict[str, Any]:
        """Fallback data when APIs are unavailable"""
        logger.info("Using fallback data for IBM")
        return {
            'source': 'Fallback',
            'timestamp': datetime.now().isoformat(),
            'leases': [],
            'statistics': {}
        }
    
    async def _fetch_fallback_boundaries(self) -> Dict[str, Any]:
        """Fallback boundaries when WMS is unavailable"""
        logger.info("Using fallback boundaries")
        return {
            'type': 'FeatureCollection',
            'features': []
        }
    
    async def _fetch_fallback_stats(self) -> Dict[str, Any]:
        """Fallback statistics when Data.gov.in is unavailable"""
        logger.info("Using fallback statistics")
        return {
            'source': 'Fallback',
            'timestamp': datetime.now().isoformat(),
            'production': {},
            'states': {}
        }
    
    async def fetch_all_government_data(self) -> Dict[str, Any]:
        """
        Fetch all available government data sources
        
        Returns:
            Dict: Combined government data
        """
        logger.info("Fetching all government data sources...")
        
        async with self:
            # Fetch data from all sources concurrently
            ibm_data, boundaries, stats, state_data = await asyncio.gather(
                self.fetch_ibm_mining_leases(),
                self.fetch_mines_gov_boundaries(),
                self.fetch_data_gov_mining_stats(),
                self.fetch_state_mining_departments(),
                return_exceptions=True
            )
            
            # Combine all data
            combined_data = {
                'timestamp': datetime.now().isoformat(),
                'sources': {
                    'ibm': ibm_data if not isinstance(ibm_data, Exception) else {},
                    'boundaries': boundaries if not isinstance(boundaries, Exception) else {},
                    'statistics': stats if not isinstance(stats, Exception) else {},
                    'state_data': state_data if not isinstance(state_data, Exception) else {}
                },
                'summary': {
                    'total_leases': len(ibm_data.get('leases', [])) if not isinstance(ibm_data, Exception) else 0,
                    'total_boundaries': len(boundaries.get('features', [])) if not isinstance(boundaries, Exception) else 0,
                    'states_covered': len(state_data) if not isinstance(state_data, Exception) else 0
                }
            }
            
            logger.info(f"Fetched data from {combined_data['summary']['states_covered']} sources")
            return combined_data

# Standalone function for easy integration
async def get_live_government_data() -> Dict[str, Any]:
    """Get live government data"""
    async with OfficialGovernmentAPI() as api:
        return await api.fetch_all_government_data()

if __name__ == "__main__":
    # Test the government API
    async def main():
        api = OfficialGovernmentAPI()
        data = await api.fetch_all_government_data()
        print(f"Fetched data from {len(data['sources'])} sources")
        print(f"Total leases: {data['summary']['total_leases']}")
    
    asyncio.run(main())
