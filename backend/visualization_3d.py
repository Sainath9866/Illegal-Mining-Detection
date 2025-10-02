"""
3D Visualization Module for Illegal Mining Detection
Creates 3D visualizations using pyvista and plotly
"""

import pyvista as pv
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import rasterio
import geopandas as gpd
import logging
from typing import Dict, Any, List, Tuple, Optional
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Visualization3D:
    """Handles 3D visualization of mining detection results"""
    
    def __init__(self):
        """Initialize 3D visualization"""
        logger.info("3D visualization initialized")
    
    def create_dem_surface(self, 
                          dem_path: str, 
                          output_path: str) -> str:
        """
        Create 3D surface from DEM data using PyVista
        
        Args:
            dem_path: Path to DEM file
            output_path: Path to save 3D surface
            
        Returns:
            str: Path to saved 3D surface
        """
        try:
            with rasterio.open(dem_path) as src:
                # Read DEM data
                dem_data = src.read(1).astype(np.float32)
                transform = src.transform
                
                # Create coordinate arrays
                rows, cols = dem_data.shape
                x = np.linspace(transform.c, transform.c + cols * transform.a, cols)
                y = np.linspace(transform.f, transform.f + rows * transform.e, rows)
                X, Y = np.meshgrid(x, y)
                
                # Create structured grid
                grid = pv.StructuredGrid()
                grid.points = np.column_stack([X.ravel(), Y.ravel(), dem_data.ravel()])
                grid.dimensions = [cols, rows, 1]
                
                # Add elevation data
                grid['elevation'] = dem_data.ravel()
                
                # Save surface
                grid.save(output_path)
                
                logger.info(f"3D DEM surface saved to: {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error creating DEM surface: {e}")
            raise
    
    def create_mining_3d_visualization(self, 
                                      dem_path: str,
                                      mining_mask_path: str,
                                      depth_map_path: str,
                                      output_path: str) -> str:
        """
        Create 3D visualization of mining areas with depth
        
        Args:
            dem_path: Path to DEM file
            mining_mask_path: Path to mining mask
            depth_map_path: Path to depth map
            output_path: Path to save 3D visualization
            
        Returns:
            str: Path to saved visualization
        """
        try:
            # Load data
            with rasterio.open(dem_path) as dem_src:
                dem_data = dem_src.read(1).astype(np.float32)
                transform = dem_src.transform
                crs = dem_src.crs
            
            with rasterio.open(mining_mask_path) as mask_src:
                mining_mask = mask_src.read(1).astype(bool)
            
            with rasterio.open(depth_map_path) as depth_src:
                depth_data = depth_src.read(1).astype(np.float32)
            
            # Create coordinate arrays
            rows, cols = dem_data.shape
            x = np.linspace(transform.c, transform.c + cols * transform.a, cols)
            y = np.linspace(transform.f, transform.f + rows * transform.e, rows)
            X, Y = np.meshgrid(x, y)
            
            # Create base surface
            base_surface = pv.StructuredGrid()
            base_surface.points = np.column_stack([X.ravel(), Y.ravel(), dem_data.ravel()])
            base_surface.dimensions = [cols, rows, 1]
            base_surface['elevation'] = dem_data.ravel()
            
            # Create mining surface (lowered by depth)
            mining_surface = base_surface.copy()
            mining_elevation = dem_data - depth_data
            mining_surface.points[:, 2] = mining_elevation.ravel()
            mining_surface['elevation'] = mining_elevation.ravel()
            mining_surface['mining_mask'] = mining_mask.ravel()
            mining_surface['depth'] = depth_data.ravel()
            
            # Create plotter
            plotter = pv.Plotter()
            
            # Add base surface
            plotter.add_mesh(
                base_surface,
                scalars='elevation',
                cmap='terrain',
                opacity=0.7,
                show_scalar_bar=True,
                scalar_bar_args={'title': 'Elevation (m)'}
            )
            
            # Add mining areas
            mining_areas = mining_surface.extract_points(mining_surface['mining_mask'] > 0)
            if len(mining_areas.points) > 0:
                plotter.add_mesh(
                    mining_areas,
                    scalars='depth',
                    cmap='Reds',
                    show_scalar_bar=True,
                    scalar_bar_args={'title': 'Mining Depth (m)'}
                )
            
            # Add wireframe for mining boundaries
            mining_boundary = mining_surface.extract_surface().extract_feature_edges()
            if len(mining_boundary.points) > 0:
                plotter.add_mesh(
                    mining_boundary,
                    color='red',
                    line_width=3,
                    opacity=0.8
                )
            
            # Set camera position
            plotter.camera_position = 'isometric'
            plotter.add_axes()
            
            # Save visualization
            plotter.screenshot(output_path)
            plotter.close()
            
            logger.info(f"3D mining visualization saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating 3D mining visualization: {e}")
            raise
    
    def create_plotly_3d_surface(self, 
                                dem_path: str,
                                mining_mask_path: str,
                                depth_map_path: str,
                                output_path: str) -> str:
        """
        Create interactive 3D surface using Plotly
        
        Args:
            dem_path: Path to DEM file
            mining_mask_path: Path to mining mask
            depth_map_path: Path to depth map
            output_path: Path to save HTML file
            
        Returns:
            str: Path to saved HTML file
        """
        try:
            # Load data
            with rasterio.open(dem_path) as dem_src:
                dem_data = dem_src.read(1).astype(np.float32)
                transform = dem_src.transform
            
            with rasterio.open(mining_mask_path) as mask_src:
                mining_mask = mask_src.read(1).astype(bool)
            
            with rasterio.open(depth_map_path) as depth_src:
                depth_data = depth_src.read(1).astype(np.float32)
            
            # Create coordinate arrays
            rows, cols = dem_data.shape
            x = np.linspace(transform.c, transform.c + cols * transform.a, cols)
            y = np.linspace(transform.f, transform.f + rows * transform.e, rows)
            X, Y = np.meshgrid(x, y)
            
            # Create base surface
            base_surface = go.Surface(
                x=X, y=Y, z=dem_data,
                colorscale='terrain',
                name='Terrain',
                opacity=0.7,
                showscale=True,
                colorbar=dict(title="Elevation (m)")
            )
            
            # Create mining surface
            mining_elevation = dem_data - depth_data
            mining_surface = go.Surface(
                x=X, y=Y, z=mining_elevation,
                colorscale='Reds',
                name='Mining Areas',
                opacity=0.8,
                showscale=True,
                colorbar=dict(title="Mining Depth (m)"),
                visible=False
            )
            
            # Create figure
            fig = go.Figure(data=[base_surface, mining_surface])
            
            # Update layout
            fig.update_layout(
                title='3D Mining Detection Visualization',
                scene=dict(
                    xaxis_title='Longitude',
                    yaxis_title='Latitude',
                    zaxis_title='Elevation (m)',
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.5)
                    )
                ),
                updatemenus=[
                    dict(
                        type="buttons",
                        direction="left",
                        buttons=list([
                            dict(
                                args=[{"visible": [True, False]}],
                                label="Terrain Only",
                                method="update"
                            ),
                            dict(
                                args=[{"visible": [False, True]}],
                                label="Mining Areas",
                                method="update"
                            ),
                            dict(
                                args=[{"visible": [True, True]}],
                                label="Both",
                                method="update"
                            )
                        ]),
                        pad={"r": 10, "t": 10},
                        showactive=True,
                        x=0.01,
                        xanchor="left",
                        y=1.02,
                        yanchor="top"
                    )
                ]
            )
            
            # Save as HTML
            fig.write_html(output_path)
            
            logger.info(f"Interactive 3D surface saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating Plotly 3D surface: {e}")
            raise
    
    def create_volume_visualization(self, 
                                   volume_stats: Dict[str, Any],
                                   output_path: str) -> str:
        """
        Create 3D volume visualization
        
        Args:
            volume_stats: Volume statistics
            output_path: Path to save visualization
            
        Returns:
            str: Path to saved visualization
        """
        try:
            # Create 3D bar chart
            categories = ['Total Volume', 'Simpson Volume']
            volumes = [
                volume_stats.get('total_volume_m3', 0) / 1000,  # Convert to k m³
                volume_stats.get('simpsons_volume_m3', 0) / 1000
            ]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=categories,
                    y=volumes,
                    marker_color=['blue', 'orange'],
                    text=[f'{v:.1f}k m³' for v in volumes],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title='Mining Volume Estimation',
                xaxis_title='Volume Type',
                yaxis_title='Volume (k m³)',
                showlegend=False
            )
            
            # Save as HTML
            fig.write_html(output_path)
            
            logger.info(f"Volume visualization saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating volume visualization: {e}")
            raise
    
    def create_depth_profile(self, 
                           depth_map_path: str,
                           output_path: str) -> str:
        """
        Create depth profile visualization
        
        Args:
            depth_map_path: Path to depth map
            output_path: Path to save profile
            
        Returns:
            str: Path to saved profile
        """
        try:
            with rasterio.open(depth_map_path) as src:
                depth_data = src.read(1).astype(np.float32)
                transform = src.transform
                
                # Create coordinate arrays
                rows, cols = depth_data.shape
                x = np.linspace(transform.c, transform.c + cols * transform.a, cols)
                y = np.linspace(transform.f, transform.f + rows * transform.e, rows)
                X, Y = np.meshgrid(x, y)
                
                # Create depth profile along center line
                center_row = rows // 2
                profile_x = X[center_row, :]
                profile_depth = depth_data[center_row, :]
                
                # Create figure
                fig = go.Figure()
                
                # Add depth profile
                fig.add_trace(go.Scatter(
                    x=profile_x,
                    y=profile_depth,
                    mode='lines+markers',
                    name='Depth Profile',
                    line=dict(color='red', width=3),
                    marker=dict(size=4)
                ))
                
                # Add zero line
                fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                
                fig.update_layout(
                    title='Mining Depth Profile',
                    xaxis_title='Longitude',
                    yaxis_title='Depth (m)',
                    showlegend=True
                )
                
                # Save as HTML
                fig.write_html(output_path)
                
                logger.info(f"Depth profile saved to: {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error creating depth profile: {e}")
            raise
    
    def create_comprehensive_3d_dashboard(self, 
                                        dem_path: str,
                                        mining_mask_path: str,
                                        depth_map_path: str,
                                        volume_stats: Dict[str, Any],
                                        output_dir: str) -> Dict[str, str]:
        """
        Create comprehensive 3D dashboard with all visualizations
        
        Args:
            dem_path: Path to DEM file
            mining_mask_path: Path to mining mask
            depth_map_path: Path to depth map
            volume_stats: Volume statistics
            output_dir: Output directory
            
        Returns:
            Dict[str, str]: Paths to created visualizations
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            output_paths = {}
            
            # Create PyVista 3D visualization
            pv_output = os.path.join(output_dir, 'mining_3d_pyvista.png')
            self.create_mining_3d_visualization(
                dem_path, mining_mask_path, depth_map_path, pv_output
            )
            output_paths['pyvista_3d'] = pv_output
            
            # Create Plotly interactive 3D surface
            plotly_output = os.path.join(output_dir, 'mining_3d_interactive.html')
            self.create_plotly_3d_surface(
                dem_path, mining_mask_path, depth_map_path, plotly_output
            )
            output_paths['plotly_3d'] = plotly_output
            
            # Create volume visualization
            volume_output = os.path.join(output_dir, 'volume_visualization.html')
            self.create_volume_visualization(volume_stats, volume_output)
            output_paths['volume_viz'] = volume_output
            
            # Create depth profile
            profile_output = os.path.join(output_dir, 'depth_profile.html')
            self.create_depth_profile(depth_map_path, profile_output)
            output_paths['depth_profile'] = profile_output
            
            logger.info("Comprehensive 3D dashboard created successfully!")
            return output_paths
            
        except Exception as e:
            logger.error(f"Error creating comprehensive 3D dashboard: {e}")
            raise

def main():
    """Example usage of Visualization3D class"""
    
    # Initialize 3D visualization
    viz = Visualization3D()
    
    print("3D Visualization module ready!")
    print("Features:")
    print("- PyVista 3D surface visualization")
    print("- Interactive Plotly 3D surfaces")
    print("- Volume visualization")
    print("- Depth profile analysis")
    print("- Comprehensive 3D dashboard")

if __name__ == "__main__":
    main()
