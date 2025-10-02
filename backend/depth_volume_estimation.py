"""
Depth and Volume Estimation Module for Illegal Mining Detection
Estimates mining depth and volume using DEM analysis and Simpson's rule
"""

import rasterio
import numpy as np
import geopandas as gpd
from scipy import ndimage
from scipy.interpolate import griddata
from shapely.geometry import Polygon
import logging
from typing import Dict, Any, Tuple, Optional, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DepthVolumeEstimation:
    """Handles estimation of mining depth and volume using DEM analysis"""
    
    def __init__(self, reference_buffer: float = 100.0):
        """
        Initialize depth and volume estimation
        
        Args:
            reference_buffer: Buffer distance in meters for reference elevation calculation
        """
        self.reference_buffer = reference_buffer
        logger.info(f"Depth and volume estimation initialized with reference buffer: {reference_buffer}m")
    
    def load_dem_data(self, dem_path: str) -> Tuple[np.ndarray, rasterio.DatasetReader]:
        """
        Load DEM data
        
        Args:
            dem_path: Path to DEM file
            
        Returns:
            Tuple[np.ndarray, rasterio.DatasetReader]: DEM data and rasterio dataset
        """
        try:
            dem_dataset = rasterio.open(dem_path)
            dem_data = dem_dataset.read(1).astype(np.float32)
            
            # Handle no-data values
            if dem_dataset.nodata is not None:
                dem_data[dem_data == dem_dataset.nodata] = np.nan
            
            logger.info(f"DEM data loaded - Shape: {dem_data.shape}, Min: {np.nanmin(dem_data):.2f}m, Max: {np.nanmax(dem_data):.2f}m")
            return dem_data, dem_dataset
            
        except Exception as e:
            logger.error(f"Error loading DEM data: {e}")
            raise
    
    def calculate_reference_elevation(self, 
                                    dem_data: np.ndarray, 
                                    mining_mask: np.ndarray,
                                    dem_dataset: rasterio.DatasetReader) -> np.ndarray:
        """
        Calculate reference elevation around mining areas
        
        Args:
            dem_data: DEM elevation data
            mining_mask: Binary mask of mining areas
            dem_dataset: Rasterio dataset for coordinate conversion
            
        Returns:
            np.ndarray: Reference elevation surface
        """
        try:
            # Create buffer around mining areas
            mining_buffer = ndimage.binary_dilation(mining_mask, structure=np.ones((5, 5)))
            buffer_zone = mining_buffer & ~mining_mask
            
            # Get pixel coordinates
            rows, cols = np.where(buffer_zone)
            
            if len(rows) == 0:
                logger.warning("No buffer zone found around mining areas")
                return np.full_like(dem_data, np.nan)
            
            # Get elevations in buffer zone
            buffer_elevations = dem_data[buffer_zone]
            valid_elevations = buffer_elevations[~np.isnan(buffer_elevations)]
            
            if len(valid_elevations) == 0:
                logger.warning("No valid elevations in buffer zone")
                return np.full_like(dem_data, np.nan)
            
            # Calculate reference elevation (median of surrounding area)
            reference_elevation = np.median(valid_elevations)
            
            # Create reference surface
            reference_surface = np.full_like(dem_data, reference_elevation)
            
            logger.info(f"Reference elevation calculated: {reference_elevation:.2f}m")
            return reference_surface
            
        except Exception as e:
            logger.error(f"Error calculating reference elevation: {e}")
            raise
    
    def calculate_mining_depth(self, 
                              dem_data: np.ndarray, 
                              reference_surface: np.ndarray,
                              mining_mask: np.ndarray) -> np.ndarray:
        """
        Calculate mining depth relative to reference surface
        
        Args:
            dem_data: Current DEM elevation data
            reference_surface: Reference elevation surface
            mining_mask: Binary mask of mining areas
            
        Returns:
            np.ndarray: Mining depth map
        """
        try:
            # Calculate depth as difference between reference and current elevation
            depth_map = reference_surface - dem_data
            
            # Apply mining mask
            depth_map = depth_map * mining_mask
            
            # Set non-mining areas to zero
            depth_map[~mining_mask] = 0
            
            # Handle negative depths (areas higher than reference)
            depth_map = np.maximum(depth_map, 0)
            
            # Calculate statistics
            mining_depths = depth_map[mining_mask]
            if len(mining_depths) > 0:
                avg_depth = np.mean(mining_depths)
                max_depth = np.max(mining_depths)
                logger.info(f"Mining depth calculated - Average: {avg_depth:.2f}m, Max: {max_depth:.2f}m")
            else:
                logger.warning("No mining depths calculated")
            
            return depth_map
            
        except Exception as e:
            logger.error(f"Error calculating mining depth: {e}")
            raise
    
    def estimate_volume_simpsons_rule(self, 
                                    depth_map: np.ndarray, 
                                    mining_mask: np.ndarray,
                                    pixel_size: float = 10.0) -> Dict[str, float]:
        """
        Estimate mining volume using Simpson's rule approximation
        
        Args:
            depth_map: Mining depth map
            mining_mask: Binary mask of mining areas
            pixel_size: Pixel size in meters
            
        Returns:
            Dict[str, float]: Volume estimation results
        """
        try:
            # Get mining depths
            mining_depths = depth_map[mining_mask]
            
            if len(mining_depths) == 0:
                return {
                    'total_volume_m3': 0.0,
                    'average_depth_m': 0.0,
                    'max_depth_m': 0.0,
                    'mining_area_m2': 0.0,
                    'mining_area_ha': 0.0
                }
            
            # Calculate pixel area
            pixel_area = pixel_size * pixel_size  # m²
            
            # Simple volume calculation (sum of depth × area for each pixel)
            total_volume = np.sum(mining_depths) * pixel_area
            
            # Calculate statistics
            avg_depth = np.mean(mining_depths)
            max_depth = np.max(mining_depths)
            min_depth = np.min(mining_depths)
            
            # Calculate mining area
            mining_area_m2 = np.sum(mining_mask) * pixel_area
            mining_area_ha = mining_area_m2 / 10000
            
            # More sophisticated Simpson's rule implementation
            # Group pixels into strips and apply Simpson's rule
            simpsons_volume = self._apply_simpsons_rule(depth_map, mining_mask, pixel_size)
            
            results = {
                'total_volume_m3': float(total_volume),
                'simpsons_volume_m3': float(simpsons_volume),
                'average_depth_m': float(avg_depth),
                'max_depth_m': float(max_depth),
                'min_depth_m': float(min_depth),
                'mining_area_m2': float(mining_area_m2),
                'mining_area_ha': float(mining_area_ha),
                'pixel_count': int(np.sum(mining_mask))
            }
            
            logger.info(f"Volume estimation completed:")
            logger.info(f"- Total volume: {total_volume:.0f} m³")
            logger.info(f"- Simpson's volume: {simpsons_volume:.0f} m³")
            logger.info(f"- Mining area: {mining_area_ha:.2f} ha")
            
            return results
            
        except Exception as e:
            logger.error(f"Error estimating volume: {e}")
            raise
    
    def _apply_simpsons_rule(self, 
                           depth_map: np.ndarray, 
                           mining_mask: np.ndarray,
                           pixel_size: float) -> float:
        """
        Apply Simpson's rule for more accurate volume estimation
        
        Args:
            depth_map: Mining depth map
            mining_mask: Binary mask of mining areas
            pixel_size: Pixel size in meters
            
        Returns:
            float: Volume using Simpson's rule
        """
        try:
            # Get mining area bounds
            rows, cols = np.where(mining_mask)
            if len(rows) == 0:
                return 0.0
            
            min_row, max_row = np.min(rows), np.max(rows)
            min_col, max_col = np.min(cols), np.max(cols)
            
            # Extract mining area
            mining_depths = depth_map[min_row:max_row+1, min_col:max_col+1]
            mining_area_mask = mining_mask[min_row:max_row+1, min_col:max_col+1]
            
            # Apply Simpson's rule along rows
            pixel_area = pixel_size * pixel_size
            volume = 0.0
            
            for i in range(mining_depths.shape[0]):
                row_depths = mining_depths[i]
                row_mask = mining_area_mask[i]
                
                if np.any(row_mask):
                    # Get valid depths in this row
                    valid_depths = row_depths[row_mask]
                    
                    if len(valid_depths) >= 3:
                        # Apply Simpson's rule: (h/3) * (y0 + 4*y1 + 2*y2 + 4*y3 + ... + yn)
                        h = pixel_size
                        n = len(valid_depths)
                        
                        if n % 2 == 0:  # Even number of points
                            simpsons_sum = valid_depths[0] + valid_depths[-1]  # First and last
                            simpsons_sum += 4 * np.sum(valid_depths[1::2])  # Odd indices
                            simpsons_sum += 2 * np.sum(valid_depths[2:-1:2])  # Even indices (excluding first and last)
                        else:  # Odd number of points
                            simpsons_sum = valid_depths[0] + valid_depths[-1]  # First and last
                            simpsons_sum += 4 * np.sum(valid_depths[1::2])  # Odd indices
                            simpsons_sum += 2 * np.sum(valid_depths[2:-2:2])  # Even indices (excluding first and last)
                        
                        volume += (h / 3) * simpsons_sum * pixel_size
                    else:
                        # Fall back to simple sum for rows with < 3 points
                        volume += np.sum(valid_depths) * pixel_area
            
            return volume
            
        except Exception as e:
            logger.error(f"Error applying Simpson's rule: {e}")
            return 0.0
    
    def save_depth_map(self, 
                      depth_map: np.ndarray, 
                      dem_dataset: rasterio.DatasetReader,
                      output_path: str) -> str:
        """
        Save depth map to GeoTIFF
        
        Args:
            depth_map: Mining depth map
            dem_dataset: Original DEM dataset for metadata
            output_path: Output file path
            
        Returns:
            str: Path to saved depth map
        """
        try:
            # Update metadata
            kwargs = dem_dataset.meta.copy()
            kwargs.update({
                'dtype': 'float32',
                'nodata': 0.0
            })
            
            # Save depth map
            with rasterio.open(output_path, 'w', **kwargs) as dst:
                dst.write(depth_map, 1)
            
            logger.info(f"Depth map saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving depth map: {e}")
            raise
    
    def estimate_mining_volume(self, 
                              dem_path: str, 
                              mining_mask_path: str, 
                              output_dir: str,
                              pixel_size: float = 10.0) -> Dict[str, Any]:
        """
        Main function to estimate mining depth and volume
        
        Args:
            dem_path: Path to DEM file
            mining_mask_path: Path to mining mask file
            output_dir: Output directory
            pixel_size: Pixel size in meters
            
        Returns:
            Dict[str, Any]: Complete estimation results
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Load DEM data
            dem_data, dem_dataset = self.load_dem_data(dem_path)
            
            # Load mining mask
            with rasterio.open(mining_mask_path) as src:
                mining_mask = src.read(1).astype(bool)
            
            # Calculate reference elevation
            reference_surface = self.calculate_reference_elevation(dem_data, mining_mask, dem_dataset)
            
            # Calculate mining depth
            depth_map = self.calculate_mining_depth(dem_data, reference_surface, mining_mask)
            
            # Estimate volume
            volume_results = self.estimate_volume_simpsons_rule(depth_map, mining_mask, pixel_size)
            
            # Save depth map
            depth_map_path = os.path.join(output_dir, "mining_depth_map.tif")
            self.save_depth_map(depth_map, dem_dataset, depth_map_path)
            
            # Combine results
            results = {
                **volume_results,
                'depth_map_path': depth_map_path,
                'reference_elevation_m': float(np.nanmean(reference_surface)),
                'pixel_size_m': pixel_size
            }
            
            logger.info("Mining volume estimation completed successfully!")
            return results
            
        except Exception as e:
            logger.error(f"Error in mining volume estimation: {e}")
            raise

def main():
    """Example usage of DepthVolumeEstimation class"""
    
    # Initialize depth and volume estimation
    estimator = DepthVolumeEstimation(reference_buffer=100.0)
    
    print("Depth and Volume Estimation module ready!")
    print("Features:")
    print("- Calculate mining depth relative to reference elevation")
    print("- Estimate volume using Simpson's rule")
    print("- Generate depth maps")
    print("- Statistical analysis of mining volumes")

if __name__ == "__main__":
    main()
