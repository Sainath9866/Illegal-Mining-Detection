"""
Dataset Acquisition Module for Illegal Mining Detection
Downloads and preprocesses satellite data (Sentinel-2, Sentinel-1, DEM)
"""

import os
import ee
import rasterio
import geopandas as gpd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAcquisition:
    """Handles downloading and preprocessing of satellite data"""
    
    def __init__(self, service_account_path: Optional[str] = None):
        """
        Initialize Google Earth Engine
        
        Args:
            service_account_path: Path to GEE service account JSON file
        """
        try:
            if service_account_path:
                credentials = ee.ServiceAccountCredentials(None, service_account_path)
                ee.Initialize(credentials)
            else:
                ee.Initialize()
            logger.info("Google Earth Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Earth Engine: {e}")
            raise
    
    def get_sentinel2_data(self, 
                          geometry: Dict[str, Any], 
                          start_date: str, 
                          end_date: str,
                          cloud_cover_threshold: int = 20) -> ee.Image:
        """
        Download Sentinel-2 imagery
        
        Args:
            geometry: Bounding box or polygon geometry
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            cloud_cover_threshold: Maximum cloud cover percentage
            
        Returns:
            ee.Image: Sentinel-2 image collection
        """
        try:
            # Define the area of interest
            aoi = ee.Geometry(geometry)
            
            # Get Sentinel-2 collection
            collection = (ee.ImageCollection('COPERNICUS/S2_SR')
                         .filterBounds(aoi)
                         .filterDate(start_date, end_date)
                         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover_threshold))
                         .sort('CLOUDY_PIXEL_PERCENTAGE'))
            
            # Get the least cloudy image
            image = collection.first()
            
            # Select relevant bands for mining detection
            bands = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']  # Blue, Green, Red, NIR, SWIR1, SWIR2
            image = image.select(bands)
            
            # Clip to area of interest
            image = image.clip(aoi)
            
            logger.info(f"Sentinel-2 data acquired for {start_date} to {end_date}")
            return image
            
        except Exception as e:
            logger.error(f"Error acquiring Sentinel-2 data: {e}")
            raise
    
    def get_sentinel1_data(self, 
                          geometry: Dict[str, Any], 
                          start_date: str, 
                          end_date: str) -> ee.Image:
        """
        Download Sentinel-1 SAR data
        
        Args:
            geometry: Bounding box or polygon geometry
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            ee.Image: Sentinel-1 image
        """
        try:
            aoi = ee.Geometry(geometry)
            
            # Get Sentinel-1 collection
            collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
                         .filterBounds(aoi)
                         .filterDate(start_date, end_date)
                         .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                         .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
                         .sort('system:time_start'))
            
            # Get the first image
            image = collection.first()
            
            # Select VV and VH bands
            image = image.select(['VV', 'VH'])
            
            # Clip to area of interest
            image = image.clip(aoi)
            
            logger.info(f"Sentinel-1 data acquired for {start_date} to {end_date}")
            return image
            
        except Exception as e:
            logger.error(f"Error acquiring Sentinel-1 data: {e}")
            raise
    
    def get_dem_data(self, geometry: Dict[str, Any]) -> ee.Image:
        """
        Download DEM data (SRTM or ALOS PALSAR)
        
        Args:
            geometry: Bounding box or polygon geometry
            
        Returns:
            ee.Image: DEM image
        """
        try:
            aoi = ee.Geometry(geometry)
            
            # Try SRTM first (30m resolution)
            try:
                dem = ee.Image('USGS/SRTMGL1_003').clip(aoi)
                logger.info("Using SRTM DEM (30m resolution)")
            except:
                # Fallback to ALOS PALSAR DEM (12.5m resolution)
                dem = ee.Image('JAXA/ALOS/AW3D30/V3_2').select('AVE_DSM').clip(aoi)
                logger.info("Using ALOS PALSAR DEM (12.5m resolution)")
            
            return dem
            
        except Exception as e:
            logger.error(f"Error acquiring DEM data: {e}")
            raise
    
    def download_image_to_local(self, 
                               image: ee.Image, 
                               output_path: str, 
                               scale: int = 10,
                               crs: str = 'EPSG:4326') -> str:
        """
        Download Earth Engine image to local file
        
        Args:
            image: Earth Engine image
            output_path: Local output file path
            scale: Pixel scale in meters
            crs: Coordinate reference system
            
        Returns:
            str: Path to downloaded file
        """
        try:
            # Get image bounds
            bounds = image.geometry().bounds().getInfo()
            
            # Download image
            task = ee.batch.Export.image.toDrive(
                image=image,
                description='mining_detection_data',
                folder='illegal_mining_detection',
                fileNamePrefix=os.path.basename(output_path).split('.')[0],
                scale=scale,
                crs=crs,
                region=bounds,
                fileFormat='GeoTIFF'
            )
            
            task.start()
            logger.info(f"Download task started. Check Google Earth Engine console for progress.")
            logger.info(f"Output will be saved to: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            raise
    
    def load_shapefile(self, shapefile_path: str) -> gpd.GeoDataFrame:
        """
        Load mining boundary shapefile
        
        Args:
            shapefile_path: Path to shapefile
            
        Returns:
            gpd.GeoDataFrame: Loaded shapefile
        """
        try:
            gdf = gpd.read_file(shapefile_path)
            
            # Ensure CRS is set
            if gdf.crs is None:
                gdf.set_crs('EPSG:4326', inplace=True)
            
            # Reproject to WGS84 if needed
            if gdf.crs != 'EPSG:4326':
                gdf = gdf.to_crs('EPSG:4326')
            
            logger.info(f"Shapefile loaded: {len(gdf)} features")
            return gdf
            
        except Exception as e:
            logger.error(f"Error loading shapefile: {e}")
            raise
    
    def get_india_district_boundaries(self, state_name: Optional[str] = None) -> gpd.GeoDataFrame:
        """
        Get India district boundaries from GADM
        
        Args:
            state_name: Optional state name to filter
            
        Returns:
            gpd.GeoDataFrame: District boundaries
        """
        try:
            # This would typically download from GADM or use a local file
            # For now, return a placeholder
            logger.info("District boundaries would be loaded from GADM dataset")
            return gpd.GeoDataFrame()
            
        except Exception as e:
            logger.error(f"Error loading district boundaries: {e}")
            raise

def main():
    """Example usage of DataAcquisition class"""
    
    # Initialize data acquisition
    data_acq = DataAcquisition()
    
    # Define area of interest (example: a mining area in India)
    aoi = {
        "type": "Polygon",
        "coordinates": [[
            [77.0, 28.0],
            [77.1, 28.0],
            [77.1, 28.1],
            [77.0, 28.1],
            [77.0, 28.0]
        ]]
    }
    
    # Date range for data acquisition
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    
    try:
        # Get satellite data
        sentinel2 = data_acq.get_sentinel2_data(aoi, start_date, end_date)
        sentinel1 = data_acq.get_sentinel1_data(aoi, start_date, end_date)
        dem = data_acq.get_dem_data(aoi)
        
        print("Data acquisition completed successfully!")
        print(f"Sentinel-2 bands: {sentinel2.bandNames().getInfo()}")
        print(f"Sentinel-1 bands: {sentinel1.bandNames().getInfo()}")
        print(f"DEM band: {dem.bandNames().getInfo()}")
        
    except Exception as e:
        print(f"Error in data acquisition: {e}")

if __name__ == "__main__":
    main()
