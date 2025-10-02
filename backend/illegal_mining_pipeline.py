"""
Complete Illegal Mining Detection Pipeline
Integrates government data, satellite analysis, and violation detection
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
import json

from official_government_api import OfficialGovernmentAPI
from satellite_analysis import SatelliteAnalysis
from violation_detection import ViolationDetector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IllegalMiningPipeline:
    """Complete pipeline for illegal mining detection"""
    
    def __init__(self):
        """Initialize the complete pipeline"""
        self.government_api = OfficialGovernmentAPI()
        self.satellite_analyzer = SatelliteAnalysis()
        self.violation_detector = ViolationDetector()
        
        logger.info("Illegal Mining Detection Pipeline initialized")
    
    async def run_complete_analysis(self) -> Dict[str, Any]:
        """
        Run the complete illegal mining detection analysis
        
        Returns:
            Dict: Complete analysis results with violations and visualizations
        """
        try:
            logger.info("🚀 Starting complete illegal mining detection analysis...")
            
            # Step 1: Fetch official government data
            logger.info("📊 Step 1: Fetching official government mining data...")
            government_data = await self.government_api.fetch_all_government_data()
            
            # Step 2: Analyze satellite imagery
            logger.info("🛰️ Step 2: Analyzing satellite imagery for mining activities...")
            satellite_data = await self.satellite_analyzer.analyze_india_mining_activities()
            
            # Step 3: Detect violations
            logger.info("🔍 Step 3: Detecting illegal mining violations...")
            violation_results = await self.violation_detector.detect_violations(
                satellite_data, government_data
            )
            
            # Step 4: Generate comprehensive report
            logger.info("📋 Step 4: Generating comprehensive analysis report...")
            comprehensive_report = self._generate_comprehensive_report(
                government_data, satellite_data, violation_results
            )
            
            logger.info("✅ Complete analysis finished successfully!")
            return comprehensive_report
            
        except Exception as e:
            logger.error(f"❌ Error in complete analysis: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'failed',
                'message': 'Analysis failed due to technical error'
            }
    
    def _generate_comprehensive_report(self, government_data: Dict[str, Any], 
                                     satellite_data: Dict[str, Any], 
                                     violation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        
        # Extract key statistics
        gov_summary = government_data.get('summary', {})
        sat_summary = {
            'total_mining_areas': satellite_data.get('total_mining_areas', 0),
            'total_area_hectares': satellite_data.get('total_area_hectares', 0)
        }
        violation_summary = violation_results.get('analysis_summary', {})
        
        # Calculate compliance metrics
        total_detected_area = sat_summary['total_area_hectares']
        total_legal_area = violation_summary.get('total_legal_area_hectares', 0)
        total_violation_area = violation_summary.get('total_violation_area_hectares', 0)
        
        compliance_rate = (total_legal_area / max(total_detected_area, 1)) * 100
        violation_rate = (total_violation_area / max(total_detected_area, 1)) * 100
        
        # Generate state-wise breakdown
        state_breakdown = self._generate_state_breakdown(violation_results)
        
        # Generate priority actions
        priority_actions = self._generate_priority_actions(violation_results)
        
        # Create visualization data
        visualization_data = self._create_visualization_data(
            government_data, satellite_data, violation_results
        )
        
        return {
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'analysis_summary': {
                'total_official_leases': gov_summary.get('total_leases', 0),
                'total_satellite_areas': sat_summary['total_mining_areas'],
                'total_detected_area_hectares': total_detected_area,
                'legal_mining_area_hectares': total_legal_area,
                'illegal_mining_area_hectares': total_violation_area,
                'compliance_rate_percent': round(compliance_rate, 2),
                'violation_rate_percent': round(violation_rate, 2),
                'total_violations': violation_summary.get('total_violations', 0),
                'red_zones': violation_summary.get('red_zones', 0),
                'orange_zones': violation_summary.get('orange_zones', 0)
            },
            'government_data': government_data,
            'satellite_data': satellite_data,
            'violation_results': violation_results,
            'state_breakdown': state_breakdown,
            'priority_actions': priority_actions,
            'visualization_data': visualization_data,
            'recommendations': self._generate_recommendations(violation_results)
        }
    
    def _generate_state_breakdown(self, violation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate state-wise breakdown of violations"""
        state_breakdown = {}
        
        # Process violations by state
        violations = violation_results.get('violations', {})
        for severity, violation_list in violations.items():
            for violation in violation_list:
                # Extract state from satellite area
                satellite_area = violation.satellite_area
                region = satellite_area.get('region', 'Unknown')
                
                if region not in state_breakdown:
                    state_breakdown[region] = {
                        'total_violations': 0,
                        'total_area_hectares': 0,
                        'severity_breakdown': {
                            'critical': 0, 'high': 0, 'medium': 0, 'low': 0
                        }
                    }
                
                state_breakdown[region]['total_violations'] += 1
                state_breakdown[region]['total_area_hectares'] += violation.violation_area_hectares
                state_breakdown[region]['severity_breakdown'][severity] += 1
        
        return state_breakdown
    
    def _generate_priority_actions(self, violation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate priority actions based on violations"""
        priority_actions = []
        
        violations = violation_results.get('violations', {})
        
        # Critical violations - immediate action required
        critical_violations = violations.get('critical', [])
        if critical_violations:
            priority_actions.append({
                'priority': 'IMMEDIATE',
                'action': 'Critical Violations Detected',
                'count': len(critical_violations),
                'description': f'{len(critical_violations)} critical violations require immediate enforcement action',
                'recommended_actions': [
                    'Issue immediate cease and desist orders',
                    'Conduct emergency site inspections',
                    'Notify state mining department',
                    'Prepare legal action'
                ]
            })
        
        # High severity violations
        high_violations = violations.get('high', [])
        if high_violations:
            priority_actions.append({
                'priority': 'HIGH',
                'action': 'High Severity Violations',
                'count': len(high_violations),
                'description': f'{len(high_violations)} high severity violations need urgent attention',
                'recommended_actions': [
                    'Issue warning notices',
                    'Schedule site inspections within 48 hours',
                    'Review mining permits',
                    'Notify district mining officers'
                ]
            })
        
        # Medium and low violations
        medium_low_count = len(violations.get('medium', [])) + len(violations.get('low', []))
        if medium_low_count > 0:
            priority_actions.append({
                'priority': 'MEDIUM',
                'action': 'Moderate Violations',
                'count': medium_low_count,
                'description': f'{medium_low_count} moderate violations require monitoring and verification',
                'recommended_actions': [
                    'Conduct site verifications',
                    'Review boundary documentation',
                    'Issue compliance notices if needed',
                    'Monitor for compliance'
                ]
            })
        
        return priority_actions
    
    def _create_visualization_data(self, government_data: Dict[str, Any], 
                                 satellite_data: Dict[str, Any], 
                                 violation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create data for visualization"""
        
        # Extract violation zones
        violation_zones = violation_results.get('violation_zones', {})
        red_zones = violation_zones.get('red_zones', [])
        orange_zones = violation_zones.get('orange_zones', [])
        
        # Create GeoJSON for visualization
        red_zones_geojson = {
            'type': 'FeatureCollection',
            'features': []
        }
        
        orange_zones_geojson = {
            'type': 'FeatureCollection',
            'features': []
        }
        
        # Process red zones
        for zone in red_zones:
            red_zones_geojson['features'].append({
                'type': 'Feature',
                'properties': {
                    'id': zone['id'],
                    'severity': zone['severity'],
                    'area_hectares': zone['area_hectares'],
                    'description': zone['description'],
                    'confidence': zone['confidence'],
                    'zone_type': 'red'
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [zone['coordinates']]
                }
            })
        
        # Process orange zones
        for zone in orange_zones:
            orange_zones_geojson['features'].append({
                'type': 'Feature',
                'properties': {
                    'id': zone['id'],
                    'severity': zone['severity'],
                    'area_hectares': zone['area_hectares'],
                    'description': zone['description'],
                    'confidence': zone['confidence'],
                    'zone_type': 'orange'
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [zone['coordinates']]
                }
            })
        
        return {
            'red_zones_geojson': red_zones_geojson,
            'orange_zones_geojson': orange_zones_geojson,
            'total_red_zones': len(red_zones),
            'total_orange_zones': len(orange_zones),
            'red_zones_area_hectares': sum(zone['area_hectares'] for zone in red_zones),
            'orange_zones_area_hectares': sum(zone['area_hectares'] for zone in orange_zones)
        }
    
    def _generate_recommendations(self, violation_results: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        
        violation_summary = violation_results.get('analysis_summary', {})
        total_violations = violation_summary.get('total_violations', 0)
        red_zones = violation_summary.get('red_zones', 0)
        orange_zones = violation_summary.get('orange_zones', 0)
        
        if total_violations == 0:
            recommendations.append("✅ No illegal mining violations detected - excellent compliance!")
            recommendations.append("Continue regular monitoring to maintain compliance")
        else:
            if red_zones > 0:
                recommendations.append(f"🚨 URGENT: {red_zones} red zones require immediate enforcement action")
                recommendations.append("Issue cease and desist orders for critical violations")
                recommendations.append("Conduct emergency site inspections")
            
            if orange_zones > 0:
                recommendations.append(f"⚠️ WARNING: {orange_zones} orange zones need monitoring and verification")
                recommendations.append("Schedule site inspections for warning zones")
                recommendations.append("Review boundary documentation accuracy")
            
            recommendations.append("Implement regular satellite monitoring program")
            recommendations.append("Establish automated violation detection system")
            recommendations.append("Train enforcement teams on new detection methods")
            recommendations.append("Create public awareness campaigns about illegal mining")
        
        return recommendations

# Standalone function for easy integration
async def run_illegal_mining_detection() -> Dict[str, Any]:
    """Run complete illegal mining detection analysis"""
    pipeline = IllegalMiningPipeline()
    return await pipeline.run_complete_analysis()

if __name__ == "__main__":
    # Test the complete pipeline
    async def main():
        pipeline = IllegalMiningPipeline()
        results = await pipeline.run_complete_analysis()
        
        print("🚀 Illegal Mining Detection Analysis Complete!")
        print(f"📊 Total violations detected: {results.get('analysis_summary', {}).get('total_violations', 0)}")
        print(f"🚨 Red zones: {results.get('analysis_summary', {}).get('red_zones', 0)}")
        print(f"⚠️ Orange zones: {results.get('analysis_summary', {}).get('orange_zones', 0)}")
    
    asyncio.run(main())
