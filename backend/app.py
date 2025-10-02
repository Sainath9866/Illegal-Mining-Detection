"""
FastAPI Backend for Illegal Mining Detection System
Provides REST API endpoints for all mining detection functionality
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

# Import pipeline
from main_pipeline import MiningDetectionPipeline

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize pipeline
pipeline = MiningDetectionPipeline(output_dir="output")

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

@app.post("/api/analyze", response_model=AnalysisResponse)
async def run_complete_analysis(request: AnalysisRequest):
    """
    Run complete illegal mining detection analysis
    
    Args:
        request: Analysis request with AOI, dates, and boundary file
        
    Returns:
        AnalysisResponse: Analysis results
    """
    try:
        logger.info(f"Starting complete analysis: {request.analysis_name}")
        
        # Run analysis
        results = pipeline.run_complete_analysis(
            aoi=request.aoi.geometry,
            start_date=request.start_date,
            end_date=request.end_date,
            boundary_path=request.boundary_file,
            analysis_name=request.analysis_name
        )
        
        # Store results
        analysis_id = f"{request.analysis_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        analysis_results[analysis_id] = results
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            message="Analysis completed successfully",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error in complete analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/quick", response_model=AnalysisResponse)
async def run_quick_analysis(request: QuickAnalysisRequest):
    """
    Run quick illegal mining detection analysis
    
    Args:
        request: Quick analysis request with AOI and boundary file
        
    Returns:
        AnalysisResponse: Analysis results
    """
    try:
        logger.info(f"Starting quick analysis: {request.analysis_name}")
        
        # Run quick analysis
        results = pipeline.run_quick_analysis(
            aoi=request.aoi.geometry,
            boundary_path=request.boundary_file,
            analysis_name=request.analysis_name
        )
        
        # Store results
        analysis_id = f"{request.analysis_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        analysis_results[analysis_id] = results
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            message="Quick analysis completed successfully",
            results=results
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
    Upload mining boundary shapefile
    
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
    Download analysis report
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        FileResponse: PDF report file
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    results = analysis_results[analysis_id]
    report_path = results.get("report_path")
    
    if not report_path or not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=report_path,
        filename=f"mining_report_{analysis_id}.pdf",
        media_type="application/pdf"
    )

@app.get("/api/download/visualization/{analysis_id}/{viz_type}")
async def download_visualization(analysis_id: str, viz_type: str):
    """
    Download visualization files
    
    Args:
        analysis_id: Analysis ID
        viz_type: Type of visualization (map, 3d, etc.)
        
    Returns:
        FileResponse: Visualization file
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    results = analysis_results[analysis_id]
    
    # Map visualization types to file paths
    viz_paths = {
        "map": results.get("mining_map_path"),
        "3d": results.get("3d_visualization_path"),
        "ndvi_bsi": results.get("ndvi_bsi_plot"),
        "depth_volume": results.get("depth_volume_plot")
    }
    
    if viz_type not in viz_paths:
        raise HTTPException(status_code=400, detail="Invalid visualization type")
    
    file_path = viz_paths[viz_type]
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Visualization not found")
    
    return FileResponse(path=file_path)

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
        "mining_detection": results.get("mining_detection", {}),
        "illegal_mining": results.get("illegal_mining_stats", {}),
        "volume_estimation": results.get("volume_estimation", {})
    }
    
    return stats

@app.post("/api/analyze/async")
async def run_async_analysis(
    background_tasks: BackgroundTasks,
    request: AnalysisRequest
):
    """
    Run analysis asynchronously
    
    Args:
        background_tasks: FastAPI background tasks
        request: Analysis request
        
    Returns:
        Dict: Analysis status
    """
    analysis_id = f"{request.analysis_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Add to background tasks
    background_tasks.add_task(
        run_analysis_background,
        analysis_id,
        request
    )
    
    return {
        "analysis_id": analysis_id,
        "status": "started",
        "message": "Analysis started in background"
    }

async def run_analysis_background(analysis_id: str, request: AnalysisRequest):
    """Background task for running analysis"""
    try:
        logger.info(f"Running background analysis: {analysis_id}")
        
        # Run analysis
        results = pipeline.run_complete_analysis(
            aoi=request.aoi.geometry,
            start_date=request.start_date,
            end_date=request.end_date,
            boundary_path=request.boundary_file,
            analysis_name=request.analysis_name
        )
        
        # Store results
        analysis_results[analysis_id] = results
        
        logger.info(f"Background analysis completed: {analysis_id}")
        
    except Exception as e:
        logger.error(f"Error in background analysis {analysis_id}: {e}")
        analysis_results[analysis_id] = {
            "status": "failed",
            "error": str(e)
        }

@app.get("/api/status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """
    Get analysis status
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        Dict: Analysis status
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    results = analysis_results[analysis_id]
    
    return {
        "analysis_id": analysis_id,
        "status": results.get("status", "unknown"),
        "timestamp": results.get("timestamp", "unknown")
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
