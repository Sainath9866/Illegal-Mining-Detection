"""
Mining Boundaries Module
Fetches and processes legal mining lease boundaries for India
"""

import os
import json
import requests
import geopandas as gpd
import pandas as pd
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MiningBoundaries:
    """Handles fetching and processing of legal mining boundaries"""
    
    def __init__(self, data_dir: str = "data/mining_boundaries"):
        """
        Initialize mining boundaries handler
        
        Args:
            data_dir: Directory to store boundary data
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Mining boundaries initialized with data directory: {data_dir}")
    
    def fetch_india_mining_leases(self, state: Optional[str] = None) -> gpd.GeoDataFrame:
        """
        Fetch mining lease data from official sources
        
        Args:
            state: Specific state to fetch data for (optional)
            
        Returns:
            gpd.GeoDataFrame: Mining lease boundaries
        """
        try:
            # This would typically fetch from official APIs
            # For demo purposes, we'll create sample data
            
            sample_leases = self._create_sample_mining_leases()
            
            # Convert to GeoDataFrame
            gdf = gpd.GeoDataFrame(sample_leases, crs='EPSG:4326')
            
            logger.info(f"Fetched {len(gdf)} mining leases")
            return gdf
            
        except Exception as e:
            logger.error(f"Error fetching mining leases: {e}")
            raise
    
    def _create_sample_mining_leases(self) -> List[Dict[str, Any]]:
        """
        Create sample mining lease data for demonstration
        
        Returns:
            List[Dict]: Sample mining lease data
        """
        from shapely.geometry import Polygon
        
        # Sample mining leases in different states of India
        sample_leases = [
            {
                'lease_id': 'ML001',
                'lease_name': 'Iron Ore Mine - Bellary',
                'state': 'Karnataka',
                'district': 'Bellary',
                'mineral': 'Iron Ore',
                'area_hectares': 150.5,
                'lease_type': 'Mining Lease',
                'valid_from': '2020-01-01',
                'valid_to': '2030-12-31',
                'geometry': Polygon([
                    [76.0, 15.0],
                    [76.1, 15.0],
                    [76.1, 15.1],
                    [76.0, 15.1],
                    [76.0, 15.0]
                ])
            },
            {
                'lease_id': 'ML002',
                'lease_name': 'Coal Mine - Singrauli',
                'state': 'Madhya Pradesh',
                'district': 'Singrauli',
                'mineral': 'Coal',
                'area_hectares': 200.0,
                'lease_type': 'Mining Lease',
                'valid_from': '2019-06-01',
                'valid_to': '2029-05-31',
                'geometry': Polygon([
                    [82.5, 24.0],
                    [82.6, 24.0],
                    [82.6, 24.1],
                    [82.5, 24.1],
                    [82.5, 24.0]
                ])
            },
            {
                'lease_id': 'ML003',
                'lease_name': 'Limestone Mine - Jodhpur',
                'state': 'Rajasthan',
                'district': 'Jodhpur',
                'mineral': 'Limestone',
                'area_hectares': 75.2,
                'lease_type': 'Mining Lease',
                'valid_from': '2021-03-01',
                'valid_to': '2031-02-28',
                'geometry': Polygon([
                    [73.0, 26.0],
                    [73.1, 26.0],
                    [73.1, 26.1],
                    [73.0, 26.1],
                    [73.0, 26.0]
                ])
            },
            {
                'lease_id': 'ML004',
                'lease_name': 'Bauxite Mine - Koraput',
                'state': 'Odisha',
                'district': 'Koraput',
                'mineral': 'Bauxite',
                'area_hectares': 120.8,
                'lease_type': 'Mining Lease',
                'valid_from': '2020-08-01',
                'valid_to': '2030-07-31',
                'geometry': Polygon([
                    [82.0, 18.5],
                    [82.1, 18.5],
                    [82.1, 18.6],
                    [82.0, 18.6],
                    [82.0, 18.5]
                ])
            },
            {
                'lease_id': 'ML005',
                'lease_name': 'Copper Mine - Khetri',
                'state': 'Rajasthan',
                'district': 'Jhunjhunu',
                'mineral': 'Copper',
                'area_hectares': 95.3,
                'lease_type': 'Mining Lease',
                'valid_from': '2018-01-01',
                'valid_to': '2028-12-31',
                'geometry': Polygon([
                    [75.5, 28.0],
                    [75.6, 28.0],
                    [75.6, 28.1],
                    [75.5, 28.1],
                    [75.5, 28.0]
                ])
            }
        ]
        
        return sample_leases
    
    def save_boundaries(self, gdf: gpd.GeoDataFrame, filename: str) -> str:
        """
        Save mining boundaries to file
        
        Args:
            gdf: GeoDataFrame with boundaries
            filename: Output filename
            
        Returns:
            str: Path to saved file
        """
        try:
            filepath = os.path.join(self.data_dir, filename)
            gdf.to_file(filepath, driver='GeoJSON')
            
            logger.info(f"Mining boundaries saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving boundaries: {e}")
            raise
    
    def load_boundaries(self, filepath: str) -> gpd.GeoDataFrame:
        """
        Load mining boundaries from file
        
        Args:
            filepath: Path to boundary file
            
        Returns:
            gpd.GeoDataFrame: Loaded boundaries
        """
        try:
            gdf = gpd.read_file(filepath)
            logger.info(f"Loaded {len(gdf)} mining boundaries from {filepath}")
            return gdf
            
        except Exception as e:
            logger.error(f"Error loading boundaries: {e}")
            raise
    
    def get_boundaries_by_state(self, state: str) -> gpd.GeoDataFrame:
        """
        Get mining boundaries for a specific state
        
        Args:
            state: State name
            
        Returns:
            gpd.GeoDataFrame: Filtered boundaries
        """
        try:
            # Load all boundaries
            all_boundaries = self.fetch_india_mining_leases()
            
            # Filter by state
            state_boundaries = all_boundaries[all_boundaries['state'] == state]
            
            logger.info(f"Found {len(state_boundaries)} mining leases in {state}")
            return state_boundaries
            
        except Exception as e:
            logger.error(f"Error getting boundaries by state: {e}")
            raise
    
    def get_boundaries_by_mineral(self, mineral: str) -> gpd.GeoDataFrame:
        """
        Get mining boundaries for a specific mineral
        
        Args:
            mineral: Mineral type
            
        Returns:
            gpd.GeoDataFrame: Filtered boundaries
        """
        try:
            # Load all boundaries
            all_boundaries = self.fetch_india_mining_leases()
            
            # Filter by mineral
            mineral_boundaries = all_boundaries[all_boundaries['mineral'] == mineral]
            
            logger.info(f"Found {len(mineral_boundaries)} {mineral} mining leases")
            return mineral_boundaries
            
        except Exception as e:
            logger.error(f"Error getting boundaries by mineral: {e}")
            raise
    
    def create_boundary_summary(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Create summary statistics for mining boundaries
        
        Args:
            gdf: GeoDataFrame with boundaries
            
        Returns:
            Dict: Summary statistics
        """
        try:
            summary = {
                'total_leases': len(gdf),
                'total_area_hectares': gdf['area_hectares'].sum(),
                'states': gdf['state'].unique().tolist(),
                'minerals': gdf['mineral'].unique().tolist(),
                'lease_types': gdf['lease_type'].unique().tolist(),
                'area_by_state': gdf.groupby('state')['area_hectares'].sum().to_dict(),
                'area_by_mineral': gdf.groupby('mineral')['area_hectares'].sum().to_dict()
            }
            
            logger.info(f"Created boundary summary: {summary['total_leases']} leases, {summary['total_area_hectares']:.1f} ha")
            return summary
            
        except Exception as e:
            logger.error(f"Error creating boundary summary: {e}")
            raise

def main():
    """Example usage of MiningBoundaries class"""
    
    # Initialize mining boundaries
    boundaries = MiningBoundaries()
    
    # Fetch sample data
    leases = boundaries.fetch_india_mining_leases()
    
    # Save to file
    filepath = boundaries.save_boundaries(leases, "india_mining_leases.geojson")
    
    # Create summary
    summary = boundaries.create_boundary_summary(leases)
    print("Mining Boundaries Summary:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
