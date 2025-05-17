"""
PDF report generation utilities for Resume ATS Plugin.
"""

import os
from typing import Dict, Any
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from io import BytesIO

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, ListItem, 
    ListFlowable, PageBreak
)

def generate_pdf_report(analysis_result: Dict[str, Any], output_path: str) -> str:
    """
    Generate a comprehensive PDF report from the ATS analysis results.
    
    Args:
        analysis_result: The analysis result dictionary from ResumeATS
        output_path: Path where the PDF will be saved
        
    Returns:
        Path to the generated PDF file
    """
    # Create the PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading1_style = styles["Heading1"]
    heading2_style = styles["Heading2"]
    normal_style = styles["Normal"]
    
    # Create custom styles
    section_title_style = ParagraphStyle(
        name="SectionTitle",
        parent=heading2_style,
        textColor=colors.navy,
        fontSize=14,
        spaceAfter=12
    )
    
    bullet_style = ParagraphStyle(
        name="BulletPoint",
        parent=normal_style,
        leftIndent=20,
        firstLineIndent=0,
        spaceBefore=2,
        spaceAfter=2
    )
    
    # Content elements
    elements = []
    
    # Title
    elements.append(Paragraph("ATS Resume Analysis Report", title_style))
    elements.append(Spacer(1, 0.25 * inch))
    
    # Resume file info
    elements.append(Paragraph(f"Resume: {analysis_result.get('resume_file', 'Unknown')}", normal_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Executive summary
    elements.append(Paragraph("Executive Summary", heading1_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Overall ATS score
    if "stats" in analysis_result and "overall_ats_score" in analysis_result["stats"]:
        score = analysis_result["stats"]["overall_ats_score"]
        score_chart = _create_score_chart(score)
        elements.append(Paragraph(f"Overall ATS Score: {score}%", heading2_style))
        elements.append(Image(score_chart, width=4*inch, height=3*inch))
    
    # Key metrics
    if "stats" in analysis_result:
        elements.append(Paragraph("Key Metrics", section_title_style))
        stats = analysis_result["stats"]
        
        data = []
        headers = ["Metric", "Value"]
        data.append(headers)
        
        # Format score is always there
        if "format_score" in stats:
            data.append(["Format Score", f"{stats['format_score']:.2f}"])
        
        if "readability_score" in stats:
            data.append(["Readability Score", f"{stats['readability_score']:.2f}"])
        
        if "keyword_match_score" in stats:
            data.append(["Keyword Match Score", f"{stats['keyword_match_score']:.2f}"])
        
        if "word_count" in stats:
            data.append(["Word Count", stats["word_count"]])
            
        # Create table
        table = Table(data, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.25 * inch))
    
    # Detected sections
    if "sections_detected" in analysis_result:
        elements.append(Paragraph("Detected Resume Sections", section_title_style))
        sections = analysis_result["sections_detected"]
        
        if sections:
            items = []
            for section in sections:
                items.append(ListItem(Paragraph(section.title(), bullet_style)))
            elements.append(ListFlowable(items, bulletType='bullet'))
        else:
            elements.append(Paragraph("No sections were detected. Make sure your resume has clear section headers.", normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
    
    # Keyword analysis (if job description was provided)
    if "stats" in analysis_result and "keyword_matches" in analysis_result["stats"]:
        elements.append(Paragraph("Keyword Analysis", heading1_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Matched keywords
        elements.append(Paragraph("Matched Keywords", section_title_style))
        matched = analysis_result["stats"]["keyword_matches"]
        
        if matched:
            word_table_data = []
            row = []
            for i, word in enumerate(matched):
                row.append(word)
                if (i + 1) % 3 == 0 or i == len(matched) - 1:
                    while len(row) < 3:
                        row.append("")
                    word_table_data.append(row)
                    row = []
            
            if word_table_data:
                keyword_table = Table(word_table_data, colWidths=[2*inch, 2*inch, 2*inch])
                keyword_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightgreen),
                ]))
                elements.append(keyword_table)
        else:
            elements.append(Paragraph("No keyword matches found.", normal_style))
        
        elements.append(Spacer(1, 0.15 * inch))
        
        # Missing keywords
        if "missing_keywords" in analysis_result["stats"]:
            elements.append(Paragraph("Missing Keywords", section_title_style))
            missing = analysis_result["stats"]["missing_keywords"]
            
            if missing:
                word_table_data = []
                row = []
                for i, word in enumerate(missing):
                    row.append(word)
                    if (i + 1) % 3 == 0 or i == len(missing) - 1:
                        while len(row) < 3:
                            row.append("")
                        word_table_data.append(row)
                        row = []
                
                if word_table_data:
                    missing_table = Table(word_table_data, colWidths=[2*inch, 2*inch, 2*inch])
                    missing_table.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                        ('BACKGROUND', (0, 0), (-1, -1), colors.salmon),
                    ]))
                    elements.append(missing_table)
            else:
                elements.append(Paragraph("No missing keywords found.", normal_style))
            
            elements.append(Spacer(1, 0.25 * inch))
    
    # Suggestions
    if "suggestions" in analysis_result:
        elements.append(Paragraph("Improvement Suggestions", heading1_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        suggestions = analysis_result["suggestions"]
        if suggestions:
            items = []
            for suggestion in suggestions:
                items.append(ListItem(Paragraph(suggestion["message"], bullet_style)))
            elements.append(ListFlowable(items, bulletType='bullet'))
        else:
            elements.append(Paragraph("No specific suggestions to improve your resume.", normal_style))
    
    # Add optimization suggestions if present
    if "optimization_suggestions" in analysis_result:
        elements.append(PageBreak())
        elements.append(Paragraph("Optimization Plan", heading1_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        opt_suggestions = analysis_result["optimization_suggestions"]
        if opt_suggestions:
            for i, suggestion in enumerate(opt_suggestions):
                elements.append(Paragraph(f"{i+1}. {suggestion['type'].replace('_', ' ').title()}", section_title_style))
                elements.append(Paragraph(suggestion["message"], normal_style))
                elements.append(Spacer(1, 0.1 * inch))
                
                # If there are keywords, list them
                if "keywords" in suggestion:
                    items = []
                    for keyword in suggestion["keywords"]:
                        items.append(ListItem(Paragraph(keyword, bullet_style)))
                    elements.append(ListFlowable(items, bulletType='bullet'))
                
                elements.append(Spacer(1, 0.1 * inch))
        else:
            elements.append(Paragraph("No optimization suggestions available.", normal_style))
    
    # Footer with time stamp
    import datetime
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(f"Report generated on {date_string}", ParagraphStyle(
        name="Footer",
        parent=normal_style,
        alignment=1,  # Center alignment
        textColor=colors.grey
    )))
    
    # Build the document
    doc.build(elements)
    
    return output_path

def _create_score_chart(score: int) -> BytesIO:
    """
    Create a gauge chart for the ATS score.
    
    Args:
        score: Score value (0-100)
        
    Returns:
        BytesIO object containing the chart image
    """
    plt.figure(figsize=(6, 4))
    
    # Create gauge chart
    angle = np.linspace(0, 180, 100)
    val = np.linspace(0, 100, 100)
    
    # Set up the colormap
    cmap = plt.cm.RdYlGn
    norm = plt.Normalize(0, 100)
    
    # Create the gauge
    plt.subplot(1, 1, 1, polar=True)
    plt.bar(
        np.deg2rad(angle), 
        [1] * len(angle), 
        width=np.deg2rad(180/99), 
        bottom=2, 
        color=cmap(norm(val))
    )
    
    # Mark the score
    score_angle = np.deg2rad(180 * score / 100)
    plt.plot([0, score_angle], [0, 2.5], 'k-', linewidth=3)
    plt.plot([0], [0], 'ko', markersize=10)
    
    # Customize the chart
    plt.axis('off')
    
    # Add score text
    plt.text(0, 1, f"{score}%", fontsize=24, ha='center', va='center', weight='bold')
    
    # Add score ranges
    plt.text(np.deg2rad(160), 2.7, 'Excellent', fontsize=10, ha='right')
    plt.text(np.deg2rad(125), 2.7, 'Good', fontsize=10, ha='right')
    plt.text(np.deg2rad(90), 2.7, 'Average', fontsize=10, ha='center')
    plt.text(np.deg2rad(55), 2.7, 'Poor', fontsize=10, ha='left')
    plt.text(np.deg2rad(20), 2.7, 'Critical', fontsize=10, ha='left')
    
    # Add text guidance based on score
    guidance = ""
    if score >= 90:
        guidance = "Your resume is extremely well-optimized for ATS"
    elif score >= 80:
        guidance = "Your resume is well-optimized with minor improvements needed"
    elif score >= 70:
        guidance = "Your resume is adequately optimized but needs some improvements"
    elif score >= 50:
        guidance = "Your resume needs significant improvements for ATS"
    else:
        guidance = "Your resume requires major revision for ATS compatibility"
    
    plt.figtext(0.5, 0.05, guidance, ha='center', fontsize=11)
    
    # Save to BytesIO
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close()
    
    buf.seek(0)
    return buf
