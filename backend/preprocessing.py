"""
Preprocessing Module for Illegal Mining Detection
Handles reprojection, clipping, normalization, and DEM processing
"""

import rasterio
import geopandas as gpd
import numpy as np
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from shapely.geometry import mapping
import logging
from typing import Tuple, Optional, Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Preprocessing:
    """Handles preprocessing of satellite imagery and DEM data"""
    
    def __init__(self, target_crs: str = 'EPSG:4326'):
        """
        Initialize preprocessing module
        
        Args:
            target_crs: Target coordinate reference system
        """
        self.target_crs = target_crs
        logger.info(f"Preprocessing initialized with target CRS: {target_crs}")
    
    def reproject_image(self, 
                       input_path: str, 
                       output_path: str, 
                       target_crs: Optional[str] = None) -> str:
        """
        Reproject image to target CRS
        
        Args:
            input_path: Path to input image
            output_path: Path to output image
            target_crs: Target CRS (defaults to self.target_crs)
            
        Returns:
            str: Path to reprojected image
        """
        if target_crs is None:
            target_crs = self.target_crs
            
        try:
            with rasterio.open(input_path) as src:
                # Calculate transform and dimensions
                transform, width, height = calculate_default_transform(
                    src.crs, target_crs, src.width, src.height, *src.bounds
                )
                
                # Update metadata
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': target_crs,
                    'transform': transform,
                    'width': width,
                    'height': height
                })
                
                # Reproject
                with rasterio.open(output_path, 'w', **kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs=target_crs,
                            resampling=Resampling.bilinear
                        )
            
            logger.info(f"Image reprojected to {target_crs}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error reprojecting image: {e}")
            raise
    
    def clip_image_to_boundary(self, 
                              image_path: str, 
                              boundary_gdf: gpd.GeoDataFrame, 
                              output_path: str) -> str:
        """
        Clip image to boundary geometry
        
        Args:
            image_path: Path to input image
            boundary_gdf: GeoDataFrame with boundary geometry
            output_path: Path to output clipped image
            
        Returns:
            str: Path to clipped image
        """
        try:
            with rasterio.open(image_path) as src:
                # Ensure boundary is in same CRS as image
                if boundary_gdf.crs != src.crs:
                    boundary_gdf = boundary_gdf.to_crs(src.crs)
                
                # Get geometry for masking
                geometries = [mapping(geom) for geom in boundary_gdf.geometry]
                
                # Clip image
                clipped_image, clipped_transform = mask(src, geometries, crop=True)
                
                # Update metadata
                kwargs = src.meta.copy()
                kwargs.update({
                    'height': clipped_image.shape[1],
                    'width': clipped_image.shape[2],
                    'transform': clipped_transform
                })
                
                # Save clipped image
                with rasterio.open(output_path, 'w', **kwargs) as dst:
                    dst.write(clipped_image)
            
            logger.info(f"Image clipped to boundary: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error clipping image: {e}")
            raise
    
    def normalize_spectral_bands(self, 
                                image_path: str, 
                                output_path: str,
                                bands: list = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']) -> str:
        """
        Normalize spectral bands for better analysis
        
        Args:
            image_path: Path to input image
            output_path: Path to output normalized image
            bands: List of band names to normalize
            
        Returns:
            str: Path to normalized image
        """
        try:
            with rasterio.open(image_path) as src:
                # Read all bands
                data = src.read()
                
                # Normalize each band to 0-1 range
                normalized_data = np.zeros_like(data, dtype=np.float32)
                
                for i in range(data.shape[0]):
                    band_data = data[i].astype(np.float32)
                    
                    # Handle no-data values
                    valid_mask = band_data != src.nodata
                    if np.any(valid_mask):
                        min_val = np.percentile(band_data[valid_mask], 2)
                        max_val = np.percentile(band_data[valid_mask], 98)
                        
                        if max_val > min_val:
                            normalized_data[i] = (band_data - min_val) / (max_val - min_val)
                        else:
                            normalized_data[i] = band_data
                
                # Update metadata
                kwargs = src.meta.copy()
                kwargs.update({
                    'dtype': 'float32',
                    'nodata': None
                })
                
                # Save normalized image
                with rasterio.open(output_path, 'w', **kwargs) as dst:
                    dst.write(normalized_data)
            
            logger.info(f"Spectral bands normalized: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error normalizing spectral bands: {e}")
            raise
    
    def preprocess_dem(self, 
                      dem_path: str, 
                      output_path: str,
                      fill_voids: bool = True,
                      smooth: bool = True) -> str:
        """
        Preprocess DEM data
        
        Args:
            dem_path: Path to input DEM
            output_path: Path to output processed DEM
            fill_voids: Whether to fill void pixels
            smooth: Whether to apply smoothing
            
        Returns:
            str: Path to processed DEM
        """
        try:
            with rasterio.open(dem_path) as src:
                dem_data = src.read(1).astype(np.float32)
                
                # Fill voids if requested
                if fill_voids:
                    from scipy import ndimage
                    from scipy.interpolate import griddata
                    
                    # Create mask for valid data
                    valid_mask = ~np.isnan(dem_data) & (dem_data != src.nodata)
                    
                    if not np.all(valid_mask):
                        # Get coordinates of valid points
                        y, x = np.where(valid_mask)
                        valid_values = dem_data[valid_mask]
                        
                        # Get coordinates of invalid points
                        invalid_y, invalid_x = np.where(~valid_mask)
                        
                        if len(invalid_y) > 0:
                            # Interpolate missing values
                            invalid_coords = np.column_stack([invalid_y, invalid_x])
                            valid_coords = np.column_stack([y, x])
                            
                            interpolated = griddata(
                                valid_coords, valid_values, invalid_coords,
                                method='linear', fill_value=np.nan
                            )
                            
                            # Fill the voids
                            dem_data[~valid_mask] = interpolated
                
                # Apply smoothing if requested
                if smooth:
                    from scipy.ndimage import gaussian_filter
                    dem_data = gaussian_filter(dem_data, sigma=1.0)
                
                # Update metadata
                kwargs = src.meta.copy()
                kwargs.update({
                    'dtype': 'float32',
                    'nodata': None
                })
                
                # Save processed DEM
                with rasterio.open(output_path, 'w', **kwargs) as dst:
                    dst.write(dem_data, 1)
            
            logger.info(f"DEM preprocessed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error preprocessing DEM: {e}")
            raise
    
    def align_images(self, 
                    reference_path: str, 
                    target_path: str, 
                    output_path: str) -> str:
        """
        Align target image to reference image
        
        Args:
            reference_path: Path to reference image
            target_path: Path to target image to align
            output_path: Path to output aligned image
            
        Returns:
            str: Path to aligned image
        """
        try:
            with rasterio.open(reference_path) as ref:
                with rasterio.open(target_path) as tgt:
                    # Calculate transform to align target to reference
                    transform, width, height = calculate_default_transform(
                        tgt.crs, ref.crs, ref.width, ref.height, *ref.bounds
                    )
                    
                    # Read target data
                    target_data = tgt.read()
                    
                    # Create aligned array
                    aligned_data = np.zeros((target_data.shape[0], height, width), 
                                          dtype=target_data.dtype)
                    
                    # Reproject each band
                    for i in range(target_data.shape[0]):
                        reproject(
                            source=target_data[i],
                            destination=aligned_data[i],
                            src_transform=tgt.transform,
                            src_crs=tgt.crs,
                            dst_transform=transform,
                            dst_crs=ref.crs,
                            resampling=Resampling.bilinear
                        )
                    
                    # Update metadata
                    kwargs = tgt.meta.copy()
                    kwargs.update({
                        'crs': ref.crs,
                        'transform': transform,
                        'width': width,
                        'height': height
                    })
                    
                    # Save aligned image
                    with rasterio.open(output_path, 'w', **kwargs) as dst:
                        dst.write(aligned_data)
            
            logger.info(f"Image aligned to reference: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error aligning images: {e}")
            raise
    
    def create_processing_pipeline(self, 
                                 sentinel2_path: str,
                                 dem_path: str,
                                 boundary_gdf: gpd.GeoDataFrame,
                                 output_dir: str) -> Dict[str, str]:
        """
        Run complete preprocessing pipeline
        
        Args:
            sentinel2_path: Path to Sentinel-2 image
            dem_path: Path to DEM image
            boundary_gdf: GeoDataFrame with boundary geometry
            output_dir: Output directory for processed files
            
        Returns:
            Dict[str, str]: Paths to processed files
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            processed_files = {}
            
            # Process Sentinel-2
            logger.info("Processing Sentinel-2 data...")
            sentinel2_reprojected = os.path.join(output_dir, "sentinel2_reprojected.tif")
            sentinel2_clipped = os.path.join(output_dir, "sentinel2_clipped.tif")
            sentinel2_normalized = os.path.join(output_dir, "sentinel2_normalized.tif")
            
            self.reproject_image(sentinel2_path, sentinel2_reprojected)
            self.clip_image_to_boundary(sentinel2_reprojected, boundary_gdf, sentinel2_clipped)
            self.normalize_spectral_bands(sentinel2_clipped, sentinel2_normalized)
            
            processed_files['sentinel2'] = sentinel2_normalized
            
            # Process DEM
            logger.info("Processing DEM data...")
            dem_reprojected = os.path.join(output_dir, "dem_reprojected.tif")
            dem_clipped = os.path.join(output_dir, "dem_clipped.tif")
            dem_processed = os.path.join(output_dir, "dem_processed.tif")
            
            self.reproject_image(dem_path, dem_reprojected)
            self.clip_image_to_boundary(dem_reprojected, boundary_gdf, dem_clipped)
            self.preprocess_dem(dem_clipped, dem_processed)
            
            processed_files['dem'] = dem_processed
            
            # Align DEM to Sentinel-2
            dem_aligned = os.path.join(output_dir, "dem_aligned.tif")
            self.align_images(sentinel2_normalized, dem_processed, dem_aligned)
            processed_files['dem_aligned'] = dem_aligned
            
            logger.info("Preprocessing pipeline completed successfully!")
            return processed_files
            
        except Exception as e:
            logger.error(f"Error in preprocessing pipeline: {e}")
            raise

def main():
    """Example usage of Preprocessing class"""
    
    # Initialize preprocessing
    preprocessor = Preprocessing()
    
    # Example usage (would need actual file paths)
    print("Preprocessing module ready!")
    print("Use the Preprocessing class to:")
    print("- Reproject images to target CRS")
    print("- Clip images to boundary")
    print("- Normalize spectral bands")
    print("- Preprocess DEM data")
    print("- Align images")

if __name__ == "__main__":
    main()
