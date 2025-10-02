"""
Enhanced Visualization Module
Creates detailed 2D and 3D visualizations with dimensions and measurements
"""

import folium
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point
from typing import Dict, Any, List, Tuple, Optional
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedVisualization:
    """Enhanced visualization with detailed measurements and 3D views"""
    
    def __init__(self):
        """Initialize enhanced visualization"""
        logger.info("Enhanced visualization initialized")
    
    def create_detailed_mining_map(self, 
                                 legal_boundaries: gpd.GeoDataFrame,
                                 detected_mining: gpd.GeoDataFrame,
                                 illegal_mining: gpd.GeoDataFrame,
                                 output_path: str) -> str:
        """
        Create detailed mining map with measurements
        
        Args:
            legal_boundaries: Legal mining lease boundaries
            detected_mining: All detected mining areas
            illegal_mining: Illegal mining areas
            output_path: Output HTML file path
            
        Returns:
            str: Path to created map
        """
        try:
            # Calculate map center
            all_geometries = []
            for gdf in [legal_boundaries, detected_mining, illegal_mining]:
                if not gdf.empty:
                    all_geometries.extend(gdf.geometry.tolist())
            
            if not all_geometries:
                raise ValueError("No geometries provided for map creation")
            
            # Get bounds
            bounds = gpd.GeoSeries(all_geometries).total_bounds
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
            
            # Create base map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=12,
                tiles=None
            )
            
            # Add tile layers
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
            
            # Add legal mining boundaries
            if not legal_boundaries.empty:
                for idx, row in legal_boundaries.iterrows():
                    # Create popup with detailed info
                    popup_html = f"""
                    <div style="width: 250px;">
                        <h4>Legal Mining Lease</h4>
                        <p><b>Lease ID:</b> {row.get('lease_id', 'N/A')}</p>
                        <p><b>Name:</b> {row.get('lease_name', 'N/A')}</p>
                        <p><b>State:</b> {row.get('state', 'N/A')}</p>
                        <p><b>District:</b> {row.get('district', 'N/A')}</p>
                        <p><b>Mineral:</b> {row.get('mineral', 'N/A')}</p>
                        <p><b>Area:</b> {row.get('area_hectares', 0):.2f} hectares</p>
                        <p><b>Valid From:</b> {row.get('valid_from', 'N/A')}</p>
                        <p><b>Valid To:</b> {row.get('valid_to', 'N/A')}</p>
                    </div>
                    """
                    
                    folium.GeoJson(
                        row.geometry.__geo_interface__,
                        style_function=lambda feature: {
                            'fillColor': 'green',
                            'color': 'darkgreen',
                            'weight': 3,
                            'fillOpacity': 0.3
                        },
                        popup=folium.Popup(popup_html, parse_html=True),
                        name='Legal Mining Leases'
                    ).add_to(m)
            
            # Add detected mining areas
            if not detected_mining.empty:
                for idx, row in detected_mining.iterrows():
                    popup_html = f"""
                    <div style="width: 200px;">
                        <h4>Detected Mining Area</h4>
                        <p><b>Area:</b> {row.get('area_ha', 0):.2f} hectares</p>
                        <p><b>Status:</b> Detected</p>
                    </div>
                    """
                    
                    folium.GeoJson(
                        row.geometry.__geo_interface__,
                        style_function=lambda feature: {
                            'fillColor': 'blue',
                            'color': 'darkblue',
                            'weight': 2,
                            'fillOpacity': 0.5
                        },
                        popup=folium.Popup(popup_html, parse_html=True),
                        name='Detected Mining Areas'
                    ).add_to(m)
            
            # Add illegal mining areas with detailed measurements
            if not illegal_mining.empty:
                for idx, row in illegal_mining.iterrows():
                    # Calculate dimensions
                    bounds = row.geometry.bounds
                    width = bounds[2] - bounds[0]  # longitude difference
                    height = bounds[3] - bounds[1]  # latitude difference
                    
                    # Convert to approximate meters (rough conversion)
                    width_m = width * 111000 * np.cos(np.radians(bounds[1]))
                    height_m = height * 111000
                    
                    popup_html = f"""
                    <div style="width: 300px;">
                        <h4 style="color: red;">⚠️ ILLEGAL MINING AREA</h4>
                        <p><b>Area:</b> {row.get('area_ha', 0):.2f} hectares</p>
                        <p><b>Dimensions:</b> {width_m:.0f}m × {height_m:.0f}m</p>
                        <p><b>Perimeter:</b> {row.geometry.length * 111000:.0f} meters</p>
                        <p><b>Status:</b> <span style="color: red;">ILLEGAL</span></p>
                        <p><b>Action Required:</b> Immediate enforcement</p>
                    </div>
                    """
                    
                    folium.GeoJson(
                        row.geometry.__geo_interface__,
                        style_function=lambda feature: {
                            'fillColor': 'red',
                            'color': 'darkred',
                            'weight': 4,
                            'fillOpacity': 0.7
                        },
                        popup=folium.Popup(popup_html, parse_html=True),
                        name='Illegal Mining Areas'
                    ).add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Add legend
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 200px; height: 120px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px">
            <h4>Legend</h4>
            <p><i class="fa fa-square" style="color:green"></i> Legal Mining Leases</p>
            <p><i class="fa fa-square" style="color:blue"></i> Detected Mining Areas</p>
            <p><i class="fa fa-square" style="color:red"></i> Illegal Mining Areas</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Save map
            m.save(output_path)
            
            logger.info(f"Detailed mining map saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating detailed mining map: {e}")
            raise
    
    def create_3d_mining_visualization(self, 
                                     legal_boundaries: gpd.GeoDataFrame,
                                     illegal_mining: gpd.GeoDataFrame,
                                     dem_data: Optional[np.ndarray] = None,
                                     output_path: str) -> str:
        """
        Create 3D visualization of mining areas
        
        Args:
            legal_boundaries: Legal mining boundaries
            illegal_mining: Illegal mining areas
            dem_data: DEM elevation data (optional)
            output_path: Output HTML file path
            
        Returns:
            str: Path to created visualization
        """
        try:
            fig = go.Figure()
            
            # Add legal mining areas
            if not legal_boundaries.empty:
                for idx, row in legal_boundaries.iterrows():
                    # Get coordinates
                    coords = list(row.geometry.exterior.coords)
                    x_coords = [coord[0] for coord in coords]
                    y_coords = [coord[1] for coord in coords]
                    z_coords = [0] * len(coords)  # Ground level
                    
                    fig.add_trace(go.Scatter3d(
                        x=x_coords,
                        y=y_coords,
                        z=z_coords,
                        mode='lines',
                        line=dict(color='green', width=5),
                        name=f'Legal Lease: {row.get("lease_id", "Unknown")}',
                        hovertemplate=f'<b>Legal Mining Lease</b><br>' +
                                    f'ID: {row.get("lease_id", "N/A")}<br>' +
                                    f'Area: {row.get("area_hectares", 0):.2f} ha<br>' +
                                    f'Mineral: {row.get("mineral", "N/A")}<extra></extra>'
                    ))
            
            # Add illegal mining areas
            if not illegal_mining.empty:
                for idx, row in illegal_mining.iterrows():
                    # Get coordinates
                    coords = list(row.geometry.exterior.coords)
                    x_coords = [coord[0] for coord in coords]
                    y_coords = [coord[1] for coord in coords]
                    z_coords = [0] * len(coords)  # Ground level
                    
                    # Calculate area for hover info
                    area_ha = row.get('area_ha', 0)
                    
                    fig.add_trace(go.Scatter3d(
                        x=x_coords,
                        y=y_coords,
                        z=z_coords,
                        mode='lines',
                        line=dict(color='red', width=8),
                        name=f'Illegal Mining Area {idx+1}',
                        hovertemplate=f'<b>⚠️ ILLEGAL MINING AREA</b><br>' +
                                    f'Area: {area_ha:.2f} hectares<br>' +
                                    f'Status: ILLEGAL<br>' +
                                    f'Action Required: Immediate enforcement<extra></extra>'
                    ))
                    
                    # Add filled area for illegal mining
                    fig.add_trace(go.Scatter3d(
                        x=x_coords,
                        y=y_coords,
                        z=z_coords,
                        mode='markers',
                        marker=dict(
                            size=3,
                            color='red',
                            opacity=0.6
                        ),
                        name=f'Illegal Area Fill {idx+1}',
                        showlegend=False
                    ))
            
            # Update layout
            fig.update_layout(
                title='3D Mining Areas Visualization',
                scene=dict(
                    xaxis_title='Longitude',
                    yaxis_title='Latitude',
                    zaxis_title='Elevation (m)',
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.5)
                    ),
                    bgcolor='lightblue'
                ),
                width=1000,
                height=800
            )
            
            # Save as HTML
            fig.write_html(output_path)
            
            logger.info(f"3D mining visualization saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating 3D visualization: {e}")
            raise
    
    def create_dimensions_report(self, 
                               illegal_mining: gpd.GeoDataFrame,
                               output_path: str) -> str:
        """
        Create detailed dimensions report for illegal mining areas
        
        Args:
            illegal_mining: Illegal mining areas
            output_path: Output HTML file path
            
        Returns:
            str: Path to created report
        """
        try:
            if illegal_mining.empty:
                # Create empty report
                html_content = """
                <html>
                <head><title>Illegal Mining Dimensions Report</title></head>
                <body>
                    <h1>Illegal Mining Dimensions Report</h1>
                    <p>No illegal mining areas detected.</p>
                </body>
                </html>
                """
            else:
                # Create detailed report
                html_content = f"""
                <html>
                <head>
                    <title>Illegal Mining Dimensions Report</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        .illegal {{ color: red; font-weight: bold; }}
                        .warning {{ background-color: #ffebee; }}
                    </style>
                </head>
                <body>
                    <h1>🚨 Illegal Mining Dimensions Report</h1>
                    <p><strong>Report Generated:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Total Illegal Areas:</strong> {len(illegal_mining)}</p>
                    
                    <h2>Detailed Measurements</h2>
                    <table>
                        <tr>
                            <th>Area ID</th>
                            <th>Area (hectares)</th>
                            <th>Length (m)</th>
                            <th>Width (m)</th>
                            <th>Perimeter (m)</th>
                            <th>Status</th>
                        </tr>
                """
                
                for idx, row in illegal_mining.iterrows():
                    # Calculate dimensions
                    bounds = row.geometry.bounds
                    width = bounds[2] - bounds[0]
                    height = bounds[3] - bounds[1]
                    
                    # Convert to meters (approximate)
                    width_m = width * 111000 * np.cos(np.radians(bounds[1]))
                    height_m = height * 111000
                    perimeter_m = row.geometry.length * 111000
                    area_ha = row.get('area_ha', 0)
                    
                    html_content += f"""
                        <tr class="warning">
                            <td>Illegal Area {idx+1}</td>
                            <td>{area_ha:.2f}</td>
                            <td>{height_m:.0f}</td>
                            <td>{width_m:.0f}</td>
                            <td>{perimeter_m:.0f}</td>
                            <td class="illegal">ILLEGAL</td>
                        </tr>
                    """
                
                html_content += """
                    </table>
                    
                    <h2>Summary Statistics</h2>
                    <ul>
                """
                
                # Add summary statistics
                total_area = illegal_mining['area_ha'].sum()
                avg_area = illegal_mining['area_ha'].mean()
                max_area = illegal_mining['area_ha'].max()
                
                html_content += f"""
                        <li><strong>Total Illegal Area:</strong> {total_area:.2f} hectares</li>
                        <li><strong>Average Area per Violation:</strong> {avg_area:.2f} hectares</li>
                        <li><strong>Largest Illegal Area:</strong> {max_area:.2f} hectares</li>
                    </ul>
                    
                    <h2>Recommended Actions</h2>
                    <ul>
                        <li>Immediate site inspection required</li>
                        <li>Issue stop-work orders</li>
                        <li>Initiate legal proceedings</li>
                        <li>Calculate environmental damage assessment</li>
                        <li>Implement monitoring system</li>
                    </ul>
                </body>
                </html>
                """
            
            # Save HTML report
            with open(output_path, 'w') as f:
                f.write(html_content)
            
            logger.info(f"Dimensions report saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating dimensions report: {e}")
            raise

def main():
    """Example usage of EnhancedVisualization class"""
    
    # Initialize enhanced visualization
    viz = EnhancedVisualization()
    
    print("Enhanced Visualization module ready!")
    print("Features:")
    print("- Detailed 2D maps with measurements")
    print("- 3D mining area visualizations")
    print("- Dimensions reports with statistics")
    print("- Interactive popups with lease information")

if __name__ == "__main__":
    main()
