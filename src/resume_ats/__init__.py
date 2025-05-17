"""
Resume ATS Plugin - Analyze and optimize resumes for Applicant Tracking Systems (ATS).
"""

__version__ = "0.2.0"

# Core functionality
from .core import ResumeATS, analyze_resume, optimize_resume

# Enhanced features 
from .enhanced import (
    EnhancedResumeATS, 
    analyze_and_report, 
    optimize_and_report
)

# PDF report generation
from .pdf_reporter import generate_pdf_report

# Resume anonymization
from .resume_anonymizer import (
    ResumeAnonymizer,
    anonymize_resume_text,
    anonymize_resume_file
)

# Version tracking
from .resume_version_tracker import ResumeVersionTracker

# Resume comparison
from .resume_comparer import (
    ResumeComparer,
    compare_resumes,
    compare_resume_to_jobs
)