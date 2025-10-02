# 🚛 Illegal Mining Detection System

A comprehensive system for detecting illegal open-crust mining activities using satellite imagery and Digital Elevation Models (DEM). This project was developed for the Smart India Hackathon.

## 🌟 Features

- **Satellite Data Acquisition**: Download and process Sentinel-2, Sentinel-1, and DEM data using Google Earth Engine
- **Mining Detection**: Rule-based and ML-based detection of mining areas using NDVI and BSI indices
- **Illegal Mining Identification**: Compare detected mining areas with legal boundaries to identify violations
- **Depth & Volume Estimation**: Calculate mining depth and volume using DEM analysis and Simpson's rule
- **2D & 3D Visualization**: Interactive maps and 3D visualizations using Folium, Plotly, and PyVista
- **Automated Reporting**: Generate comprehensive PDF reports with statistics and visualizations
- **Web Interface**: Modern React frontend with interactive maps and real-time analysis

## 🏗️ Architecture

### Backend (Python + FastAPI)
- **Data Acquisition**: Google Earth Engine integration for satellite data
- **Preprocessing**: Image reprojection, clipping, normalization, and DEM processing
- **Mining Detection**: Rule-based detection using spectral indices
- **Illegal Mining Detection**: Spatial analysis and boundary comparison
- **Volume Estimation**: DEM-based depth and volume calculations
- **Visualization**: 2D maps and 3D visualizations
- **Report Generation**: Automated PDF report creation

### Frontend (React + TypeScript)
- **Interactive Maps**: Leaflet-based mapping with satellite imagery
- **Real-time Analysis**: Live analysis results and statistics
- **3D Visualization**: Interactive 3D mining visualizations
- **Report Download**: PDF report generation and download

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Google Earth Engine account
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd illegal-mining-detection
   ```

2. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up Google Earth Engine**
   ```bash
   # Install Google Earth Engine Python API
   pip install earthengine-api
   
   # Authenticate (follow the prompts)
   earthengine authenticate
   ```

4. **Run the backend server**
   ```bash
   python app_simple.py
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Install Node.js dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`

## 📊 Usage

### 1. Data Acquisition
```python
from data_acquisition import DataAcquisition

# Initialize data acquisition
data_acq = DataAcquisition()

# Define area of interest
aoi = {
    "type": "Polygon",
    "coordinates": [[[77.0, 28.0], [77.1, 28.0], [77.1, 28.1], [77.0, 28.1], [77.0, 28.0]]]
}

# Get satellite data
sentinel2 = data_acq.get_sentinel2_data(aoi, "2023-01-01", "2023-12-31")
dem = data_acq.get_dem_data(aoi)
```

### 2. Mining Detection
```python
from mining_detection import MiningDetection

# Initialize mining detection
detector = MiningDetection(ndvi_threshold=0.2, bsi_threshold=0.3)

# Detect mining areas
results = detector.detect_mining_areas(
    image_path="sentinel2_processed.tif",
    output_dir="mining_detection",
    method="rule_based"
)
```

### 3. Illegal Mining Detection
```python
from illegal_mining_detection import IllegalMiningDetection

# Initialize illegal mining detection
illegal_detector = IllegalMiningDetection()

# Detect illegal mining
results = illegal_detector.detect_illegal_mining(
    mining_polygons_path="mining_polygons.shp",
    boundary_path="mining_boundaries.shp",
    output_dir="illegal_detection"
)
```

### 4. Volume Estimation
```python
from depth_volume_estimation import DepthVolumeEstimation

# Initialize volume estimation
estimator = DepthVolumeEstimation()

# Estimate volume
results = estimator.estimate_mining_volume(
    dem_path="dem.tif",
    mining_mask_path="mining_mask.tif",
    output_dir="volume_estimation"
)
```

## 🔧 API Endpoints

### Analysis Endpoints
- `POST /api/analyze` - Run complete analysis
- `POST /api/analyze/quick` - Run quick analysis
- `GET /api/analysis/{analysis_id}` - Get analysis results
- `GET /api/analysis` - List all analyses
- `DELETE /api/analysis/{analysis_id}` - Delete analysis

### File Management
- `POST /api/upload/boundary` - Upload boundary shapefile
- `GET /api/download/report/{analysis_id}` - Download PDF report
- `GET /api/download/visualization/{analysis_id}/{viz_type}` - Download visualizations

### Statistics
- `GET /api/statistics/{analysis_id}` - Get analysis statistics
- `GET /api/status/{analysis_id}` - Get analysis status

## 📈 Analysis Workflow

1. **Data Acquisition**: Download satellite imagery and DEM data
2. **Preprocessing**: Reproject, clip, and normalize data
3. **Mining Detection**: Identify mining areas using spectral indices
4. **Illegal Mining Detection**: Compare with legal boundaries
5. **Volume Estimation**: Calculate depth and volume of mining
6. **Visualization**: Create 2D maps and 3D visualizations
7. **Report Generation**: Generate comprehensive PDF reports

## 🎯 Key Features

### Mining Detection Methods
- **Rule-based**: Uses NDVI and BSI indices for fast detection
- **ML-based**: U-Net segmentation for advanced detection (optional)

### Spectral Indices
- **NDVI**: Normalized Difference Vegetation Index
- **BSI**: Bare Soil Index for bare ground detection

### Volume Estimation
- **Simpson's Rule**: Advanced numerical integration for volume calculation
- **DEM Analysis**: Elevation difference analysis for depth estimation

### Visualization
- **2D Maps**: Interactive Leaflet maps with multiple layers
- **3D Visualization**: PyVista and Plotly 3D surfaces
- **Statistical Plots**: Comprehensive analysis charts

## 📋 Requirements

### Backend Dependencies
- FastAPI 0.104.1
- Rasterio 1.3.9
- GeoPandas 0.14.1
- Google Earth Engine API
- PyVista 0.43.1
- Plotly 5.17.0
- ReportLab 4.0.7

### Frontend Dependencies
- React 19.1.1
- React-Leaflet 4.2.1
- Leaflet 1.9.4
- TypeScript 5.8.3

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🏆 Smart India Hackathon

This project was developed for the Smart India Hackathon 2024, focusing on:
- Detection of illegal mining activities
- Use of satellite imagery and DEM data
- Automated analysis and reporting
- Interactive web interface
- Real-time monitoring capabilities

## 📞 Support

For support and questions, please contact the development team or create an issue in the repository.

## 🔮 Future Enhancements

- Real-time satellite data processing
- Machine learning model improvements
- Mobile application
- Integration with government databases
- Advanced 3D visualization
- Automated alert system
