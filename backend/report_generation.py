"""
Report Generation Module for Illegal Mining Detection
Generates comprehensive PDF reports with statistics, maps, and figures
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Report generation libraries
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportGenerator:
    """Handles generation of comprehensive PDF reports"""
    
    def __init__(self, 
                 report_title: str = "Illegal Mining Detection Report",
                 company_name: str = "Mining Detection System"):
        """
        Initialize report generator
        
        Args:
            report_title: Title of the report
            company_name: Name of the company/organization
        """
        self.report_title = report_title
        self.company_name = company_name
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self._create_custom_styles()
        
        logger.info(f"Report generator initialized: {report_title}")
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for the report"""
        try:
            # Title style
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            ))
            
            # Subtitle style
            self.styles.add(ParagraphStyle(
                name='CustomSubtitle',
                parent=self.styles['Heading2'],
                fontSize=16,
                spaceAfter=20,
                alignment=TA_LEFT,
                textColor=colors.darkgreen
            ))
            
            # Summary style
            self.styles.add(ParagraphStyle(
                name='Summary',
                parent=self.styles['Normal'],
                fontSize=12,
                spaceAfter=12,
                alignment=TA_LEFT,
                textColor=colors.black,
                backColor=colors.lightgrey,
                borderPadding=10
            ))
            
            # Statistics style
            self.styles.add(ParagraphStyle(
                name='Statistics',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                alignment=TA_LEFT,
                textColor=colors.darkred
            ))
            
        except Exception as e:
            logger.error(f"Error creating custom styles: {e}")
            raise
    
    def create_executive_summary(self, 
                               stats: Dict[str, Any],
                               volume_stats: Dict[str, Any]) -> List:
        """
        Create executive summary section
        
        Args:
            stats: Mining detection statistics
            volume_stats: Volume estimation statistics
            
        Returns:
            List: Report elements for executive summary
        """
        try:
            elements = []
            
            # Executive Summary title
            elements.append(Paragraph("Executive Summary", self.styles['CustomSubtitle']))
            elements.append(Spacer(1, 12))
            
            # Summary text
            total_mining_area = stats.get('total_mining', {}).get('area_ha', 0)
            illegal_area = stats.get('illegal_mining', {}).get('area_ha', 0)
            illegal_percentage = stats.get('illegal_mining', {}).get('percentage', 0)
            total_volume = volume_stats.get('total_volume_m3', 0)
            avg_depth = volume_stats.get('average_depth_m', 0)
            
            summary_text = f"""
            This report presents the results of illegal mining detection analysis conducted using 
            satellite imagery and digital elevation models. The analysis identified a total mining 
            area of {total_mining_area:.2f} hectares, of which {illegal_area:.2f} hectares 
            ({illegal_percentage:.1f}%) are classified as illegal mining activities outside 
            designated lease boundaries. The estimated total volume of extracted material is 
            {total_volume:,.0f} cubic meters, with an average mining depth of {avg_depth:.2f} meters.
            """
            
            elements.append(Paragraph(summary_text, self.styles['Summary']))
            elements.append(Spacer(1, 20))
            
            return elements
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {e}")
            raise
    
    def create_statistics_table(self, 
                               stats: Dict[str, Any],
                               volume_stats: Dict[str, Any]) -> Table:
        """
        Create statistics table
        
        Args:
            stats: Mining detection statistics
            volume_stats: Volume estimation statistics
            
        Returns:
            Table: Statistics table
        """
        try:
            # Prepare data for table
            data = [
                ['Parameter', 'Value', 'Unit'],
                ['', '', ''],
                ['MINING AREA STATISTICS', '', ''],
                ['Legal Mining Areas', f"{stats.get('legal_mining', {}).get('count', 0)}", 'count'],
                ['Legal Mining Area', f"{stats.get('legal_mining', {}).get('area_ha', 0):.2f}", 'hectares'],
                ['Legal Mining Percentage', f"{stats.get('legal_mining', {}).get('percentage', 0):.1f}", '%'],
                ['', '', ''],
                ['Illegal Mining Areas', f"{stats.get('illegal_mining', {}).get('count', 0)}", 'count'],
                ['Illegal Mining Area', f"{stats.get('illegal_mining', {}).get('area_ha', 0):.2f}", 'hectares'],
                ['Illegal Mining Percentage', f"{stats.get('illegal_mining', {}).get('percentage', 0):.1f}", '%'],
                ['', '', ''],
                ['VOLUME ESTIMATION', '', ''],
                ['Total Volume', f"{volume_stats.get('total_volume_m3', 0):,.0f}", 'm³'],
                ['Simpson Volume', f"{volume_stats.get('simpsons_volume_m3', 0):,.0f}", 'm³'],
                ['Average Depth', f"{volume_stats.get('average_depth_m', 0):.2f}", 'meters'],
                ['Maximum Depth', f"{volume_stats.get('max_depth_m', 0):.2f}", 'meters'],
                ['Mining Area', f"{volume_stats.get('mining_area_ha', 0):.2f}", 'hectares']
            ]
            
            # Create table
            table = Table(data, colWidths=[2.5*inch, 1.5*inch, 0.8*inch])
            
            # Apply table style
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 10),
                ('BACKGROUND', (0, 2), (-1, 2), colors.darkblue),
                ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
                ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 2), (-1, 2), 11),
                ('BACKGROUND', (0, 7), (-1, 7), colors.darkred),
                ('TEXTCOLOR', (0, 7), (-1, 7), colors.white),
                ('FONTNAME', (0, 7), (-1, 7), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 7), (-1, 7), 11),
                ('BACKGROUND', (0, 12), (-1, 12), colors.darkgreen),
                ('TEXTCOLOR', (0, 12), (-1, 12), colors.white),
                ('FONTNAME', (0, 12), (-1, 12), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 12), (-1, 12), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            return table
            
        except Exception as e:
            logger.error(f"Error creating statistics table: {e}")
            raise
    
    def add_image_to_report(self, 
                          image_path: str, 
                          caption: str,
                          width: float = 6*inch,
                          height: float = 4*inch) -> List:
        """
        Add image to report with caption
        
        Args:
            image_path: Path to image file
            caption: Image caption
            width: Image width
            height: Image height
            
        Returns:
            List: Report elements for image
        """
        try:
            elements = []
            
            if os.path.exists(image_path):
                # Add image
                img = Image(image_path, width=width, height=height)
                elements.append(img)
                elements.append(Spacer(1, 6))
                
                # Add caption
                elements.append(Paragraph(f"<i>{caption}</i>", self.styles['Normal']))
                elements.append(Spacer(1, 12))
            else:
                logger.warning(f"Image not found: {image_path}")
                elements.append(Paragraph(f"[Image not available: {caption}]", self.styles['Normal']))
                elements.append(Spacer(1, 12))
            
            return elements
            
        except Exception as e:
            logger.error(f"Error adding image to report: {e}")
            raise
    
    def create_compliance_analysis(self, 
                                 stats: Dict[str, Any]) -> List:
        """
        Create compliance analysis section
        
        Args:
            stats: Mining detection statistics
            
        Returns:
            List: Report elements for compliance analysis
        """
        try:
            elements = []
            
            # Compliance Analysis title
            elements.append(Paragraph("Compliance Analysis", self.styles['CustomSubtitle']))
            elements.append(Spacer(1, 12))
            
            # Calculate compliance metrics
            legal_percentage = stats.get('legal_mining', {}).get('percentage', 0)
            illegal_percentage = stats.get('illegal_mining', {}).get('percentage', 0)
            
            # Compliance status
            if legal_percentage >= 95:
                compliance_status = "COMPLIANT"
                status_color = "green"
            elif legal_percentage >= 80:
                compliance_status = "PARTIALLY COMPLIANT"
                status_color = "orange"
            else:
                compliance_status = "NON-COMPLIANT"
                status_color = "red"
            
            compliance_text = f"""
            The mining activities in the analyzed area show a compliance rate of {legal_percentage:.1f}%, 
            with {illegal_percentage:.1f}% of mining activities occurring outside designated lease boundaries. 
            Based on these findings, the area is classified as <b style="color: {status_color}">{compliance_status}</b>.
            
            <br/><br/>
            <b>Key Findings:</b>
            <br/>• Total mining area: {stats.get('total_mining', {}).get('area_ha', 0):.2f} hectares
            <br/>• Legal mining area: {stats.get('legal_mining', {}).get('area_ha', 0):.2f} hectares
            <br/>• Illegal mining area: {stats.get('illegal_mining', {}).get('area_ha', 0):.2f} hectares
            <br/>• Number of illegal mining sites: {stats.get('illegal_mining', {}).get('count', 0)}
            """
            
            elements.append(Paragraph(compliance_text, self.styles['Normal']))
            elements.append(Spacer(1, 20))
            
            return elements
            
        except Exception as e:
            logger.error(f"Error creating compliance analysis: {e}")
            raise
    
    def create_recommendations(self, 
                             stats: Dict[str, Any]) -> List:
        """
        Create recommendations section
        
        Args:
            stats: Mining detection statistics
            
        Returns:
            List: Report elements for recommendations
        """
        try:
            elements = []
            
            # Recommendations title
            elements.append(Paragraph("Recommendations", self.styles['CustomSubtitle']))
            elements.append(Spacer(1, 12))
            
            illegal_percentage = stats.get('illegal_mining', {}).get('percentage', 0)
            
            if illegal_percentage > 20:
                recommendations_text = """
                <b>High Priority Actions Required:</b>
                <br/>• Immediate enforcement action against illegal mining activities
                <br/>• Strengthen monitoring and surveillance systems
                <br/>• Implement stricter penalties for violations
                <br/>• Regular satellite monitoring and ground verification
                <br/>• Community awareness programs about legal mining requirements
                """
            elif illegal_percentage > 10:
                recommendations_text = """
                <b>Moderate Priority Actions:</b>
                <br/>• Enhanced monitoring of mining activities
                <br/>• Regular compliance audits
                <br/>• Improved coordination between regulatory agencies
                <br/>• Training programs for mining operators
                <br/>• Periodic satellite monitoring
                """
            else:
                recommendations_text = """
                <b>Maintenance Actions:</b>
                <br/>• Continue regular monitoring
                <br/>• Maintain current enforcement levels
                <br/>• Periodic compliance reviews
                <br/>• Update monitoring protocols as needed
                """
            
            elements.append(Paragraph(recommendations_text, self.styles['Normal']))
            elements.append(Spacer(1, 20))
            
            return elements
            
        except Exception as e:
            logger.error(f"Error creating recommendations: {e}")
            raise
    
    def generate_report(self, 
                       output_path: str,
                       stats: Dict[str, Any],
                       volume_stats: Dict[str, Any],
                       image_paths: Optional[Dict[str, str]] = None) -> str:
        """
        Generate complete PDF report
        
        Args:
            output_path: Path to save PDF report
            stats: Mining detection statistics
            volume_stats: Volume estimation statistics
            image_paths: Dictionary of image paths for different sections
            
        Returns:
            str: Path to generated report
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build report content
            story = []
            
            # Title page
            story.append(Paragraph(self.report_title, self.styles['CustomTitle']))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Generated by: {self.company_name}", self.styles['Normal']))
            story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
            story.append(Spacer(1, 30))
            
            # Executive Summary
            story.extend(self.create_executive_summary(stats, volume_stats))
            
            # Statistics Table
            story.append(Paragraph("Detailed Statistics", self.styles['CustomSubtitle']))
            story.append(Spacer(1, 12))
            story.append(self.create_statistics_table(stats, volume_stats))
            story.append(Spacer(1, 20))
            
            # Add images if provided
            if image_paths:
                if 'mining_map' in image_paths:
                    story.extend(self.add_image_to_report(
                        image_paths['mining_map'], 
                        "Mining Detection Map showing legal and illegal mining areas"
                    ))
                
                if 'ndvi_bsi' in image_paths:
                    story.extend(self.add_image_to_report(
                        image_paths['ndvi_bsi'], 
                        "NDVI and BSI Analysis for mining area detection"
                    ))
                
                if 'depth_volume' in image_paths:
                    story.extend(self.add_image_to_report(
                        image_paths['depth_volume'], 
                        "Mining depth and volume analysis"
                    ))
                
                if '3d_visualization' in image_paths:
                    story.extend(self.add_image_to_report(
                        image_paths['3d_visualization'], 
                        "3D visualization of mining areas and terrain"
                    ))
            
            # Compliance Analysis
            story.extend(self.create_compliance_analysis(stats))
            
            # Recommendations
            story.extend(self.create_recommendations(stats))
            
            # Footer
            story.append(Spacer(1, 30))
            story.append(Paragraph("End of Report", self.styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise
    
    def create_summary_report(self, 
                            output_path: str,
                            all_results: Dict[str, Any]) -> str:
        """
        Create a summary report with all analysis results
        
        Args:
            output_path: Path to save summary report
            all_results: Dictionary containing all analysis results
            
        Returns:
            str: Path to generated summary report
        """
        try:
            # Extract statistics from results
            stats = all_results.get('illegal_mining_stats', {})
            volume_stats = all_results.get('volume_estimation', {})
            
            # Extract image paths
            image_paths = {
                'mining_map': all_results.get('mining_map_path'),
                'ndvi_bsi': all_results.get('ndvi_bsi_plot'),
                'depth_volume': all_results.get('depth_volume_plot'),
                '3d_visualization': all_results.get('3d_visualization_path')
            }
            
            # Generate report
            report_path = self.generate_report(
                output_path, stats, volume_stats, image_paths
            )
            
            logger.info(f"Summary report created: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error creating summary report: {e}")
            raise

def main():
    """Example usage of ReportGenerator class"""
    
    # Initialize report generator
    generator = ReportGenerator(
        report_title="Illegal Mining Detection Analysis Report",
        company_name="Smart India Hackathon Team"
    )
    
    print("Report Generation module ready!")
    print("Features:")
    print("- Executive summary generation")
    print("- Statistics tables")
    print("- Compliance analysis")
    print("- Recommendations")
    print("- Image integration")
    print("- Complete PDF report generation")

if __name__ == "__main__":
    main()
