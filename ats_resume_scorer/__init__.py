# ats_resume_scorer/__init__.py
"""
ATS Resume Scorer Plugin

A comprehensive Python-based plugin to score resumes against ATS standards
and job descriptions with actionable feedback.
"""

__version__ = "1.0.0"
__author__ = "Kumar Abhishek"
__email__ = "developer@kabhishek18.com"

# Core imports
from .main import ATSResumeScorer, ScoringWeights
from .parsers.resume_parser import (
    ResumeParser,
    ResumeData,
    ContactInfo,
    Experience,
    Education,
)
from .parsers.jd_parser import JobDescriptionParser, JobDescription
from .scoring.scoring_engine import ATSScoringEngine
from .utils.report_generator import ReportGenerator

# Make main classes available at package level
__all__ = [
    "ATSResumeScorer",
    "ScoringWeights",
    "ResumeParser",
    "ResumeData",
    "ContactInfo",
    "Experience",
    "Education",
    "JobDescriptionParser",
    "JobDescription",
    "ATSScoringEngine",
    "ReportGenerator",
]
