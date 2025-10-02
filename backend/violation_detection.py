"""
Illegal Mining Violation Detection System
Compares satellite-detected mining areas with official government boundaries
Identifies red zones (critical violations) and orange zones (warning violations)
"""

import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import numpy as np
from dataclasses import dataclass
from enum import Enum
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ViolationSeverity(Enum):
    """Violation severity levels"""
    NONE = "none"
    LOW = "low"          # Orange zone
    MEDIUM = "medium"    # Orange zone
    HIGH = "high"        # Red zone
    CRITICAL = "critical" # Red zone

@dataclass
class MiningViolation:
    """Represents a mining violation"""
    id: str
    violation_type: str
    severity: ViolationSeverity
    satellite_area: Dict[str, Any]
    official_boundary: Optional[Dict[str, Any]]
    overlap_percentage: float
    violation_area_hectares: float
    coordinates: List[List[float]]
    confidence: float
    description: str
    recommendations: List[str]

class ViolationDetector:
    """Detects illegal mining violations by comparing satellite data with official boundaries"""
    
    def __init__(self):
        """Initialize violation detection system"""
        self.violation_thresholds = {
            'overlap_min': 0.1,      # Minimum overlap to consider violation
            'area_min_hectares': 5.0, # Minimum area for violation
            'confidence_min': 0.6,   # Minimum confidence for violation
            'severity_thresholds': {
                'critical': 0.9,     # >90% overlap = critical
                'high': 0.7,         # 70-90% overlap = high
                'medium': 0.5,       # 50-70% overlap = medium
                'low': 0.1           # 10-50% overlap = low
            }
        }
        
        logger.info("Violation Detection system initialized")
    
    async def detect_violations(self, satellite_data: Dict[str, Any], 
                              government_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect illegal mining violations by comparing satellite and government data
        
        Args:
            satellite_data: Satellite-detected mining areas
            government_data: Official government mining boundaries
            
        Returns:
            Dict: Detected violations with severity classification
        """
        try:
            logger.info("Starting violation detection analysis...")
            
            # Extract mining areas and boundaries
            satellite_areas = satellite_data.get('mining_areas', [])
            official_boundaries = self._extract_official_boundaries(government_data)
            
            logger.info(f"Analyzing {len(satellite_areas)} satellite areas against {len(official_boundaries)} official boundaries")
            
            # Detect violations
            violations = []
            legal_areas = []
            
            for satellite_area in satellite_areas:
                violation_result = await self._analyze_satellite_area(
                    satellite_area, official_boundaries
                )
                
                if violation_result['is_violation']:
                    violations.append(violation_result['violation'])
                else:
                    legal_areas.append(violation_result['legal_area'])
            
            # Classify violations by severity
            classified_violations = self._classify_violations(violations)
            
            # Generate summary statistics
            summary = self._generate_violation_summary(classified_violations, legal_areas)
            
            # Create violation zones for visualization
            violation_zones = self._create_violation_zones(classified_violations)
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'analysis_summary': summary,
                'violations': classified_violations,
                'legal_areas': legal_areas,
                'violation_zones': violation_zones,
                'total_violations': len(violations),
                'total_legal_areas': len(legal_areas),
                'violation_rate': len(violations) / max(len(satellite_areas), 1) * 100
            }
            
            logger.info(f"Detection complete: {len(violations)} violations, {len(legal_areas)} legal areas")
            return result
            
        except Exception as e:
            logger.error(f"Error in violation detection: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'violations': [],
                'legal_areas': [],
                'violation_zones': {'red_zones': [], 'orange_zones': []}
            }
    
    def _extract_official_boundaries(self, government_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract official mining boundaries from government data"""
        boundaries = []
        
        # Extract from different sources
        sources = government_data.get('sources', {})
        
        # From IBM data
        if 'ibm' in sources and 'leases' in sources['ibm']:
            for lease in sources['ibm']['leases']:
                if 'geometry' in lease:
                    boundaries.append({
                        'id': lease.get('lease_id', ''),
                        'name': lease.get('lease_name', ''),
                        'state': lease.get('state', ''),
                        'mineral': lease.get('mineral', ''),
                        'area_hectares': lease.get('area_hectares', 0),
                        'geometry': lease['geometry'],
                        'source': 'IBM'
                    })
        
        # From WMS boundaries
        if 'boundaries' in sources and 'features' in sources['boundaries']:
            for feature in sources['boundaries']['features']:
                boundaries.append({
                    'id': feature.get('properties', {}).get('id', ''),
                    'name': feature.get('properties', {}).get('name', ''),
                    'state': feature.get('properties', {}).get('state', ''),
                    'mineral': feature.get('properties', {}).get('mineral', ''),
                    'area_hectares': feature.get('properties', {}).get('area_hectares', 0),
                    'geometry': feature.get('geometry', {}),
                    'source': 'WMS'
                })
        
        return boundaries
    
    async def _analyze_satellite_area(self, satellite_area: Dict[str, Any], 
                                    official_boundaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a single satellite area for violations"""
        try:
            satellite_geometry = satellite_area.get('geometry', {})
            satellite_coords = self._extract_coordinates(satellite_geometry)
            
            if not satellite_coords:
                return {
                    'is_violation': False,
                    'legal_area': satellite_area,
                    'violation': None
                }
            
            # Find overlapping official boundaries
            overlaps = []
            
            for boundary in official_boundaries:
                boundary_coords = self._extract_coordinates(boundary.get('geometry', {}))
                
                if boundary_coords:
                    overlap = self._calculate_overlap(satellite_coords, boundary_coords)
                    
                    if overlap > 0:
                        overlaps.append({
                            'boundary': boundary,
                            'overlap_percentage': overlap,
                            'overlap_area_hectares': overlap * satellite_area['area_hectares']
                        })
            
            # Determine if this is a violation
            if not overlaps:
                # No official boundary found - potential violation
                violation = self._create_violation(
                    satellite_area, None, 0.0, "No official boundary found"
                )
                return {
                    'is_violation': True,
                    'legal_area': None,
                    'violation': violation
                }
            
            # Check if satellite area extends beyond official boundaries
            max_overlap = max(overlaps, key=lambda x: x['overlap_percentage'])
            
            if max_overlap['overlap_percentage'] < 1.0:
                # Partial overlap - potential violation
                violation_area = satellite_area['area_hectares'] - max_overlap['overlap_area_hectares']
                
                if violation_area > self.violation_thresholds['area_min_hectares']:
                    violation = self._create_violation(
                        satellite_area, max_overlap['boundary'], 
                        max_overlap['overlap_percentage'], 
                        f"Extends beyond official boundary by {violation_area:.1f} hectares"
                    )
                    return {
                        'is_violation': True,
                        'legal_area': None,
                        'violation': violation
                    }
            
            # Area is within official boundaries - legal
            legal_area = {
                **satellite_area,
                'official_boundary': max_overlap['boundary'],
                'overlap_percentage': max_overlap['overlap_percentage'],
                'status': 'legal'
            }
            
            return {
                'is_violation': False,
                'legal_area': legal_area,
                'violation': None
            }
            
        except Exception as e:
            logger.error(f"Error analyzing satellite area: {e}")
            return {
                'is_violation': False,
                'legal_area': satellite_area,
                'violation': None
            }
    
    def _extract_coordinates(self, geometry: Dict[str, Any]) -> Optional[List[List[float]]]:
        """Extract coordinates from geometry"""
        try:
            if geometry.get('type') == 'Polygon':
                return geometry.get('coordinates', [[]])[0]
            elif geometry.get('type') == 'MultiPolygon':
                # Return the largest polygon
                polygons = geometry.get('coordinates', [])
                if polygons:
                    return max(polygons, key=len)[0]
            return None
        except Exception as e:
            logger.error(f"Error extracting coordinates: {e}")
            return None
    
    def _calculate_overlap(self, coords1: List[List[float]], coords2: List[List[float]]) -> float:
        """Calculate overlap percentage between two polygons"""
        try:
            # Simplified overlap calculation
            # In a real implementation, you would use proper geometric libraries
            
            # Get bounding boxes
            bbox1 = self._get_bounding_box(coords1)
            bbox2 = self._get_bounding_box(coords2)
            
            # Calculate bounding box overlap
            overlap_bbox = self._get_bbox_overlap(bbox1, bbox2)
            
            if not overlap_bbox:
                return 0.0
            
            # Calculate areas
            area1 = self._calculate_polygon_area(coords1)
            area2 = self._calculate_polygon_area(coords2)
            overlap_area = self._calculate_bbox_area(overlap_bbox)
            
            if area1 == 0:
                return 0.0
            
            # Return overlap percentage
            return min(overlap_area / area1, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating overlap: {e}")
            return 0.0
    
    def _get_bounding_box(self, coords: List[List[float]]) -> Dict[str, float]:
        """Get bounding box for coordinates"""
        if not coords:
            return {'min_lon': 0, 'max_lon': 0, 'min_lat': 0, 'max_lat': 0}
        
        lons = [coord[0] for coord in coords]
        lats = [coord[1] for coord in coords]
        
        return {
            'min_lon': min(lons),
            'max_lon': max(lons),
            'min_lat': min(lats),
            'max_lat': max(lats)
        }
    
    def _get_bbox_overlap(self, bbox1: Dict[str, float], bbox2: Dict[str, float]) -> Optional[Dict[str, float]]:
        """Get overlapping bounding box"""
        overlap = {
            'min_lon': max(bbox1['min_lon'], bbox2['min_lon']),
            'max_lon': min(bbox1['max_lon'], bbox2['max_lon']),
            'min_lat': max(bbox1['min_lat'], bbox2['min_lat']),
            'max_lat': min(bbox1['max_lat'], bbox2['max_lat'])
        }
        
        if overlap['min_lon'] >= overlap['max_lon'] or overlap['min_lat'] >= overlap['max_lat']:
            return None
        
        return overlap
    
    def _calculate_polygon_area(self, coords: List[List[float]]) -> float:
        """Calculate polygon area using shoelace formula"""
        if len(coords) < 3:
            return 0.0
        
        area = 0.0
        n = len(coords)
        
        for i in range(n):
            j = (i + 1) % n
            area += coords[i][0] * coords[j][1]
            area -= coords[j][0] * coords[i][1]
        
        return abs(area) / 2.0
    
    def _calculate_bbox_area(self, bbox: Dict[str, float]) -> float:
        """Calculate bounding box area"""
        return (bbox['max_lon'] - bbox['min_lon']) * (bbox['max_lat'] - bbox['min_lat'])
    
    def _create_violation(self, satellite_area: Dict[str, Any], 
                         official_boundary: Optional[Dict[str, Any]], 
                         overlap_percentage: float, description: str) -> MiningViolation:
        """Create a mining violation object"""
        
        # Calculate violation area
        if official_boundary:
            violation_area = satellite_area['area_hectares'] * (1 - overlap_percentage)
        else:
            violation_area = satellite_area['area_hectares']
        
        # Determine severity
        if overlap_percentage == 0:
            severity = ViolationSeverity.CRITICAL
        elif overlap_percentage < 0.1:
            severity = ViolationSeverity.HIGH
        elif overlap_percentage < 0.5:
            severity = ViolationSeverity.MEDIUM
        else:
            severity = ViolationSeverity.LOW
        
        # Generate recommendations
        recommendations = self._generate_recommendations(severity, violation_area)
        
        return MiningViolation(
            id=f"violation_{int(datetime.now().timestamp())}_{len(satellite_area.get('id', ''))}",
            violation_type="illegal_mining",
            severity=severity,
            satellite_area=satellite_area,
            official_boundary=official_boundary,
            overlap_percentage=overlap_percentage,
            violation_area_hectares=round(violation_area, 2),
            coordinates=self._extract_coordinates(satellite_area.get('geometry', {})),
            confidence=satellite_area.get('confidence', 0.5),
            description=description,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, severity: ViolationSeverity, area_hectares: float) -> List[str]:
        """Generate recommendations based on violation severity"""
        recommendations = []
        
        if severity == ViolationSeverity.CRITICAL:
            recommendations.extend([
                "Immediate cease and desist order required",
                "Issue stop work notice to mining operators",
                "Conduct immediate site inspection",
                "Prepare legal action against violators",
                "Notify state mining department"
            ])
        elif severity == ViolationSeverity.HIGH:
            recommendations.extend([
                "Issue warning notice to operators",
                "Schedule site inspection within 48 hours",
                "Review mining permit status",
                "Notify district mining officer"
            ])
        elif severity == ViolationSeverity.MEDIUM:
            recommendations.extend([
                "Conduct site verification",
                "Review boundary documentation",
                "Issue compliance notice if needed"
            ])
        else:
            recommendations.extend([
                "Monitor area for compliance",
                "Verify boundary accuracy"
            ])
        
        if area_hectares > 50:
            recommendations.append("Large-scale violation - prioritize enforcement action")
        
        return recommendations
    
    def _classify_violations(self, violations: List[MiningViolation]) -> Dict[str, List[MiningViolation]]:
        """Classify violations by severity"""
        classified = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for violation in violations:
            severity_key = violation.severity.value
            if severity_key in classified:
                classified[severity_key].append(violation)
        
        return classified
    
    def _generate_violation_summary(self, classified_violations: Dict[str, List[MiningViolation]], 
                                  legal_areas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_violations = sum(len(violations) for violations in classified_violations.values())
        total_violation_area = sum(
            sum(violation.violation_area_hectares for violation in violations)
            for violations in classified_violations.values()
        )
        
        total_legal_area = sum(area.get('area_hectares', 0) for area in legal_areas)
        
        return {
            'total_violations': total_violations,
            'total_violation_area_hectares': round(total_violation_area, 2),
            'total_legal_area_hectares': round(total_legal_area, 2),
            'violation_breakdown': {
                'critical': len(classified_violations['critical']),
                'high': len(classified_violations['high']),
                'medium': len(classified_violations['medium']),
                'low': len(classified_violations['low'])
            },
            'red_zones': len(classified_violations['critical']) + len(classified_violations['high']),
            'orange_zones': len(classified_violations['medium']) + len(classified_violations['low'])
        }
    
    def _create_violation_zones(self, classified_violations: Dict[str, List[MiningViolation]]) -> Dict[str, List[Dict[str, Any]]]:
        """Create violation zones for visualization"""
        red_zones = []
        orange_zones = []
        
        # Red zones: Critical and High severity
        for violation in classified_violations['critical'] + classified_violations['high']:
            red_zones.append({
                'id': violation.id,
                'severity': violation.severity.value,
                'area_hectares': violation.violation_area_hectares,
                'coordinates': violation.coordinates,
                'description': violation.description,
                'recommendations': violation.recommendations,
                'confidence': violation.confidence
            })
        
        # Orange zones: Medium and Low severity
        for violation in classified_violations['medium'] + classified_violations['low']:
            orange_zones.append({
                'id': violation.id,
                'severity': violation.severity.value,
                'area_hectares': violation.violation_area_hectares,
                'coordinates': violation.coordinates,
                'description': violation.description,
                'recommendations': violation.recommendations,
                'confidence': violation.confidence
            })
        
        return {
            'red_zones': red_zones,
            'orange_zones': orange_zones
        }

# Standalone function for easy integration
async def detect_mining_violations(satellite_data: Dict[str, Any], 
                                 government_data: Dict[str, Any]) -> Dict[str, Any]:
    """Detect mining violations by comparing satellite and government data"""
    detector = ViolationDetector()
    return await detector.detect_violations(satellite_data, government_data)

if __name__ == "__main__":
    # Test the violation detection
    async def main():
        # Mock data for testing
        satellite_data = {'mining_areas': []}
        government_data = {'sources': {}}
        
        detector = ViolationDetector()
        results = await detector.detect_violations(satellite_data, government_data)
        print(f"Detected {results['total_violations']} violations")
    
    asyncio.run(main())
