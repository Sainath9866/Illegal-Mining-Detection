"""
Mining Detection Module for Illegal Mining Detection
Implements rule-based and ML-based mining area detection
"""

import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from scipy import ndimage
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import logging
from typing import Tuple, Optional, Dict, Any, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MiningDetection:
    """Handles detection of mining areas using rule-based and ML methods"""
    
    def __init__(self, 
                 ndvi_threshold: float = 0.2, 
                 bsi_threshold: float = 0.3):
        """
        Initialize mining detection
        
        Args:
            ndvi_threshold: NDVI threshold for non-vegetated areas
            bsi_threshold: BSI threshold for bare soil detection
        """
        self.ndvi_threshold = ndvi_threshold
        self.bsi_threshold = bsi_threshold
        logger.info(f"Mining detection initialized with NDVI threshold: {ndvi_threshold}, BSI threshold: {bsi_threshold}")
    
    def calculate_ndvi(self, nir_band: np.ndarray, red_band: np.ndarray) -> np.ndarray:
        """
        Calculate Normalized Difference Vegetation Index (NDVI)
        
        Args:
            nir_band: Near-infrared band data
            red_band: Red band data
            
        Returns:
            np.ndarray: NDVI values
        """
        try:
            # Avoid division by zero
            denominator = nir_band + red_band
            denominator = np.where(denominator == 0, 1e-10, denominator)
            
            ndvi = (nir_band - red_band) / denominator
            
            # Clip values to valid range [-1, 1]
            ndvi = np.clip(ndvi, -1, 1)
            
            logger.info(f"NDVI calculated - Min: {np.nanmin(ndvi):.3f}, Max: {np.nanmax(ndvi):.3f}")
            return ndvi
            
        except Exception as e:
            logger.error(f"Error calculating NDVI: {e}")
            raise
    
    def calculate_bsi(self, 
                     swir_band: np.ndarray, 
                     red_band: np.ndarray, 
                     nir_band: np.ndarray, 
                     blue_band: np.ndarray) -> np.ndarray:
        """
        Calculate Bare Soil Index (BSI)
        
        Args:
            swir_band: SWIR band data
            red_band: Red band data
            nir_band: NIR band data
            blue_band: Blue band data
            
        Returns:
            np.ndarray: BSI values
        """
        try:
            # Calculate BSI: ((SWIR + Red) - (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))
            numerator = (swir_band + red_band) - (nir_band + blue_band)
            denominator = (swir_band + red_band) + (nir_band + blue_band)
            
            # Avoid division by zero
            denominator = np.where(denominator == 0, 1e-10, denominator)
            
            bsi = numerator / denominator
            
            # Clip values to valid range [-1, 1]
            bsi = np.clip(bsi, -1, 1)
            
            logger.info(f"BSI calculated - Min: {np.nanmin(bsi):.3f}, Max: {np.nanmax(bsi):.3f}")
            return bsi
            
        except Exception as e:
            logger.error(f"Error calculating BSI: {e}")
            raise
    
    def rule_based_mining_detection(self, 
                                   image_path: str, 
                                   output_path: str) -> Dict[str, Any]:
        """
        Perform rule-based mining detection using NDVI and BSI
        
        Args:
            image_path: Path to preprocessed Sentinel-2 image
            output_path: Path to output mining mask
            
        Returns:
            Dict[str, Any]: Detection results and statistics
        """
        try:
            with rasterio.open(image_path) as src:
                # Read bands (assuming order: B2, B3, B4, B8, B11, B12)
                blue = src.read(3)  # B2
                green = src.read(2)  # B3
                red = src.read(1)   # B4
                nir = src.read(4)   # B8
                swir1 = src.read(5) # B11
                swir2 = src.read(6) # B12
                
                # Calculate indices
                ndvi = self.calculate_ndvi(nir, red)
                bsi = self.calculate_bsi(swir1, red, nir, blue)
                
                # Apply thresholds for mining detection
                # Mining areas: low vegetation (NDVI < threshold) AND high bare soil (BSI > threshold)
                mining_mask = (ndvi < self.ndvi_threshold) & (bsi > self.bsi_threshold)
                
                # Additional filtering to remove noise
                # Remove small isolated pixels
                mining_mask = ndimage.binary_opening(mining_mask, structure=np.ones((3, 3)))
                mining_mask = ndimage.binary_closing(mining_mask, structure=np.ones((5, 5)))
                
                # Convert to binary mask (0: non-mining, 1: mining)
                mining_mask = mining_mask.astype(np.uint8)
                
                # Calculate statistics
                total_pixels = mining_mask.size
                mining_pixels = np.sum(mining_mask)
                mining_percentage = (mining_pixels / total_pixels) * 100
                
                # Calculate area (assuming 10m pixel size for Sentinel-2)
                pixel_area = 100  # 10m x 10m = 100 m²
                mining_area_m2 = mining_pixels * pixel_area
                mining_area_ha = mining_area_m2 / 10000
                
                # Save mining mask
                kwargs = src.meta.copy()
                kwargs.update({
                    'dtype': 'uint8',
                    'count': 1,
                    'nodata': 0
                })
                
                with rasterio.open(output_path, 'w', **kwargs) as dst:
                    dst.write(mining_mask, 1)
                
                results = {
                    'mining_mask_path': output_path,
                    'mining_pixels': int(mining_pixels),
                    'total_pixels': int(total_pixels),
                    'mining_percentage': float(mining_percentage),
                    'mining_area_m2': float(mining_area_m2),
                    'mining_area_ha': float(mining_area_ha),
                    'ndvi_stats': {
                        'min': float(np.nanmin(ndvi)),
                        'max': float(np.nanmax(ndvi)),
                        'mean': float(np.nanmean(ndvi))
                    },
                    'bsi_stats': {
                        'min': float(np.nanmin(bsi)),
                        'max': float(np.nanmax(bsi)),
                        'mean': float(np.nanmean(bsi))
                    }
                }
                
                logger.info(f"Rule-based mining detection completed:")
                logger.info(f"- Mining area: {mining_area_ha:.2f} hectares")
                logger.info(f"- Mining percentage: {mining_percentage:.2f}%")
                
                return results
                
        except Exception as e:
            logger.error(f"Error in rule-based mining detection: {e}")
            raise
    
    def extract_mining_polygons(self, 
                               mining_mask_path: str, 
                               output_path: str,
                               min_area_m2: float = 1000) -> gpd.GeoDataFrame:
        """
        Extract mining polygons from binary mask
        
        Args:
            mining_mask_path: Path to mining mask
            output_path: Path to output shapefile
            min_area_m2: Minimum area for mining polygons (m²)
            
        Returns:
            gpd.GeoDataFrame: Mining polygons
        """
        try:
            with rasterio.open(mining_mask_path) as src:
                # Read mining mask
                mining_mask = src.read(1)
                
                # Get transform and CRS
                transform = src.transform
                crs = src.crs
                
                # Find contours of mining areas
                from skimage import measure
                
                # Label connected components
                labeled_mask = measure.label(mining_mask)
                
                # Extract properties of each region
                regions = measure.regionprops(labeled_mask)
                
                polygons = []
                areas = []
                
                for region in regions:
                    # Skip small regions
                    area_m2 = region.area * (transform[0] ** 2)  # Convert pixels to m²
                    if area_m2 < min_area_m2:
                        continue
                    
                    # Get coordinates of region
                    coords = region.coords
                    
                    # Convert pixel coordinates to geographic coordinates
                    geo_coords = []
                    for coord in coords:
                        geo_x, geo_y = rasterio.transform.xy(transform, coord[0], coord[1])
                        geo_coords.append([geo_x, geo_y])
                    
                    # Create polygon
                    if len(geo_coords) >= 3:
                        polygon = Polygon(geo_coords)
                        if polygon.is_valid and polygon.area > 0:
                            polygons.append(polygon)
                            areas.append(area_m2)
                
                # Create GeoDataFrame
                gdf = gpd.GeoDataFrame({
                    'area_m2': areas,
                    'area_ha': [area / 10000 for area in areas],
                    'geometry': polygons
                }, crs=crs)
                
                # Save to shapefile
                gdf.to_file(output_path)
                
                logger.info(f"Extracted {len(polygons)} mining polygons")
                logger.info(f"Total mining area: {sum(areas) / 10000:.2f} hectares")
                
                return gdf
                
        except Exception as e:
            logger.error(f"Error extracting mining polygons: {e}")
            raise
    
    def ml_based_mining_detection(self, 
                                 image_path: str, 
                                 output_path: str,
                                 model_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform ML-based mining detection using segmentation model
        
        Args:
            image_path: Path to preprocessed Sentinel-2 image
            output_path: Path to output mining mask
            model_path: Path to trained model (optional)
            
        Returns:
            Dict[str, Any]: Detection results and statistics
        """
        try:
            # This is a placeholder for ML-based detection
            # In a real implementation, you would load a trained U-Net or DeepLabV3 model
            
            logger.info("ML-based mining detection not implemented yet")
            logger.info("This would use a trained U-Net or DeepLabV3 model")
            
            # For now, fall back to rule-based detection
            return self.rule_based_mining_detection(image_path, output_path)
            
        except Exception as e:
            logger.error(f"Error in ML-based mining detection: {e}")
            raise
    
    def detect_mining_areas(self, 
                           image_path: str, 
                           output_dir: str,
                           method: str = 'rule_based',
                           min_area_m2: float = 1000) -> Dict[str, Any]:
        """
        Main function to detect mining areas
        
        Args:
            image_path: Path to preprocessed Sentinel-2 image
            output_dir: Output directory for results
            method: Detection method ('rule_based' or 'ml_based')
            min_area_m2: Minimum area for mining polygons
            
        Returns:
            Dict[str, Any]: Complete detection results
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Paths for outputs
            mining_mask_path = os.path.join(output_dir, "mining_mask.tif")
            mining_polygons_path = os.path.join(output_dir, "mining_polygons.shp")
            
            # Perform detection
            if method == 'rule_based':
                detection_results = self.rule_based_mining_detection(image_path, mining_mask_path)
            elif method == 'ml_based':
                detection_results = self.ml_based_mining_detection(image_path, mining_mask_path)
            else:
                raise ValueError(f"Unknown detection method: {method}")
            
            # Extract polygons
            mining_polygons = self.extract_mining_polygons(
                mining_mask_path, mining_polygons_path, min_area_m2
            )
            
            # Combine results
            results = {
                **detection_results,
                'mining_polygons_path': mining_polygons_path,
                'mining_polygons_count': len(mining_polygons),
                'method': method
            }
            
            logger.info(f"Mining detection completed using {method} method")
            return results
            
        except Exception as e:
            logger.error(f"Error in mining detection: {e}")
            raise

def main():
    """Example usage of MiningDetection class"""
    
    # Initialize mining detection
    detector = MiningDetection(ndvi_threshold=0.2, bsi_threshold=0.3)
    
    print("Mining Detection module ready!")
    print("Features:")
    print("- Rule-based detection using NDVI and BSI")
    print("- ML-based detection (placeholder)")
    print("- Polygon extraction from binary masks")
    print("- Statistical analysis of mining areas")

if __name__ == "__main__":
    main()
