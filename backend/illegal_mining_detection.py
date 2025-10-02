"""
Illegal Mining Detection Module
Compares detected mining areas with legal boundaries to identify illegal mining
"""

import geopandas as gpd
import numpy as np
import logging
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from typing import Dict, Any, List, Tuple, Optional
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IllegalMiningDetection:
    """Handles detection of illegal mining activities by comparing with legal boundaries"""
    
    def __init__(self):
        """Initialize illegal mining detection"""
        logger.info("Illegal mining detection initialized")
    
    def load_mining_boundaries(self, boundary_path: str) -> gpd.GeoDataFrame:
        """
        Load mining lease boundaries from shapefile
        
        Args:
            boundary_path: Path to mining boundary shapefile
            
        Returns:
            gpd.GeoDataFrame: Mining boundaries
        """
        try:
            boundaries = gpd.read_file(boundary_path)
            
            # Ensure CRS is set
            if boundaries.crs is None:
                boundaries.set_crs('EPSG:4326', inplace=True)
            
            # Reproject to WGS84 if needed
            if boundaries.crs != 'EPSG:4326':
                boundaries = boundaries.to_crs('EPSG:4326')
            
            logger.info(f"Loaded {len(boundaries)} mining boundaries")
            return boundaries
            
        except Exception as e:
            logger.error(f"Error loading mining boundaries: {e}")
            raise
    
    def load_detected_mining_areas(self, mining_polygons_path: str) -> gpd.GeoDataFrame:
        """
        Load detected mining areas from shapefile
        
        Args:
            mining_polygons_path: Path to detected mining polygons shapefile
            
        Returns:
            gpd.GeoDataFrame: Detected mining areas
        """
        try:
            mining_areas = gpd.read_file(mining_polygons_path)
            
            # Ensure CRS is set
            if mining_areas.crs is None:
                mining_areas.set_crs('EPSG:4326', inplace=True)
            
            # Reproject to WGS84 if needed
            if mining_areas.crs != 'EPSG:4326':
                mining_areas = mining_areas.to_crs('EPSG:4326')
            
            logger.info(f"Loaded {len(mining_areas)} detected mining areas")
            return mining_areas
            
        except Exception as e:
            logger.error(f"Error loading detected mining areas: {e}")
            raise
    
    def identify_legal_mining(self, 
                             mining_areas: gpd.GeoDataFrame, 
                             boundaries: gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """
        Identify legal vs illegal mining areas
        
        Args:
            mining_areas: Detected mining areas
            boundaries: Legal mining boundaries
            
        Returns:
            Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]: Legal and illegal mining areas
        """
        try:
            # Ensure both GeoDataFrames have the same CRS
            if mining_areas.crs != boundaries.crs:
                mining_areas = mining_areas.to_crs(boundaries.crs)
            
            # Create a union of all legal boundaries
            legal_boundary = unary_union(boundaries.geometry)
            
            # Initialize lists for legal and illegal areas
            legal_areas = []
            illegal_areas = []
            
            for idx, mining_area in mining_areas.iterrows():
                # Check if mining area intersects with legal boundary
                if mining_area.geometry.intersects(legal_boundary):
                    # Check if it's completely within legal boundary
                    if mining_area.geometry.within(legal_boundary):
                        legal_areas.append(mining_area)
                    else:
                        # Partially within - split into legal and illegal parts
                        legal_part = mining_area.geometry.intersection(legal_boundary)
                        illegal_part = mining_area.geometry.difference(legal_boundary)
                        
                        if legal_part.area > 0:
                            legal_row = mining_area.copy()
                            legal_row.geometry = legal_part
                            legal_areas.append(legal_row)
                        
                        if illegal_part.area > 0:
                            illegal_row = mining_area.copy()
                            illegal_row.geometry = illegal_part
                            illegal_areas.append(illegal_row)
                else:
                    # Completely outside legal boundary
                    illegal_areas.append(mining_area)
            
            # Create GeoDataFrames
            legal_gdf = gpd.GeoDataFrame(legal_areas, crs=mining_areas.crs) if legal_areas else gpd.GeoDataFrame(columns=mining_areas.columns, crs=mining_areas.crs)
            illegal_gdf = gpd.GeoDataFrame(illegal_areas, crs=mining_areas.crs) if illegal_areas else gpd.GeoDataFrame(columns=mining_areas.columns, crs=mining_areas.crs)
            
            # Recalculate areas for split polygons
            if not legal_gdf.empty:
                legal_gdf['area_m2'] = legal_gdf.geometry.area
                legal_gdf['area_ha'] = legal_gdf['area_m2'] / 10000
            
            if not illegal_gdf.empty:
                illegal_gdf['area_m2'] = illegal_gdf.geometry.area
                illegal_gdf['area_ha'] = illegal_gdf['area_m2'] / 10000
            
            logger.info(f"Identified {len(legal_gdf)} legal mining areas")
            logger.info(f"Identified {len(illegal_gdf)} illegal mining areas")
            
            return legal_gdf, illegal_gdf
            
        except Exception as e:
            logger.error(f"Error identifying legal/illegal mining: {e}")
            raise
    
    def calculate_illegal_mining_stats(self, 
                                      legal_areas: gpd.GeoDataFrame, 
                                      illegal_areas: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Calculate statistics for illegal mining detection
        
        Args:
            legal_areas: Legal mining areas
            illegal_areas: Illegal mining areas
            
        Returns:
            Dict[str, Any]: Statistics
        """
        try:
            # Calculate areas
            legal_area_ha = legal_areas['area_ha'].sum() if not legal_areas.empty else 0
            illegal_area_ha = illegal_areas['area_ha'].sum() if not illegal_areas.empty else 0
            total_mining_area_ha = legal_area_ha + illegal_area_ha
            
            # Calculate percentages
            legal_percentage = (legal_area_ha / total_mining_area_ha * 100) if total_mining_area_ha > 0 else 0
            illegal_percentage = (illegal_area_ha / total_mining_area_ha * 100) if total_mining_area_ha > 0 else 0
            
            # Count areas
            legal_count = len(legal_areas)
            illegal_count = len(illegal_areas)
            
            stats = {
                'legal_mining': {
                    'count': legal_count,
                    'area_ha': float(legal_area_ha),
                    'percentage': float(legal_percentage)
                },
                'illegal_mining': {
                    'count': illegal_count,
                    'area_ha': float(illegal_area_ha),
                    'percentage': float(illegal_percentage)
                },
                'total_mining': {
                    'count': legal_count + illegal_count,
                    'area_ha': float(total_mining_area_ha),
                    'percentage': 100.0
                }
            }
            
            logger.info(f"Illegal mining statistics:")
            logger.info(f"- Legal mining: {legal_count} areas, {legal_area_ha:.2f} ha ({legal_percentage:.1f}%)")
            logger.info(f"- Illegal mining: {illegal_count} areas, {illegal_area_ha:.2f} ha ({illegal_percentage:.1f}%)")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating illegal mining stats: {e}")
            raise
    
    def save_results(self, 
                    legal_areas: gpd.GeoDataFrame, 
                    illegal_areas: gpd.GeoDataFrame, 
                    output_dir: str) -> Dict[str, str]:
        """
        Save legal and illegal mining areas to shapefiles
        
        Args:
            legal_areas: Legal mining areas
            illegal_areas: Illegal mining areas
            output_dir: Output directory
            
        Returns:
            Dict[str, str]: Paths to saved files
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            output_paths = {}
            
            # Save legal mining areas
            if not legal_areas.empty:
                legal_path = os.path.join(output_dir, "legal_mining_areas.shp")
                legal_areas.to_file(legal_path)
                output_paths['legal_areas'] = legal_path
                logger.info(f"Legal mining areas saved to: {legal_path}")
            
            # Save illegal mining areas
            if not illegal_areas.empty:
                illegal_path = os.path.join(output_dir, "illegal_mining_areas.shp")
                illegal_areas.to_file(illegal_path)
                output_paths['illegal_areas'] = illegal_path
                logger.info(f"Illegal mining areas saved to: {illegal_path}")
            
            return output_paths
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise
    
    def detect_illegal_mining(self, 
                             mining_polygons_path: str, 
                             boundary_path: str, 
                             output_dir: str) -> Dict[str, Any]:
        """
        Main function to detect illegal mining activities
        
        Args:
            mining_polygons_path: Path to detected mining polygons
            boundary_path: Path to legal mining boundaries
            output_dir: Output directory for results
            
        Returns:
            Dict[str, Any]: Complete detection results
        """
        try:
            # Load data
            mining_areas = self.load_detected_mining_areas(mining_polygons_path)
            boundaries = self.load_mining_boundaries(boundary_path)
            
            # Identify legal vs illegal mining
            legal_areas, illegal_areas = self.identify_legal_mining(mining_areas, boundaries)
            
            # Calculate statistics
            stats = self.calculate_illegal_mining_stats(legal_areas, illegal_areas)
            
            # Save results
            output_paths = self.save_results(legal_areas, illegal_areas, output_dir)
            
            # Combine results
            results = {
                'statistics': stats,
                'output_paths': output_paths,
                'legal_areas_gdf': legal_areas,
                'illegal_areas_gdf': illegal_areas
            }
            
            logger.info("Illegal mining detection completed successfully!")
            return results
            
        except Exception as e:
            logger.error(f"Error in illegal mining detection: {e}")
            raise
    
    def generate_compliance_report(self, 
                                 legal_areas: gpd.GeoDataFrame, 
                                 illegal_areas: gpd.GeoDataFrame,
                                 boundaries: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Generate compliance report for mining activities
        
        Args:
            legal_areas: Legal mining areas
            illegal_areas: Illegal mining areas
            boundaries: Legal mining boundaries
            
        Returns:
            Dict[str, Any]: Compliance report
        """
        try:
            # Calculate compliance metrics
            total_legal_area = legal_areas['area_ha'].sum() if not legal_areas.empty else 0
            total_illegal_area = illegal_areas['area_ha'].sum() if not illegal_areas.empty else 0
            total_mining_area = total_legal_area + total_illegal_area
            
            # Calculate compliance percentage
            compliance_percentage = (total_legal_area / total_mining_area * 100) if total_mining_area > 0 else 100
            
            # Identify most problematic areas
            if not illegal_areas.empty:
                largest_illegal = illegal_areas.loc[illegal_areas['area_ha'].idxmax()]
                avg_illegal_size = illegal_areas['area_ha'].mean()
            else:
                largest_illegal = None
                avg_illegal_size = 0
            
            report = {
                'compliance_percentage': float(compliance_percentage),
                'total_legal_area_ha': float(total_legal_area),
                'total_illegal_area_ha': float(total_illegal_area),
                'total_mining_area_ha': float(total_mining_area),
                'illegal_areas_count': len(illegal_areas),
                'legal_areas_count': len(legal_areas),
                'largest_illegal_area_ha': float(largest_illegal['area_ha']) if largest_illegal is not None else 0,
                'average_illegal_area_ha': float(avg_illegal_size),
                'compliance_status': 'COMPLIANT' if compliance_percentage >= 95 else 'NON_COMPLIANT'
            }
            
            logger.info(f"Compliance report generated:")
            logger.info(f"- Compliance: {compliance_percentage:.1f}%")
            logger.info(f"- Status: {report['compliance_status']}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise

def main():
    """Example usage of IllegalMiningDetection class"""
    
    # Initialize illegal mining detection
    detector = IllegalMiningDetection()
    
    print("Illegal Mining Detection module ready!")
    print("Features:")
    print("- Compare mining areas with legal boundaries")
    print("- Identify legal vs illegal mining activities")
    print("- Calculate compliance statistics")
    print("- Generate compliance reports")

if __name__ == "__main__":
    main()
