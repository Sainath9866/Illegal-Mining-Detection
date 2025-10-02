"""
2D Visualization Module for Illegal Mining Detection
Creates interactive maps using folium and matplotlib
"""

import folium
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import rasterio
import geopandas as gpd
from folium import plugins
import logging
from typing import Dict, Any, List, Tuple, Optional
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Visualization2D:
    """Handles 2D visualization of mining detection results"""
    
    def __init__(self, 
                 map_center: Tuple[float, float] = (28.0, 77.0),
                 zoom_start: int = 12):
        """
        Initialize 2D visualization
        
        Args:
            map_center: Center coordinates for maps (lat, lon)
            zoom_start: Initial zoom level
        """
        self.map_center = map_center
        self.zoom_start = zoom_start
        logger.info(f"2D visualization initialized with center: {map_center}")
    
    def create_base_map(self, 
                       center: Optional[Tuple[float, float]] = None,
                       zoom: Optional[int] = None) -> folium.Map:
        """
        Create base folium map
        
        Args:
            center: Map center coordinates
            zoom: Initial zoom level
            
        Returns:
            folium.Map: Base map
        """
        try:
            if center is None:
                center = self.map_center
            if zoom is None:
                zoom = self.zoom_start
            
            # Create base map with multiple tile layers
            m = folium.Map(
                location=center,
                zoom_start=zoom,
                tiles=None
            )
            
            # Add different tile layers
            folium.TileLayer(
                tiles='OpenStreetMap',
                name='OpenStreetMap',
                overlay=False,
                control=True
            ).add_to(m)
            
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Satellite',
                overlay=False,
                control=True
            ).add_to(m)
            
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Topographic',
                overlay=False,
                control=True
            ).add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            logger.info("Base map created successfully")
            return m
            
        except Exception as e:
            logger.error(f"Error creating base map: {e}")
            raise
    
    def add_satellite_imagery(self, 
                             map_obj: folium.Map, 
                             image_path: str,
                             bounds: Tuple[Tuple[float, float], Tuple[float, float]]) -> folium.Map:
        """
        Add satellite imagery overlay to map
        
        Args:
            map_obj: Folium map object
            image_path: Path to satellite image
            bounds: Image bounds as ((min_lat, min_lon), (max_lat, max_lon))
            
        Returns:
            folium.Map: Updated map
        """
        try:
            # Add image overlay
            folium.raster_layers.ImageOverlay(
                image=image_path,
                bounds=bounds,
                opacity=0.7,
                name='Satellite Imagery',
                overlay=True,
                control=True
            ).add_to(map_obj)
            
            logger.info("Satellite imagery added to map")
            return map_obj
            
        except Exception as e:
            logger.error(f"Error adding satellite imagery: {e}")
            raise
    
    def add_mining_boundaries(self, 
                             map_obj: folium.Map, 
                             boundaries_path: str,
                             color: str = 'blue',
                             weight: int = 3) -> folium.Map:
        """
        Add mining lease boundaries to map
        
        Args:
            map_obj: Folium map object
            boundaries_path: Path to boundaries shapefile
            color: Boundary color
            weight: Boundary line weight
            
        Returns:
            folium.Map: Updated map
        """
        try:
            # Load boundaries
            boundaries = gpd.read_file(boundaries_path)
            
            # Add boundaries to map
            folium.GeoJson(
                boundaries.to_json(),
                style_function=lambda feature: {
                    'fillColor': color,
                    'color': color,
                    'weight': weight,
                    'fillOpacity': 0.1
                },
                name='Mining Boundaries',
                overlay=True,
                control=True
            ).add_to(map_obj)
            
            logger.info(f"Added {len(boundaries)} mining boundaries to map")
            return map_obj
            
        except Exception as e:
            logger.error(f"Error adding mining boundaries: {e}")
            raise
    
    def add_mining_areas(self, 
                        map_obj: folium.Map, 
                        legal_areas_path: str,
                        illegal_areas_path: str) -> folium.Map:
        """
        Add detected mining areas to map
        
        Args:
            map_obj: Folium map object
            legal_areas_path: Path to legal mining areas shapefile
            illegal_areas_path: Path to illegal mining areas shapefile
            
        Returns:
            folium.Map: Updated map
        """
        try:
            # Add legal mining areas
            if os.path.exists(legal_areas_path):
                legal_areas = gpd.read_file(legal_areas_path)
                if not legal_areas.empty:
                    folium.GeoJson(
                        legal_areas.to_json(),
                        style_function=lambda feature: {
                            'fillColor': 'green',
                            'color': 'green',
                            'weight': 2,
                            'fillOpacity': 0.6
                        },
                        name='Legal Mining Areas',
                        overlay=True,
                        control=True,
                        popup=folium.Popup(
                            'Legal Mining Area<br>'
                            f'Area: {feature["properties"].get("area_ha", "N/A")} ha',
                            parse_html=True
                        )
                    ).add_to(map_obj)
            
            # Add illegal mining areas
            if os.path.exists(illegal_areas_path):
                illegal_areas = gpd.read_file(illegal_areas_path)
                if not illegal_areas.empty:
                    folium.GeoJson(
                        illegal_areas.to_json(),
                        style_function=lambda feature: {
                            'fillColor': 'red',
                            'color': 'red',
                            'weight': 2,
                            'fillOpacity': 0.6
                        },
                        name='Illegal Mining Areas',
                        overlay=True,
                        control=True,
                        popup=folium.Popup(
                            'Illegal Mining Area<br>'
                            f'Area: {feature["properties"].get("area_ha", "N/A")} ha',
                            parse_html=True
                        )
                    ).add_to(map_obj)
            
            logger.info("Mining areas added to map")
            return map_obj
            
        except Exception as e:
            logger.error(f"Error adding mining areas: {e}")
            raise
    
    def add_depth_visualization(self, 
                               map_obj: folium.Map, 
                               depth_map_path: str,
                               bounds: Tuple[Tuple[float, float], Tuple[float, float]]) -> folium.Map:
        """
        Add mining depth visualization to map
        
        Args:
            map_obj: Folium map object
            depth_map_path: Path to depth map GeoTIFF
            bounds: Image bounds
            
        Returns:
            folium.Map: Updated map
        """
        try:
            # Add depth map overlay
            folium.raster_layers.ImageOverlay(
                image=depth_map_path,
                bounds=bounds,
                opacity=0.5,
                name='Mining Depth',
                overlay=True,
                control=True,
                colormap=plt.cm.Reds
            ).add_to(map_obj)
            
            logger.info("Depth visualization added to map")
            return map_obj
            
        except Exception as e:
            logger.error(f"Error adding depth visualization: {e}")
            raise
    
    def add_statistics_popup(self, 
                           map_obj: folium.Map, 
                           stats: Dict[str, Any]) -> folium.Map:
        """
        Add statistics popup to map
        
        Args:
            map_obj: Folium map object
            stats: Statistics dictionary
            
        Returns:
            folium.Map: Updated map
        """
        try:
            # Create statistics HTML
            stats_html = f"""
            <div style="width: 300px; padding: 10px;">
                <h3>Mining Detection Statistics</h3>
                <p><b>Legal Mining:</b></p>
                <ul>
                    <li>Areas: {stats.get('legal_mining', {}).get('count', 0)}</li>
                    <li>Area: {stats.get('legal_mining', {}).get('area_ha', 0):.2f} ha</li>
                    <li>Percentage: {stats.get('legal_mining', {}).get('percentage', 0):.1f}%</li>
                </ul>
                <p><b>Illegal Mining:</b></p>
                <ul>
                    <li>Areas: {stats.get('illegal_mining', {}).get('count', 0)}</li>
                    <li>Area: {stats.get('illegal_mining', {}).get('area_ha', 0):.2f} ha</li>
                    <li>Percentage: {stats.get('illegal_mining', {}).get('percentage', 0):.1f}%</li>
                </ul>
                <p><b>Total Mining:</b></p>
                <ul>
                    <li>Areas: {stats.get('total_mining', {}).get('count', 0)}</li>
                    <li>Area: {stats.get('total_mining', {}).get('area_ha', 0):.2f} ha</li>
                </ul>
            </div>
            """
            
            # Add popup to map
            folium.Marker(
                location=self.map_center,
                popup=folium.Popup(stats_html, parse_html=True),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(map_obj)
            
            logger.info("Statistics popup added to map")
            return map_obj
            
        except Exception as e:
            logger.error(f"Error adding statistics popup: {e}")
            raise
    
    def create_mining_detection_map(self, 
                                   output_path: str,
                                   boundaries_path: str,
                                   legal_areas_path: str,
                                   illegal_areas_path: str,
                                   stats: Dict[str, Any],
                                   satellite_image_path: Optional[str] = None,
                                   depth_map_path: Optional[str] = None) -> str:
        """
        Create complete mining detection map
        
        Args:
            output_path: Path to save HTML map
            boundaries_path: Path to mining boundaries
            legal_areas_path: Path to legal mining areas
            illegal_areas_path: Path to illegal mining areas
            stats: Statistics dictionary
            satellite_image_path: Optional satellite image path
            depth_map_path: Optional depth map path
            
        Returns:
            str: Path to saved map
        """
        try:
            # Create base map
            map_obj = self.create_base_map()
            
            # Add satellite imagery if provided
            if satellite_image_path and os.path.exists(satellite_image_path):
                # Get image bounds (would need to be calculated from image metadata)
                bounds = ((27.9, 76.9), (28.1, 77.1))  # Example bounds
                self.add_satellite_imagery(map_obj, satellite_image_path, bounds)
            
            # Add mining boundaries
            self.add_mining_boundaries(map_obj, boundaries_path)
            
            # Add mining areas
            self.add_mining_areas(map_obj, legal_areas_path, illegal_areas_path)
            
            # Add depth visualization if provided
            if depth_map_path and os.path.exists(depth_map_path):
                bounds = ((27.9, 76.9), (28.1, 77.1))  # Example bounds
                self.add_depth_visualization(map_obj, depth_map_path, bounds)
            
            # Add statistics popup
            self.add_statistics_popup(map_obj, stats)
            
            # Save map
            map_obj.save(output_path)
            
            logger.info(f"Mining detection map saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating mining detection map: {e}")
            raise
    
    def create_ndvi_bsi_plots(self, 
                             image_path: str, 
                             output_dir: str) -> Dict[str, str]:
        """
        Create NDVI and BSI visualization plots
        
        Args:
            image_path: Path to preprocessed Sentinel-2 image
            output_dir: Output directory for plots
            
        Returns:
            Dict[str, str]: Paths to created plots
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            with rasterio.open(image_path) as src:
                # Read bands
                blue = src.read(3)  # B2
                green = src.read(2)  # B3
                red = src.read(1)   # B4
                nir = src.read(4)   # B8
                swir1 = src.read(5) # B11
                swir2 = src.read(6) # B12
                
                # Calculate indices
                ndvi = (nir - red) / (nir + red + 1e-10)
                bsi = ((swir1 + red) - (nir + blue)) / ((swir1 + red) + (nir + blue) + 1e-10)
                
                # Create NDVI plot
                plt.figure(figsize=(12, 8))
                plt.subplot(2, 2, 1)
                plt.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
                plt.colorbar(label='NDVI')
                plt.title('Normalized Difference Vegetation Index (NDVI)')
                plt.axis('off')
                
                # Create BSI plot
                plt.subplot(2, 2, 2)
                plt.imshow(bsi, cmap='RdYlBu', vmin=-1, vmax=1)
                plt.colorbar(label='BSI')
                plt.title('Bare Soil Index (BSI)')
                plt.axis('off')
                
                # Create RGB composite
                plt.subplot(2, 2, 3)
                rgb = np.dstack([red, green, blue])
                rgb_norm = (rgb - rgb.min()) / (rgb.max() - rgb.min())
                plt.imshow(rgb_norm)
                plt.title('RGB Composite')
                plt.axis('off')
                
                # Create histogram
                plt.subplot(2, 2, 4)
                plt.hist(ndvi.flatten(), bins=50, alpha=0.7, label='NDVI', color='green')
                plt.hist(bsi.flatten(), bins=50, alpha=0.7, label='BSI', color='brown')
                plt.xlabel('Index Value')
                plt.ylabel('Frequency')
                plt.title('NDVI and BSI Distribution')
                plt.legend()
                
                plt.tight_layout()
                
                # Save plot
                plot_path = os.path.join(output_dir, 'ndvi_bsi_analysis.png')
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                logger.info(f"NDVI/BSI plots saved to: {plot_path}")
                return {'ndvi_bsi_plot': plot_path}
                
        except Exception as e:
            logger.error(f"Error creating NDVI/BSI plots: {e}")
            raise
    
    def create_depth_volume_plots(self, 
                                 depth_map_path: str, 
                                 volume_stats: Dict[str, Any],
                                 output_dir: str) -> Dict[str, str]:
        """
        Create depth and volume visualization plots
        
        Args:
            depth_map_path: Path to depth map
            volume_stats: Volume statistics
            output_dir: Output directory
            
        Returns:
            Dict[str, str]: Paths to created plots
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            with rasterio.open(depth_map_path) as src:
                depth_map = src.read(1)
                
                # Create depth visualization
                plt.figure(figsize=(15, 10))
                
                # Depth map
                plt.subplot(2, 3, 1)
                im = plt.imshow(depth_map, cmap='Reds', vmin=0)
                plt.colorbar(im, label='Depth (m)')
                plt.title('Mining Depth Map')
                plt.axis('off')
                
                # Depth histogram
                plt.subplot(2, 3, 2)
                valid_depths = depth_map[depth_map > 0]
                if len(valid_depths) > 0:
                    plt.hist(valid_depths, bins=50, alpha=0.7, color='red')
                    plt.xlabel('Depth (m)')
                    plt.ylabel('Frequency')
                    plt.title('Depth Distribution')
                
                # Volume statistics pie chart
                plt.subplot(2, 3, 3)
                labels = ['Mining Area', 'Non-Mining Area']
                sizes = [
                    volume_stats.get('mining_area_ha', 0),
                    max(0, 100 - volume_stats.get('mining_area_ha', 0))
                ]
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                plt.title('Area Distribution')
                
                # Volume bar chart
                plt.subplot(2, 3, 4)
                categories = ['Total Volume', 'Simpson Volume']
                volumes = [
                    volume_stats.get('total_volume_m3', 0) / 1000,  # Convert to k m³
                    volume_stats.get('simpsons_volume_m3', 0) / 1000
                ]
                plt.bar(categories, volumes, color=['blue', 'orange'])
                plt.ylabel('Volume (k m³)')
                plt.title('Volume Estimation Comparison')
                
                # Depth statistics
                plt.subplot(2, 3, 5)
                depth_stats = ['Avg Depth', 'Max Depth', 'Min Depth']
                depth_values = [
                    volume_stats.get('average_depth_m', 0),
                    volume_stats.get('max_depth_m', 0),
                    volume_stats.get('min_depth_m', 0)
                ]
                plt.bar(depth_stats, depth_values, color='green')
                plt.ylabel('Depth (m)')
                plt.title('Depth Statistics')
                
                # Summary text
                plt.subplot(2, 3, 6)
                plt.text(0.1, 0.8, f"Total Volume: {volume_stats.get('total_volume_m3', 0):.0f} m³", 
                        transform=plt.gca().transAxes, fontsize=12)
                plt.text(0.1, 0.7, f"Mining Area: {volume_stats.get('mining_area_ha', 0):.2f} ha", 
                        transform=plt.gca().transAxes, fontsize=12)
                plt.text(0.1, 0.6, f"Average Depth: {volume_stats.get('average_depth_m', 0):.2f} m", 
                        transform=plt.gca().transAxes, fontsize=12)
                plt.text(0.1, 0.5, f"Max Depth: {volume_stats.get('max_depth_m', 0):.2f} m", 
                        transform=plt.gca().transAxes, fontsize=12)
                plt.axis('off')
                plt.title('Summary Statistics')
                
                plt.tight_layout()
                
                # Save plot
                plot_path = os.path.join(output_dir, 'depth_volume_analysis.png')
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                logger.info(f"Depth/volume plots saved to: {plot_path}")
                return {'depth_volume_plot': plot_path}
                
        except Exception as e:
            logger.error(f"Error creating depth/volume plots: {e}")
            raise

def main():
    """Example usage of Visualization2D class"""
    
    # Initialize 2D visualization
    viz = Visualization2D(map_center=(28.0, 77.0), zoom_start=12)
    
    print("2D Visualization module ready!")
    print("Features:")
    print("- Interactive folium maps")
    print("- Satellite imagery overlay")
    print("- Mining area visualization")
    print("- NDVI/BSI analysis plots")
    print("- Depth and volume visualization")

if __name__ == "__main__":
    main()
