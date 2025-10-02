import { useState, useEffect } from 'react';
import MapComponent from './MapComponent';
import './App.css';

// Fix for default markers in react-leaflet
import L from 'leaflet';
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// AnalysisResult interface removed as it's not used in the current implementation

interface IllegalMiningArea {
  id: string;
  name: string;
  area_ha: number;
  depth_m: number;
  width_m: number;
  length_m: number;
  volume_m3: number;
  coordinates: [number, number][];
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
}

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mapCenter] = useState<[number, number]>([28.0, 77.0]);
  const [mapZoom] = useState(12);
  const [miningBoundaries, setMiningBoundaries] = useState<any>(null);
  const [showBoundaries, setShowBoundaries] = useState(false);
  const [analysisStep, setAnalysisStep] = useState<'idle' | 'legal' | 'analyzing' | 'illegal' | 'visualization'>('idle');
  const [illegalAreas, setIllegalAreas] = useState<IllegalMiningArea[]>([]);
  const [selectedIllegalArea, setSelectedIllegalArea] = useState<IllegalMiningArea | null>(null);
  const [showVisualization, setShowVisualization] = useState(false);
  const [violationZones, setViolationZones] = useState<{
    redZones: any[];
    orangeZones: any[];
  }>({ redZones: [], orangeZones: [] });
  const [illegalMiningAnalysis, setIllegalMiningAnalysis] = useState<any>(null);
  const [satelliteData, setSatelliteData] = useState<any>(null);

  // Fetch mining boundaries and satellite data on component mount
  useEffect(() => {
    fetchMiningBoundaries();
    fetchSatelliteData();
  }, []);

  const fetchMiningBoundaries = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/mining-boundaries');
      if (response.ok) {
        const data = await response.json();
        setMiningBoundaries(data);
      }
    } catch (err) {
      console.error('Error fetching mining boundaries:', err);
    }
  };

  const fetchSatelliteData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/satellite-data');
      if (response.ok) {
        const data = await response.json();
        setSatelliteData(data);
        console.log(`🛰️ Fetched ${data.total_areas} satellite-detected mining areas`);
      }
    } catch (err) {
      console.error('Error fetching satellite data:', err);
    }
  };

  const runAnalysis = async () => {
    setIsLoading(true);
    setError(null);
    setAnalysisStep('legal');

    try {
      // Step 1: Show legal boundaries
      setShowBoundaries(true);
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Step 2: Start analysis
      setAnalysisStep('analyzing');
      
      const aoi = {
        type: "Polygon",
        coordinates: [[
          [77.0, 28.0],
          [77.1, 28.0],
          [77.1, 28.1],
          [77.0, 28.1],
          [77.0, 28.0]
        ]]
      };

      const request = {
        aoi: {
          geometry: aoi,
          name: "Demo Mining Area"
        },
        boundary_file: "demo_boundary.shp",
        analysis_name: `analysis_${Date.now()}`
      };

      const response = await fetch('http://localhost:8000/api/analyze/quick', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (response.ok) {
        await response.json(); // Process response but don't store it
        
        // Step 3: Generate illegal mining areas
        setAnalysisStep('illegal');
        await generateIllegalMiningAreas();
      } else {
        throw new Error('Analysis failed');
      }
    } catch (err) {
      setError('Failed to run analysis. Please make sure the backend is running.');
      console.error('Error running analysis:', err);
      setAnalysisStep('idle');
    } finally {
      setIsLoading(false);
    }
  };

  const runCompleteIllegalMiningDetection = async () => {
    setIsLoading(true);
    setError(null);
    setAnalysisStep('analyzing');

    try {
      console.log('🚀 Starting complete illegal mining detection...');
      
      // Start the complete illegal mining detection analysis
      const response = await fetch('http://localhost:8000/api/analyze/illegal-mining-detection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Illegal mining analysis started:', result);
        
        // Poll for results
        await pollForIllegalMiningResults(result.analysis_id);
      } else {
        throw new Error('Failed to start illegal mining detection');
      }
    } catch (err) {
      setError('Illegal mining detection failed. Please try again.');
      console.error('Illegal mining detection error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const pollForIllegalMiningResults = async (analysisId: string) => {
    const maxAttempts = 30; // 5 minutes with 10-second intervals
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/illegal-mining-results/${analysisId}`);
        
        if (response.ok) {
          const result = await response.json();
          
          if (result.status === 'completed') {
            console.log('🎉 Illegal mining detection completed!', result);
            setIllegalMiningAnalysis(result);
            setAnalysisStep('illegal');
            
            // Process violation zones
            const zones = result.violation_zones || {};
            setViolationZones({
              redZones: zones.red_zones_geojson?.features || [],
              orangeZones: zones.orange_zones_geojson?.features || []
            });
            
            // Generate illegal areas from violation zones
            generateIllegalAreasFromViolations(result);
            
          } else if (result.status === 'failed') {
            setError(`Analysis failed: ${result.message}`);
          } else if (attempts < maxAttempts) {
            // Still processing, wait and try again
            setTimeout(poll, 10000); // Wait 10 seconds
            attempts++;
          } else {
            setError('Analysis timed out. Please try again.');
          }
        }
      } catch (err) {
        console.error('Error polling for results:', err);
        if (attempts < maxAttempts) {
          setTimeout(poll, 10000);
          attempts++;
        } else {
          setError('Failed to get analysis results.');
        }
      }
    };

    poll();
  };

  const generateIllegalAreasFromViolations = (analysisResult: any) => {
    const summary = analysisResult.analysis_summary || {};
    const zones = analysisResult.violation_zones || {};
    
    const illegalAreas: IllegalMiningArea[] = [];
    
    // Process red zones (critical violations)
    const redZones = zones.red_zones_geojson?.features || [];
    redZones.forEach((zone: any, index: number) => {
      const props = zone.properties;
      const coords = zone.geometry.coordinates[0];
      
      illegalAreas.push({
        id: `red_zone_${index}`,
        name: `Critical Violation ${index + 1}`,
        area_ha: props.area_hectares || 0,
        depth_m: Math.random() * 20 + 5, // Simulate depth
        width_m: Math.random() * 100 + 50,
        length_m: Math.random() * 150 + 100,
        volume_m3: (props.area_hectares || 0) * 10000 * (Math.random() * 20 + 5),
        coordinates: coords,
        severity: 'critical' as const,
        description: props.description || 'Critical illegal mining violation detected'
      });
    });
    
    // Process orange zones (warning violations)
    const orangeZones = zones.orange_zones_geojson?.features || [];
    orangeZones.forEach((zone: any, index: number) => {
      const props = zone.properties;
      const coords = zone.geometry.coordinates[0];
      
      illegalAreas.push({
        id: `orange_zone_${index}`,
        name: `Warning Violation ${index + 1}`,
        area_ha: props.area_hectares || 0,
        depth_m: Math.random() * 15 + 3,
        width_m: Math.random() * 80 + 30,
        length_m: Math.random() * 120 + 60,
        volume_m3: (props.area_hectares || 0) * 10000 * (Math.random() * 15 + 3),
        coordinates: coords,
        severity: 'high' as const,
        description: props.description || 'Warning: Potential illegal mining activity'
      });
    });
    
    setIllegalAreas(illegalAreas);
  };

  const generateIllegalMiningAreas = async () => {
    // Simulate illegal mining detection
    const mockIllegalAreas: IllegalMiningArea[] = [
      {
        id: 'illegal_001',
        name: 'Unauthorized Iron Ore Mining',
        area_ha: 15.5,
        depth_m: 8.2,
        width_m: 120,
        length_m: 180,
        volume_m3: 11250,
        coordinates: [[77.05, 28.05], [77.08, 28.05], [77.08, 28.08], [77.05, 28.08], [77.05, 28.05]],
        severity: 'high',
        description: 'Illegal iron ore extraction detected outside lease boundaries. Significant environmental damage observed.'
      },
      {
        id: 'illegal_002',
        name: 'Unlicensed Limestone Quarry',
        area_ha: 8.3,
        depth_m: 5.1,
        width_m: 90,
        length_m: 110,
        volume_m3: 4230,
        coordinates: [[77.02, 28.02], [77.05, 28.02], [77.05, 28.05], [77.02, 28.05], [77.02, 28.02]],
        severity: 'medium',
        description: 'Unauthorized limestone mining operation. Moderate environmental impact.'
      },
      {
        id: 'illegal_003',
        name: 'Illegal Sand Mining',
        area_ha: 3.2,
        depth_m: 2.8,
        width_m: 60,
        length_m: 70,
        volume_m3: 896,
        coordinates: [[77.08, 28.08], [77.10, 28.08], [77.10, 28.10], [77.08, 28.10], [77.08, 28.08]],
        severity: 'critical',
        description: 'Critical illegal sand mining near water bodies. Immediate action required.'
      }
    ];

    setIllegalAreas(mockIllegalAreas);
    setAnalysisStep('visualization');
  };

  const selectIllegalArea = (area: IllegalMiningArea) => {
    setSelectedIllegalArea(area);
    setShowVisualization(true);
  };

  const open3DView = () => {
    if (selectedIllegalArea) {

      // Open 3D viewer in new window
      const newWindow = window.open('', '_blank', 'width=1200,height=800');
      if (newWindow) {
        newWindow.document.write(`
          <!DOCTYPE html>
          <html>
          <head>
            <title>3D Mining Visualization - ${selectedIllegalArea.name}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
              body { margin: 0; padding: 20px; font-family: Arial, sans-serif; background: #f0f0f0; }
              .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
              .controls { background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
              .measurements { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
              .measurement-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #667eea; }
              .measurement-value { font-size: 1.5em; font-weight: bold; color: #333; }
              .measurement-label { color: #666; margin-top: 5px; }
              #plotly-div { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>🚛 3D Mining Visualization</h1>
              <h2>${selectedIllegalArea.name}</h2>
              <p>Severity: <strong>${selectedIllegalArea.severity.toUpperCase()}</strong> | ${selectedIllegalArea.description}</p>
              <div style="margin-top: 15px; display: flex; gap: 25px; flex-wrap: wrap; justify-content: center;">
                <div style="display: flex; align-items: center; gap: 10px; padding: 8px 15px; background: rgba(46, 204, 113, 0.1); border-radius: 8px; border: 2px solid #2ecc71;">
                  <div style="width: 25px; height: 25px; background: #2ecc71; border-radius: 4px;"></div>
                  <span style="font-weight: bold; color: #2c3e50;">Legal Mining Area (3x Larger)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px; padding: 8px 15px; background: rgba(231, 76, 60, 0.1); border-radius: 8px; border: 2px solid #e74c3c;">
                  <div style="width: 25px; height: 25px; background: #e74c3c; border-radius: 4px;"></div>
                  <span style="font-weight: bold; color: #2c3e50;">Illegal Mining Pit (Violation)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px; padding: 8px 15px; background: rgba(243, 156, 18, 0.1); border-radius: 8px; border: 2px solid #f39c12;">
                  <div style="width: 25px; height: 25px; background: #f39c12; border-radius: 4px;"></div>
                  <span style="font-weight: bold; color: #2c3e50;">Pit Walls (Depth Violation)</span>
                </div>
              </div>
              <div style="margin-top: 10px; text-align: center; color: #7f8c8d; font-size: 14px;">
                <strong>Clear Comparison:</strong> Large green area (legal) vs Small red pit (illegal violation)
              </div>
            </div>
            
            <div class="controls">
              <h3>📊 Measurements</h3>
              <div class="measurements">
                <div class="measurement-card">
                  <div class="measurement-value">${selectedIllegalArea.length_m}m</div>
                  <div class="measurement-label">Length</div>
                </div>
                <div class="measurement-card">
                  <div class="measurement-value">${selectedIllegalArea.width_m}m</div>
                  <div class="measurement-label">Width</div>
                </div>
                <div class="measurement-card">
                  <div class="measurement-value">${selectedIllegalArea.depth_m}m</div>
                  <div class="measurement-label">Depth</div>
                </div>
                <div class="measurement-card">
                  <div class="measurement-value">${selectedIllegalArea.volume_m3.toLocaleString()} m³</div>
                  <div class="measurement-label">Volume</div>
                </div>
                <div class="measurement-card">
                  <div class="measurement-value">${selectedIllegalArea.area_ha} ha</div>
                  <div class="measurement-label">Area</div>
                </div>
              </div>
            </div>
            
            <div id="plotly-div" style="width: 100%; height: 600px;"></div>
            
            <script>
              // Create enhanced 3D mining pit visualization with clear legal vs illegal boundaries
              const illegalLength = ${selectedIllegalArea.length_m};
              const illegalWidth = ${selectedIllegalArea.width_m};
              const illegalDepth = ${selectedIllegalArea.depth_m};
              
              // Make legal area much larger and more visible
              const legalLength = illegalLength * 4; // 4x larger for clear comparison
              const legalWidth = illegalWidth * 4;
              
              const data = [
                // Create a large, dramatic legal mining area (left side)
                {
                  type: 'scatter3d',
                  x: [-legalLength/2, legalLength/2, legalLength/2, -legalLength/2, -legalLength/2],
                  y: [-legalWidth/2, -legalWidth/2, legalWidth/2, legalWidth/2, -legalWidth/2],
                  z: [0, 0, 0, 0, 0],
                  mode: 'markers+lines',
                  marker: { 
                    size: 20, 
                    color: '#2ecc71',
                    symbol: 'square'
                  },
                  line: { 
                    color: '#2ecc71', 
                    width: 15 
                  },
                  name: 'Legal Mining Area (Permitted Zone)',
                  showlegend: true
                },
                // Fill the legal area with a large surface
                {
                  type: 'surface',
                  x: [-legalLength/2, legalLength/2, legalLength/2, -legalLength/2, -legalLength/2],
                  y: [-legalWidth/2, -legalWidth/2, legalWidth/2, legalWidth/2, -legalWidth/2],
                  z: [
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0]
                  ],
                  colorscale: [[0, '#2ecc71'], [1, '#27ae60']],
                  opacity: 0.8,
                  name: 'Legal Mining Surface',
                  showscale: false
                },
                // Create a dramatic illegal mining pit (right side)
                {
                  type: 'scatter3d',
                  x: [illegalLength/2, illegalLength/2 + illegalLength, illegalLength/2 + illegalLength, illegalLength/2, illegalLength/2],
                  y: [-illegalWidth/2, -illegalWidth/2, illegalWidth/2, illegalWidth/2, -illegalWidth/2],
                  z: [0, 0, 0, 0, 0],
                  mode: 'markers+lines',
                  marker: { 
                    size: 15, 
                    color: '#e74c3c',
                    symbol: 'diamond'
                  },
                  line: { 
                    color: '#e74c3c', 
                    width: 12,
                    dash: 'dash'
                  },
                  name: 'Illegal Mining Area (Violation Zone)',
                  showlegend: true
                },
                // Create the illegal pit bottom
                {
                  type: 'scatter3d',
                  x: [illegalLength/2, illegalLength/2 + illegalLength, illegalLength/2 + illegalLength, illegalLength/2, illegalLength/2],
                  y: [-illegalWidth/2, -illegalWidth/2, illegalWidth/2, illegalWidth/2, -illegalWidth/2],
                  z: [-illegalDepth, -illegalDepth, -illegalDepth, -illegalDepth, -illegalDepth],
                  mode: 'markers+lines',
                  marker: { 
                    size: 15, 
                    color: '#c0392b',
                    symbol: 'diamond'
                  },
                  line: { 
                    color: '#c0392b', 
                    width: 10,
                    dash: 'dash'
                  },
                  name: 'Illegal Pit Bottom',
                  showlegend: true
                },
                // Create pit walls to show depth
                {
                  type: 'scatter3d',
                  x: [illegalLength/2, illegalLength/2, illegalLength/2 + illegalLength, illegalLength/2 + illegalLength, illegalLength/2],
                  y: [-illegalWidth/2, illegalWidth/2, illegalWidth/2, -illegalWidth/2, -illegalWidth/2],
                  z: [0, 0, 0, 0, 0],
                  mode: 'lines',
                  line: { 
                    color: '#f39c12', 
                    width: 8
                  },
                  name: 'Pit Walls (Depth Violation)',
                  showlegend: true
                },
                {
                  type: 'scatter3d',
                  x: [illegalLength/2, illegalLength/2, illegalLength/2 + illegalLength, illegalLength/2 + illegalLength, illegalLength/2],
                  y: [-illegalWidth/2, illegalWidth/2, illegalWidth/2, -illegalWidth/2, -illegalWidth/2],
                  z: [-illegalDepth, -illegalDepth, -illegalDepth, -illegalDepth, -illegalDepth],
                  mode: 'lines',
                  line: { 
                    color: '#f39c12', 
                    width: 8
                  },
                  name: 'Pit Bottom Walls',
                  showlegend: true
                },
                // Ground level reference line connecting both areas
                {
                  type: 'scatter3d',
                  x: [-legalLength/2, legalLength/2 + illegalLength],
                  y: [0, 0],
                  z: [0, 0],
                  mode: 'lines',
                  line: { color: '#95a5a6', width: 6, dash: 'dot' },
                  name: 'Ground Level Reference',
                  showlegend: true
                }
              ];

              const layout = {
                title: {
                  text: '🚛 DRAMATIC 3D COMPARISON: Legal vs Illegal Mining Boundaries',
                  font: { size: 20, color: '#2c3e50' }
                },
                scene: {
                  xaxis: { 
                    title: 'Length (meters)', 
                    range: [-legalLength/2 - 50, legalLength/2 + illegalLength + 50],
                    titlefont: { size: 14, color: '#2c3e50' }
                  },
                  yaxis: { 
                    title: 'Width (meters)', 
                    range: [-legalWidth/2 - 50, legalWidth/2 + 50],
                    titlefont: { size: 14, color: '#2c3e50' }
                  },
                  zaxis: { 
                    title: 'Depth (meters)', 
                    range: [-illegalDepth - 5, 10],
                    titlefont: { size: 14, color: '#2c3e50' }
                  },
                  camera: {
                    eye: { x: 1.5, y: 1.5, z: 1.0 },
                    center: { x: 0, y: 0, z: 0 }
                  },
                  aspectmode: 'cube',
                  bgcolor: 'rgba(240, 248, 255, 0.1)'
                },
                margin: { l: 0, r: 0, t: 80, b: 0 },
                paper_bgcolor: 'white',
                plot_bgcolor: 'white',
                legend: {
                  x: 0.02,
                  y: 0.98,
                  bgcolor: 'rgba(255, 255, 255, 0.95)',
                  bordercolor: '#2c3e50',
                  borderwidth: 2,
                  font: { size: 11 }
                }
              };

              const config = {
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
              };

              Plotly.newPlot('plotly-div', data, layout, config);
            </script>
          </body>
          </html>
        `);
        newWindow.document.close();
      }
    }
  };

  const open2DView = () => {
    if (selectedIllegalArea) {
      // Create 2D cross-section visualization
      const newWindow = window.open('', '_blank', 'width=1000,height=700');
      if (newWindow) {
        newWindow.document.write(`
          <!DOCTYPE html>
          <html>
          <head>
            <title>2D Mining Cross-Section - ${selectedIllegalArea.name}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
              body { margin: 0; padding: 20px; font-family: Arial, sans-serif; background: #f0f0f0; }
              .header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
              .info { background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
              #plotly-div { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>📐 2D Mining Cross-Section</h1>
              <h2>${selectedIllegalArea.name}</h2>
            </div>
            
            <div class="info">
              <h3>📊 Cross-Section View</h3>
              <p>This shows a side view of the mining pit with depth measurements and volume calculations.</p>
            </div>
            
            <div id="plotly-div" style="width: 100%; height: 500px;"></div>
            
            <script>
              // Create 2D cross-section visualization
              const x = [0, ${selectedIllegalArea.length_m}, ${selectedIllegalArea.length_m}, 0, 0];
              const y = [0, 0, -${selectedIllegalArea.depth_m}, -${selectedIllegalArea.depth_m}, 0];
              
              const data = [{
                x: x,
                y: y,
                type: 'scatter',
                mode: 'lines+markers',
                fill: 'tonexty',
                fillcolor: 'rgba(255, 165, 0, 0.3)',
                line: { color: '#ff6b35', width: 3 },
                name: 'Mining Pit Cross-Section',
                hovertemplate: 'Length: %{x}m<br>Depth: %{y}m<extra></extra>'
              }, {
                x: [0, ${selectedIllegalArea.length_m}],
                y: [0, 0],
                type: 'scatter',
                mode: 'lines',
                line: { color: '#2ecc71', width: 4, dash: 'dash' },
                name: 'Ground Level'
              }];

              const layout = {
                title: {
                  text: 'Mining Pit Cross-Section View',
                  font: { size: 18, color: '#333' }
                },
                xaxis: {
                  title: 'Length (meters)',
                  range: [-10, ${selectedIllegalArea.length_m + 10}]
                },
                yaxis: {
                  title: 'Depth (meters)',
                  range: [-${selectedIllegalArea.depth_m * 1.2}, 5]
                },
                annotations: [
                  {
                    x: ${selectedIllegalArea.length_m / 2},
                    y: -${selectedIllegalArea.depth_m / 2},
                    text: \`Depth: ${selectedIllegalArea.depth_m}m<br>Length: ${selectedIllegalArea.length_m}m<br>Volume: ${selectedIllegalArea.volume_m3.toLocaleString()} m³\`,
                    showarrow: true,
                    arrowhead: 2,
                    arrowcolor: '#ff6b35',
                    bgcolor: 'rgba(255,255,255,0.8)',
                    bordercolor: '#ff6b35',
                    borderwidth: 1
                  }
                ],
                margin: { l: 60, r: 20, t: 60, b: 60 },
                paper_bgcolor: 'white',
                plot_bgcolor: 'white'
              };

              const config = {
                displayModeBar: true,
                displaylogo: false
              };

              Plotly.newPlot('plotly-div', data, layout, config);
            </script>
          </body>
          </html>
        `);
        newWindow.document.close();
      }
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return '#10b981';
      case 'medium': return '#f59e0b';
      case 'high': return '#ef4444';
      case 'critical': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'low': return '🟢';
      case 'medium': return '🟡';
      case 'high': return '🟠';
      case 'critical': return '🔴';
      default: return '⚪';
    }
  };

  const generateReport = () => {
    if (selectedIllegalArea) {
      const reportContent = `
# 🚨 Illegal Mining Detection Report

## Area Information
- **Name**: ${selectedIllegalArea.name}
- **Severity**: ${selectedIllegalArea.severity.toUpperCase()}
- **Description**: ${selectedIllegalArea.description}

## Measurements
- **Length**: ${selectedIllegalArea.length_m} meters
- **Width**: ${selectedIllegalArea.width_m} meters
- **Depth**: ${selectedIllegalArea.depth_m} meters
- **Area**: ${selectedIllegalArea.area_ha} hectares
- **Volume**: ${selectedIllegalArea.volume_m3.toLocaleString()} cubic meters

## Environmental Impact
- **Estimated Soil Displacement**: ${(selectedIllegalArea.volume_m3 / 1000).toFixed(0)}k cubic meters
- **Surface Area Affected**: ${selectedIllegalArea.area_ha} hectares
- **Depth of Excavation**: ${selectedIllegalArea.depth_m} meters below ground level

## Recommendations
${selectedIllegalArea.severity === 'critical' ? 
  '🚨 IMMEDIATE ACTION REQUIRED: This is a critical violation requiring immediate intervention and legal action.' :
  selectedIllegalArea.severity === 'high' ?
  '⚠️ HIGH PRIORITY: Significant environmental damage detected. Urgent investigation and enforcement needed.' :
  selectedIllegalArea.severity === 'medium' ?
  '📋 MEDIUM PRIORITY: Moderate environmental impact. Schedule investigation and monitoring.' :
  '📝 LOW PRIORITY: Minor violation detected. Regular monitoring recommended.'
}

## Report Generated
- **Date**: ${new Date().toLocaleDateString()}
- **Time**: ${new Date().toLocaleTimeString()}
- **System**: Illegal Mining Detection System v1.0
      `;

      // Create and download the report
      const blob = new Blob([reportContent], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `illegal_mining_report_${selectedIllegalArea.id}_${new Date().toISOString().split('T')[0]}.md`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🚛 Illegal Mining Detection System</h1>
        <p>Smart India Hackathon Project - AI-Powered Mining Surveillance</p>
      </header>

      <div className="app-content">
        <div className="sidebar">
          <div className="control-panel">
            <h3>Analysis Control</h3>
            
            {analysisStep === 'idle' && (
      <div>
                <button 
                  onClick={runAnalysis} 
                  disabled={isLoading}
                  className="analyze-btn"
                >
                  🚀 Quick Analysis
                </button>
                
                <button 
                  onClick={runCompleteIllegalMiningDetection} 
                  disabled={isLoading}
                  className="analyze-btn"
                  style={{ 
                    marginTop: '1rem',
                    background: 'linear-gradient(135deg, #e74c3c, #c0392b)',
                    boxShadow: '0 10px 30px rgba(231, 76, 60, 0.3)'
                  }}
                >
                  🚨 Complete Illegal Mining Detection
                </button>
              </div>
            )}

            {analysisStep === 'legal' && (
              <div className="step-indicator">
                <div className="step active">
                  <div className="step-icon">1</div>
                  <div className="step-text">Showing Legal Boundaries</div>
                </div>
                <div className="step">
                  <div className="step-icon">2</div>
                  <div className="step-text">Analyzing Satellite Images</div>
                </div>
                <div className="step">
                  <div className="step-icon">3</div>
                  <div className="step-text">Detecting Illegal Mining</div>
                </div>
              </div>
            )}

            {analysisStep === 'analyzing' && (
              <div className="step-indicator">
                <div className="step completed">
                  <div className="step-icon">✓</div>
                  <div className="step-text">Legal Boundaries Loaded</div>
                </div>
                <div className="step active">
                  <div className="step-icon">2</div>
                  <div className="step-text">Analyzing Satellite Images...</div>
                </div>
                <div className="step">
                  <div className="step-icon">3</div>
                  <div className="step-text">Detecting Illegal Mining</div>
                </div>
              </div>
            )}

            {analysisStep === 'illegal' && (
              <div className="step-indicator">
                <div className="step completed">
                  <div className="step-icon">✓</div>
                  <div className="step-text">Legal Boundaries Loaded</div>
                </div>
                <div className="step completed">
                  <div className="step-icon">✓</div>
                  <div className="step-text">Satellite Analysis Complete</div>
                </div>
                <div className="step active">
                  <div className="step-icon">3</div>
                  <div className="step-text">Illegal Mining Detected!</div>
                </div>
              </div>
            )}

            {analysisStep === 'visualization' && (
              <div className="step-indicator">
                <div className="step completed">
                  <div className="step-icon">✓</div>
                  <div className="step-text">Legal Boundaries Loaded</div>
                </div>
                <div className="step completed">
                  <div className="step-icon">✓</div>
                  <div className="step-text">Satellite Analysis Complete</div>
                </div>
                <div className="step completed">
                  <div className="step-icon">✓</div>
                  <div className="step-text">Illegal Mining Detected</div>
                </div>
              </div>
            )}

            <div className="control-options">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showBoundaries}
                  onChange={(e) => setShowBoundaries(e.target.checked)}
                />
                Show Legal Mining Boundaries
              </label>
            </div>
            
            {miningBoundaries && (
              <div className="boundaries-info">
                <h4>🏛️ Official Mining Leases (Live Data)</h4>
                <p><strong>Total Leases:</strong> {miningBoundaries.summary?.total_leases || 0}</p>
                <p><strong>Total Area:</strong> {miningBoundaries.summary?.total_area_hectares?.toFixed(1) || 0} hectares</p>
                <p><strong>States:</strong> {miningBoundaries.summary?.states?.join(', ') || 'N/A'}</p>
                <p><strong>Minerals:</strong> {miningBoundaries.summary?.minerals?.join(', ') || 'N/A'}</p>
                {miningBoundaries.summary?.value_2024_crores && (
                  <p><strong>Total Value (2024):</strong> ₹{miningBoundaries.summary.value_2024_crores.total_value?.toLocaleString()} crores</p>
                )}
                <div style={{marginTop: '10px', padding: '8px', background: 'rgba(52, 152, 219, 0.1)', borderRadius: '5px', borderLeft: '3px solid #3498db'}}>
                  <p style={{margin: 0, fontSize: '0.85rem', color: '#2c3e50'}}>
                    <strong>📡 Data Source:</strong> Real mining lease data from official sources. 
                    <br/>Satellite analysis uses simulated data for demo purposes.
                  </p>
                </div>
              </div>
            )}
            
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </div>

          {illegalAreas.length > 0 && (
            <div className="illegal-areas-panel">
              <h3>🚨 Illegal Mining Areas Detected</h3>
              <div className="illegal-areas-list">
                {illegalAreas.map((area) => (
                  <div 
                    key={area.id}
                    className={`illegal-area-card ${selectedIllegalArea?.id === area.id ? 'selected' : ''}`}
                    onClick={() => selectIllegalArea(area)}
                  >
                    <div className="area-header">
                      <div className="severity-badge" style={{ backgroundColor: getSeverityColor(area.severity) }}>
                        {getSeverityIcon(area.severity)} {area.severity.toUpperCase()}
                      </div>
                    </div>
                    <div className="area-name">{area.name}</div>
                    <div className="area-stats">
                      <div className="stat">
                        <span className="stat-label">Area:</span>
                        <span className="stat-value">{area.area_ha} ha</span>
                      </div>
                      <div className="stat">
                        <span className="stat-label">Depth:</span>
                        <span className="stat-value">{area.depth_m} m</span>
                      </div>
                      <div className="stat">
                        <span className="stat-label">Volume:</span>
                        <span className="stat-value">{area.volume_m3.toLocaleString()} m³</span>
                      </div>
                    </div>
                    <div className="area-description">{area.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="main-content">
          <div className="map-container">
            <MapComponent
              center={mapCenter}
              zoom={mapZoom}
              style={{ height: '100%', width: '100%' }}
              miningBoundaries={miningBoundaries}
              showBoundaries={showBoundaries}
              illegalAreas={illegalAreas}
              selectedIllegalArea={selectedIllegalArea}
              violationZones={violationZones}
              satelliteData={satelliteData}
            />
          </div>

          {showVisualization && selectedIllegalArea && (
            <div className="visualization-panel">
              <h3>📊 3D Visualization & Measurements</h3>
              <div className="visualization-content">
                <div className="measurements-grid">
                  <div className="measurement-card">
                    <div className="measurement-icon">📏</div>
                    <div className="measurement-label">Length</div>
                    <div className="measurement-value">{selectedIllegalArea.length_m} m</div>
                  </div>
                  <div className="measurement-card">
                    <div className="measurement-icon">📐</div>
                    <div className="measurement-label">Width</div>
                    <div className="measurement-value">{selectedIllegalArea.width_m} m</div>
                  </div>
                  <div className="measurement-card">
                    <div className="measurement-icon">⬇️</div>
                    <div className="measurement-label">Depth</div>
                    <div className="measurement-value">{selectedIllegalArea.depth_m} m</div>
                  </div>
                  <div className="measurement-card">
                    <div className="measurement-icon">📦</div>
                    <div className="measurement-label">Volume</div>
                    <div className="measurement-value">{selectedIllegalArea.volume_m3.toLocaleString()} m³</div>
                  </div>
                </div>
                <div className="visualization-actions">
                  <button className="viz-btn primary" onClick={open2DView}>🗺️ 2D View</button>
                  <button className="viz-btn secondary" onClick={open3DView}>🌐 3D View</button>
                  <button className="viz-btn danger" onClick={generateReport}>📄 Generate Report</button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      </div>
  );
}

export default App;