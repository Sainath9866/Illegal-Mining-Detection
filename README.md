# Illegal Mining Detection System

A comprehensive end-to-end system for detecting illegal open-crust mining activities using satellite imagery and DEM data, built for the Smart India Hackathon.

## 🎯 Overview

This system provides:
- **Real satellite data acquisition** from Sentinel-2, Sentinel-1 SAR, and DEM sources via Google Earth Engine
- **Advanced spectral analysis** using NDVI, BSI, NDBI, and other indices
- **Spatial overlay analysis** to compare detected mining with legal lease boundaries
- **Interactive 2D visualization** with Leaflet and radar-style location markers
- **Automated PDF report generation** with color-coded severity levels
- **RESTful API** with FastAPI for easy integration
- **Modern React frontend** with beautiful UI and animations

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Data Sources  │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (GEE/SAR)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Processing    │
                       │   Pipeline      │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Google Earth Engine account
- Google Cloud Project with Earth Engine API enabled

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd illegal-mining-detection
```

2. **Install backend dependencies**
```bash
cd backend
pip install -r requirements.txt
```

3. **Install frontend dependencies**
```bash
cd ../frontend
npm install
```

4. **Set up Google Earth Engine**
```bash
# Install GEE CLI
pip install earthengine-api

# Authenticate (requires GEE account)
earthengine authenticate

# Set up gcloud (if needed)
brew install google-cloud-sdk
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable earthengine.googleapis.com
```

5. **Create .env file in backend/**
```bash
EE_PROJECT_ID=your-project-id
```

### Running the Application

1. **Start the backend server**
```bash
cd backend
python app.py
```

2. **Start the frontend development server**
```bash
cd frontend
npm run dev
```

3. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📊 Core Modules

### 1. Data Acquisition (`gee_utils.py`)
- Downloads Sentinel-2 multispectral imagery from Google Earth Engine
- Fetches DEM data (SRTM/ALOS)
- Handles cloud masking and composite generation
- Direct download via GEE getDownloadURL

### 2. Preprocessing (`preprocess.py`)
- Reprojects rasters to target CRS
- Normalizes spectral bands
- Fills DEM voids and applies smoothing

### 3. Mining Detection (`detect_indices.py`)
- Calculates spectral indices (NDVI, BSI, NDBI, NDWI, SAVI, EVI, NBR)
- Applies threshold-based classification
- Performs morphological operations for noise reduction
- Converts detection masks to vector polygons with properties

### 4. Illegal Mining Detection (`compare_with_lease.py`)
- Loads legal lease boundaries from various formats
- Performs spatial overlay analysis
- Classifies areas as legal/illegal/mixed
- Calculates confidence scores and statistics

## 🔧 API Endpoints

### Demo Endpoints (Current Implementation)

- `GET /api/mining-boundaries` - Get 12 demo legal mining leases across India
- `GET /api/satellite-data` - Get satellite-detected mining areas
- `POST /api/analyze/quick` - Quick analysis workflow
- `POST /api/analyze/illegal-mining-detection` - Complete detection analysis
- `GET /api/illegal-mining-results/{analysis_id}` - Get analysis results

### Utility Endpoints

- `GET /api/health` - Health check
- `GET /` - API information

## 🎨 Frontend Features

- **Empty Map on Load**: No data shown initially, clean interface
- **Beautiful Blur Popup**: Color legend explaining zones after clicking analysis
- **Radar/Sonar Rings**: Expanding circular rings at mining locations (not balloons!)
- **Zoom-Dependent Display**: Circle markers when zoomed out, detailed polygons when zoomed in
- **Color-Coded Zones**:
  - 🟢 Green: Legal mining boundaries
  - 🔴 Red: Critical illegal violations (4+ locations)
  - 🟠 Orange: Warning zones (4+ locations)
  - 🔵 Blue: Satellite detections
- **3D Visualization**: Interactive 3D terrain models with Plotly
- **PDF Reports**: Color-coded PDF generation via browser print dialog

## 🔍 Detection Algorithm

### Spectral Indices Used

1. **NDVI** (Normalized Difference Vegetation Index): `(NIR - Red) / (NIR + Red)` < 0.2
2. **BSI** (Bare Soil Index): `((SWIR + Red) - (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))` > 0.3
3. **NDBI** (Normalized Difference Built-up Index): `(SWIR - NIR) / (SWIR + NIR)` > 0.1
4. **NDWI** (Normalized Difference Water Index): `(Green - NIR) / (Green + NIR)` < 0.2

### Classification Logic

Mining areas are detected when **at least 4 out of 7 conditions** are met.

## 📊 Output Formats

### Vector Data
- **GeoJSON**: Web-compatible format with detailed properties
- **Shapefile**: GIS standard format

### Reports
- **PDF**: Comprehensive color-coded analysis report with severity badges
- **Interactive Popups**: Detailed information on map clicks

## 🛠️ Configuration

### Spectral Thresholds
```python
thresholds = {
    'ndvi': 0.2,      # Vegetation threshold
    'bsi': 0.3,       # Bare soil threshold
    'ndbi': 0.1,      # Built-up threshold
    'ndwi': 0.2,      # Water threshold
    'min_area_ha': 0.1,  # Minimum detection area
    'max_area_ha': 1000, # Maximum detection area
}
```

## 📝 License

This project is developed for the Smart India Hackathon and follows the competition guidelines.

## 🔮 Future Enhancements

- [ ] Integration with real government WFS/WMS endpoints for legal boundaries
- [ ] Temporal change detection using multi-date imagery
- [ ] Depth and volume estimation using DEM differencing
- [ ] Machine learning-based detection
- [ ] Real-time satellite data streaming
- [ ] Cloud deployment with Docker
- [ ] Advanced 3D visualization improvements
- [ ] Automated alert system

---

**Built with ❤️ for Smart India Hackathon 2025**
