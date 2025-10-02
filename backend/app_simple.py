"""
Simplified FastAPI Backend for Illegal Mining Detection System
Works without heavy geospatial dependencies for demo purposes
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Import live government API and simplified illegal mining pipeline
from live_government_api import get_live_mining_data
from simple_illegal_mining_pipeline import run_simple_illegal_mining_detection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Illegal Mining Detection API",
    description="API for detecting illegal mining activities using satellite imagery",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AOIRequest(BaseModel):
    """Area of Interest request model"""
    geometry: Dict[str, Any]
    name: str

class AnalysisRequest(BaseModel):
    """Analysis request model"""
    aoi: AOIRequest
    start_date: str
    end_date: str
    boundary_file: str
    analysis_name: str

class QuickAnalysisRequest(BaseModel):
    """Quick analysis request model"""
    aoi: AOIRequest
    boundary_file: str
    analysis_name: str

class AnalysisResponse(BaseModel):
    """Analysis response model"""
    analysis_id: str
    status: str
    message: str
    results: Optional[Dict[str, Any]] = None

# Global storage for analysis results
analysis_results = {}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Illegal Mining Detection API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/analyze/quick", response_model=AnalysisResponse)
async def run_quick_analysis(request: QuickAnalysisRequest):
    """
    Run quick illegal mining detection analysis (demo version)
    
    Args:
        request: Quick analysis request with AOI and boundary file
        
    Returns:
        AnalysisResponse: Analysis results
    """
    try:
        logger.info(f"Starting quick analysis: {request.analysis_name}")
        
        # Create mock analysis results for demo
        analysis_id = f"{request.analysis_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Mock statistics
        mock_results = {
            "statistics": {
                "legal_mining": {
                    "count": 5,
                    "area_ha": 12.5,
                    "percentage": 75.0
                },
                "illegal_mining": {
                    "count": 2,
                    "area_ha": 4.2,
                    "percentage": 25.0
                },
                "total_mining": {
                    "count": 7,
                    "area_ha": 16.7,
                    "percentage": 100.0
                }
            },
            "volume_estimation": {
                "total_volume_m3": 125000.0,
                "average_depth_m": 3.2,
                "max_depth_m": 8.5,
                "mining_area_ha": 16.7
            }
        }
        
        # Store results
        analysis_results[analysis_id] = {
            "analysis_id": analysis_id,
            "analysis_name": request.analysis_name,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "results": mock_results
        }
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            message="Quick analysis completed successfully (demo mode)",
            results=mock_results
        )
        
    except Exception as e:
        logger.error(f"Error in quick analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """
    Get analysis results by ID
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        Dict: Analysis results
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis_results[analysis_id]

@app.get("/api/analysis")
async def list_analyses():
    """
    List all analyses
    
    Returns:
        List: List of analysis IDs and basic info
    """
    analyses = []
    for analysis_id, results in analysis_results.items():
        analyses.append({
            "analysis_id": analysis_id,
            "analysis_name": results.get("analysis_name", "Unknown"),
            "timestamp": results.get("timestamp", "Unknown"),
            "status": results.get("status", "Unknown")
        })
    
    return {"analyses": analyses}

@app.delete("/api/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """
    Delete analysis by ID
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        Dict: Deletion status
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    del analysis_results[analysis_id]
    return {"message": f"Analysis {analysis_id} deleted successfully"}

@app.post("/api/upload/boundary")
async def upload_boundary_file(file: UploadFile = File(...)):
    """
    Upload mining boundary shapefile (demo version)
    
    Args:
        file: Uploaded shapefile
        
    Returns:
        Dict: Upload status and file path
    """
    try:
        # Create uploads directory
        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save uploaded file
        file_path = os.path.join(uploads_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Boundary file uploaded: {file_path}")
        
        return {
            "message": "Boundary file uploaded successfully",
            "file_path": file_path,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Error uploading boundary file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/report/{analysis_id}")
async def download_report(analysis_id: str):
    """
    Download analysis report (demo version)
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        FileResponse: PDF report file
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Create a simple text report for demo
    results = analysis_results[analysis_id]
    report_content = f"""
Illegal Mining Detection Report
==============================

Analysis ID: {analysis_id}
Analysis Name: {results.get('analysis_name', 'Unknown')}
Timestamp: {results.get('timestamp', 'Unknown')}

Statistics:
- Legal Mining: {results['results']['statistics']['legal_mining']['area_ha']} ha ({results['results']['statistics']['legal_mining']['percentage']}%)
- Illegal Mining: {results['results']['statistics']['illegal_mining']['area_ha']} ha ({results['results']['statistics']['illegal_mining']['percentage']}%)
- Total Mining: {results['results']['statistics']['total_mining']['area_ha']} ha

Volume Estimation:
- Total Volume: {results['results']['volume_estimation']['total_volume_m3']:,.0f} m³
- Average Depth: {results['results']['volume_estimation']['average_depth_m']} m
- Max Depth: {results['results']['volume_estimation']['max_depth_m']} m

This is a demo report generated by the Illegal Mining Detection System.
"""
    
    # Save report
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, f"report_{analysis_id}.txt")
    
    with open(report_path, "w") as f:
        f.write(report_content)
    
    return FileResponse(
        path=report_path,
        filename=f"mining_report_{analysis_id}.txt",
        media_type="text/plain"
    )

@app.get("/api/statistics/{analysis_id}")
async def get_analysis_statistics(analysis_id: str):
    """
    Get analysis statistics

    Args:
        analysis_id: Analysis ID

    Returns:
        Dict: Analysis statistics
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")

    results = analysis_results[analysis_id]

    # Extract statistics
    stats = {
        "mining_detection": {},
        "illegal_mining": results.get("results", {}).get("statistics", {}),
        "volume_estimation": results.get("results", {}).get("volume_estimation", {})
    }

    return stats

@app.post("/api/analyze/illegal-mining-detection")
async def run_illegal_mining_analysis(background_tasks: BackgroundTasks):
    """
    Run complete illegal mining detection analysis
    Compares satellite data with official government boundaries
    
    Returns:
        Dict: Complete analysis results with red and orange zones
    """
    try:
        logger.info("🚀 Starting complete illegal mining detection analysis...")
        
        # Run the complete analysis in background
        analysis_id = f"illegal_mining_{datetime.now().timestamp()}"
        
        # Store initial status
        analysis_results[analysis_id] = {
            "analysis_id": analysis_id,
            "status": "processing",
            "message": "Illegal mining detection analysis initiated...",
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "illegal_mining_detection"
        }
        
        # Run analysis in background
        background_tasks.add_task(
            _run_illegal_mining_analysis_task, analysis_id
        )
        
        return {
            "analysis_id": analysis_id,
            "status": "processing",
            "message": "Illegal mining detection analysis initiated. This may take several minutes.",
            "timestamp": datetime.now().isoformat(),
            "estimated_completion_time": "5-10 minutes"
        }
        
    except Exception as e:
        logger.error(f"Error starting illegal mining analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_illegal_mining_analysis_task(analysis_id: str):
    """Background task for illegal mining analysis"""
    try:
        logger.info(f"Running illegal mining analysis for {analysis_id}")
        
        # Run the simplified illegal mining detection pipeline
        results = await run_simple_illegal_mining_detection()
        
        # Update analysis results
        analysis_results[analysis_id].update({
            "status": "completed",
            "message": "Illegal mining detection analysis completed successfully.",
            "timestamp": datetime.now().isoformat(),
            "results": results
        })
        
        logger.info(f"Illegal mining analysis {analysis_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in illegal mining analysis {analysis_id}: {e}")
        analysis_results[analysis_id].update({
            "status": "failed",
            "message": f"Analysis failed: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        })

@app.get("/api/illegal-mining-results/{analysis_id}")
async def get_illegal_mining_results(analysis_id: str):
    """
    Get illegal mining detection results
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        Dict: Illegal mining detection results
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    results = analysis_results[analysis_id]
    
    if results["status"] != "completed":
        return {
            "analysis_id": analysis_id,
            "status": results["status"],
            "message": results["message"],
            "timestamp": results["timestamp"]
        }
    
    # Extract key results for frontend
    analysis_data = results.get("results", {})
    
    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "timestamp": results["timestamp"],
        "analysis_summary": analysis_data.get("analysis_summary", {}),
        "violation_zones": analysis_data.get("visualization_data", {}),
        "state_breakdown": analysis_data.get("state_breakdown", {}),
        "priority_actions": analysis_data.get("priority_actions", []),
        "recommendations": analysis_data.get("recommendations", [])
    }

# Live government API will be called as needed

@app.get("/api/mining-boundaries")
async def get_mining_boundaries(strict: bool = True):
    """
    Get legal mining lease boundaries from live government APIs
    
    Returns:
        Dict: Live mining boundaries data from multiple government sources
    """
    try:
        logger.info("🔄 Fetching live mining boundaries from government APIs...")
        
        # Get live data from multiple government sources (strict: only real live)
        from live_government_api import LiveGovernmentAPI
        api = LiveGovernmentAPI()
        live_data = await api.fetch_live_mining_leases(strict=strict)
        boundaries = live_data['boundaries']
        summary = live_data['summary']
        
        logger.info(f"✅ Fetched {len(boundaries['features'])} live mining boundaries from {summary['successful_sources']} sources")
        logger.info(f"📊 Data freshness: {summary['data_freshness']}")
        logger.info(f"🌍 States covered: {summary['states_covered']}")
        
        return {
            "boundaries": boundaries,
            "summary": {
                "total_leases": summary["total_leases"],
                "total_area_hectares": summary["total_area_hectares"],
                "states_covered": summary["states_covered"],
                "minerals_covered": summary["minerals_covered"],
                "data_sources": summary["data_sources"],
                "successful_sources": summary["successful_sources"],
                "source_success_rate": summary["source_success_rate"],
                "last_updated": summary["last_updated"],
                "data_freshness": summary["data_freshness"]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching live mining boundaries: {e}")
        raise HTTPException(status_code=502, detail=f"Live government APIs unavailable or credentials missing: {e}")

@app.get("/api/mining-boundaries/{state}")
async def get_boundaries_by_state(state: str):
    """
    Get mining boundaries for a specific state from live API
    
    Args:
        state: State name
        
    Returns:
        Dict: State-specific boundaries
    """
    try:
        # Fetch real state data from live API
        state_data = real_mining_api.get_state_mining_data(state)
        
        return {
            "state": state,
            "boundaries": state_data["boundaries"],
            "summary": state_data["summary"]
        }
        
    except Exception as e:
        logger.error(f"Error fetching live boundaries for state {state}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mining-statistics")
async def get_mining_statistics():
    """
    Get live mining statistics from government APIs
    
    Returns:
        Dict: Live mining statistics and data freshness info
    """
    try:
        logger.info("📊 Fetching live mining statistics from government APIs...")
        
        # Get live data from multiple government sources
        live_data = await get_live_mining_data()
        summary = live_data['summary']
        source_stats = live_data.get('source_stats', {})
        
        logger.info(f"✅ Fetched live statistics: {summary['total_leases']} leases, {summary['total_area_hectares']} hectares")
        logger.info(f"📡 Data sources: {summary['successful_sources']}/{len(summary['data_sources'])} successful")
        
        return {
            "statistics": summary,
            "source_performance": source_stats,
            "data_freshness": summary['data_freshness'],
            "last_updated": summary['last_updated'],
            "api_status": "live"
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching live mining statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/satellite-analysis")
async def run_satellite_analysis():
    """
    Run live satellite analysis for mining detection
    
    Returns:
        Dict: Live satellite analysis results
    """
    try:
        logger.info("🛰️ Starting live satellite analysis...")
        
        # Define India-wide analysis area
        india_aoi = {
            "type": "Polygon",
            "coordinates": [[
                [68.0, 6.0], [97.0, 6.0], [97.0, 37.0], [68.0, 37.0], [68.0, 6.0]
            ]]
        }
        
        # Import and run live satellite analysis
        from live_satellite_analysis import analyze_mining_activities_live
        results = await analyze_mining_activities_live(india_aoi)
        
        logger.info(f"✅ Live satellite analysis completed: {results['summary']['satellite_analysis']['total_detected_areas']} areas detected")
        
        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "live_satellite",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Error in live satellite analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/satellite-data")
async def get_satellite_data():
    """
    Get live satellite analysis data for map display
    
    Returns:
        Dict: Satellite detected mining areas
    """
    try:
        logger.info("🛰️ Fetching live satellite data for map display...")
        
        # Define India-wide analysis area
        india_aoi = {
            "type": "Polygon",
            "coordinates": [[
                [68.0, 6.0], [97.0, 6.0], [97.0, 37.0], [68.0, 37.0], [68.0, 6.0]
            ]]
        }
        
        # Import and run live satellite analysis
        from live_satellite_analysis import analyze_mining_activities_live
        results = await analyze_mining_activities_live(india_aoi)
        
        # Extract mining areas for map display
        mining_areas = results.get('mining_areas', [])
        
        # Convert to GeoJSON format for map
        features = []
        for area in mining_areas:
            feature = {
                'type': 'Feature',
                'properties': {
                    'id': area.get('id', 'unknown'),
                    'source': area.get('source', 'satellite'),
                    'area_hectares': area.get('area_hectares', 0),
                    'confidence': area.get('spectral_analysis', {}).get('confidence', 0),
                    'ndvi': area.get('spectral_analysis', {}).get('ndvi', 0),
                    'bsi': area.get('spectral_analysis', {}).get('bsi', 0),
                    'detection_date': area.get('detection_date', ''),
                    'resolution': area.get('resolution', 'unknown'),
                    'cloud_cover': area.get('cloud_cover', 0),
                    'mining_type': 'Detected Mining Area'
                },
                'geometry': area.get('geometry', {
                    'type': 'Polygon',
                    'coordinates': [[]]
                })
            }
            features.append(feature)
        
        geojson_data = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        logger.info(f"✅ Satellite data prepared: {len(features)} areas for map display")
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data_type': 'satellite_mining_areas',
            'total_areas': len(features),
            'geojson': geojson_data,
            'summary': results.get('summary', {}).get('satellite_analysis', {})
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching satellite data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
