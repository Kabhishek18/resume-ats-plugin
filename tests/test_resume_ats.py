"""
Unit tests for resume_ats plugin.
"""

import json
import os
import tempfile
from unittest import TestCase, mock

import pytest

from src.resume_ats import ResumeATS, analyze_resume, optimize_resume
from src.resume_ats.utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    normalize_text,
    get_keywords_from_job_description,
    calculate_similarity_score
)


class TestResumeATS(TestCase):
    """Test cases for the ResumeATS class."""
    
    def setUp(self):
        """Set up test environment."""
        self.sample_resume_text = """
        JOHN DOE
        Software Engineer
        john.doe@example.com | (123) 456-7890 | linkedin.com/in/johndoe

        SUMMARY
        Experienced software engineer with 5+ years developing web applications.

        EXPERIENCE
        Senior Software Engineer, ABC Tech Inc.
        2020 - Present
        • Led development of RESTful APIs using Python and Flask
        • Implemented CI/CD pipeline reducing deployment time by 40%
        • Mentored junior developers and conducted code reviews

        Software Engineer, XYZ Solutions
        2018 - 2020
        • Developed front-end components using React
        • Created unit tests increasing code coverage by 30%

        SKILLS
        Python, JavaScript, React, Flask, Docker, AWS, Git, CI/CD, Agile

        EDUCATION
        Bachelor of Science in Computer Science
        University of Technology, 2018
        """
        
        self.sample_job_description = """
        Software Engineer Position
        
        Requirements:
        - 3+ years experience in Python development
        - Experience with web frameworks (Flask or Django)
        - Knowledge of front-end technologies (React preferred)
        - Familiarity with Docker and containerization
        - Experience with CI/CD pipelines
        - Strong problem-solving and communication skills
        
        Responsibilities:
        - Develop and maintain web applications
        - Collaborate with cross-functional teams
        - Implement automated testing
        - Optimize application performance
        """
        
        # Create mock resume file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        self.temp_file.write(self.sample_resume_text.encode('utf-8'))
        self.temp_file.close()
        
        # Initialize ResumeATS
        self.ats = ResumeATS()
    
    def tearDown(self):
        """Clean up test environment."""
        os.unlink(self.temp_file.name)
    
    @mock.patch('src.resume_ats.core.ResumeATS._extract_text')
    def test_analyze_basic(self, mock_extract_text):
        """Test basic resume analysis."""
        mock_extract_text.return_value = self.sample_resume_text
        
        result = self.ats.analyze(self.temp_file.name)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("sections_detected", result)
        self.assertIn("stats", result)
        self.assertIn("suggestions", result)
        
        # Check if at least some sections were detected
        self.assertTrue(len(result["sections_detected"]) > 0)
        
        # Check if stats include word count and format score
        self.assertIn("word_count", result["stats"])
        self.assertIn("format_score", result["stats"])
    
    @mock.patch('src.resume_ats.core.ResumeATS._extract_text')
    def test_analyze_with_job_description(self, mock_extract_text):
        """Test resume analysis against job description."""
        mock_extract_text.return_value = self.sample_resume_text
        
        result = self.ats.analyze(self.temp_file.name, self.sample_job_description)
        
        self.assertEqual(result["status"], "success")
        
        # Check if job-specific metrics are included
        self.assertIn("keyword_match_score", result["stats"])
        self.assertIn("keyword_matches", result["stats"])
        self.assertIn("missing_keywords", result["stats"])
        self.assertIn("overall_ats_score", result["stats"])
        
        # Check if keyword matches include Python (which is in both resume and job)
        self.assertIn("python", [k.lower() for k in result["stats"]["keyword_matches"]])
    
    @mock.patch('src.resume_ats.core.ResumeATS._extract_text')
    def test_optimize(self, mock_extract_text):
        """Test resume optimization."""
        mock_extract_text.return_value = self.sample_resume_text
        
        result = self.ats.optimize(self.temp_file.name, self.sample_job_description)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("optimization_suggestions", result)
        self.assertIn("analysis", result)
        
        # Optimization suggestions should be a list
        self.assertIsInstance(result["optimization_suggestions"], list)
    
    def test_match_keywords(self):
        """Test keyword matching functionality."""
        keywords = ["python", "flask", "react", "nosql", "kubernetes"]
        text = "Experience with Python and Flask. Familiar with React."
        
        score, matches, missing = self.ats._match_keywords(text, keywords)
        
        # Check match score
        self.assertAlmostEqual(score, 0.6, delta=0.01)  # 3 out of 5 matches
        
        # Check matches list
        self.assertEqual(len(matches), 3)
        self.assertIn("python", [m.lower() for m in matches])
        self.assertIn("flask", [m.lower() for m in matches])
        
        # Check missing list
        self.assertEqual(len(missing), 2)
        self.assertIn("nosql", [m.lower() for m in missing])
        self.assertIn("kubernetes", [m.lower() for m in missing])
    
    def test_extract_sections(self):
        """Test section extraction."""
        sections = self.ats._extract_sections(self.sample_resume_text)
        
        # Check if main sections are detected
        self.assertIn("summary", sections)
        self.assertIn("experience", sections)
        self.assertIn("skills", sections)
        self.assertIn("education", sections)


class TestUtils(TestCase):
    """Test cases for utility functions."""
    
    def test_normalize_text(self):
        """Test text normalization."""
        text = "  This  is    a\n\n\ntest   with \t spaces \n and newlines.  "
        expected = "This is a\n\ntest with spaces and newlines."
        
        result = normalize_text(text)
        self.assertEqual(result, expected)
    
    def test_get_keywords_from_job_description(self):
        """Test keyword extraction from job description."""
        job_description = """
        Senior Developer Position
        
        Requirements:
        - 5+ years of experience with Python and Django
        - Strong knowledge of JavaScript and React
        - Experience with AWS cloud infrastructure
        - Familiarity with CI/CD pipelines and DevOps practices
        """
        
        keywords = get_keywords_from_job_description(job_description, max_keywords=10)
        
        # Check if important keywords are extracted
        self.assertTrue(any("python" in k.lower() for k in keywords))
        self.assertTrue(any("django" in k.lower() for k in keywords))
        self.assertTrue(any("react" in k.lower() for k in keywords))
        self.assertTrue(any("aws" in k.lower() for k in keywords))
    
    def test_calculate_similarity_score(self):
        """Test similarity score calculation."""
        text1 = "Python developer with Django and Flask experience"
        text2 = "Looking for Python developer familiar with Flask or Django"
        
        score = calculate_similarity_score(text1, text2)
        
        # Check if score is reasonable (should be relatively high)
        self.assertGreater(score, 0.5)
        self.assertLessEqual(score, 1.0)
        
        # Check different texts
        text3 = "Marketing specialist with SEO and content creation skills"
        score_different = calculate_similarity_score(text1, text3)
        
        # Score should be lower for dissimilar texts
        self.assertLess(score_different, score)


class TestFunctionsAPI(TestCase):
    """Test convenience function API."""
    
    @mock.patch('src.resume_ats.core.ResumeATS.analyze')
    def test_analyze_resume_function(self, mock_analyze):
        """Test analyze_resume convenience function."""
        mock_analyze.return_value = {"status": "success", "test": True}
        
        result = analyze_resume("fakepath.pdf", "job description", {"config": "value"})
        
        # Check if function returns expected result
        self.assertEqual(result, {"status": "success", "test": True})
        
        # Check if ResumeATS.analyze was called with correct arguments
        mock_analyze.assert_called_once_with("fakepath.pdf", "job description")
    
    @mock.patch('src.resume_ats.core.ResumeATS.optimize')
    def test_optimize_resume_function(self, mock_optimize):
        """Test optimize_resume convenience function."""
        mock_optimize.return_value = {"status": "success", "test": True}
        
        result = optimize_resume("fakepath.pdf", "job description", {"config": "value"})
        
        # Check if function returns expected result
        self.assertEqual(result, {"status": "success", "test": True})
        
        # Check if ResumeATS.optimize was called with correct arguments
        mock_optimize.assert_called_once_with("fakepath.pdf", "job description")


class TestCommandLine(TestCase):
    """Test command-line interface."""
    
    @mock.patch('src.resume_ats.core.analyze_resume')
    @mock.patch('argparse.ArgumentParser.parse_args')
def test_main_analyze(self, mock_parse_args, mock_analyze_resume):
        """Test main function with analyze mode."""
        # Mock arguments
        mock_args = mock.Mock()
        mock_args.resume = "resume.pdf"
        mock_args.job = None
        mock_args.optimize = False
        mock_args.config = None
        mock_args.output = None
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args
        
        # Mock analyze_resume return value
        mock_analyze_resume.return_value = {"status": "success", "test": True}
        
        # Run main
        from src.resume_ats.core import main
        with mock.patch("sys.stdout"):  # Capture stdout
            result = main()
        
        # Check if function returned successfully
        self.assertEqual(result, 0)
        
        # Check if analyze_resume was called with correct arguments
        mock_analyze_resume.assert_called_once_with("resume.pdf", None, None)
    
    @mock.patch('src.resume_ats.core.optimize_resume')
    @mock.patch('argparse.ArgumentParser.parse_args')
def test_main_optimize(self, mock_parse_args, mock_optimize_resume):
        """Test main function with optimize mode."""
        # Mock arguments
        mock_args = mock.Mock()
        mock_args.resume = "resume.pdf"
        mock_args.job = "job.txt"
        mock_args.optimize = True
        mock_args.config = None
        mock_args.output = "output.json"
        mock_args.log_level = "INFO"
        mock_parse_args.return_value = mock_args
        
        # Mock job file content
        mock_open = mock.mock_open(read_data="Job description text")
        
        # Mock optimize_resume return value
        mock_optimize_resume.return_value = {"status": "success", "test": True}
        
        # Run main
        from src.resume_ats.core import main
        with mock.patch("builtins.open", mock_open):
            result = main()
        
        # Check if function returned successfully
        self.assertEqual(result, 0)
        
        # Check if optimize_resume was called with correct arguments
        mock_optimize_resume.assert_called_once_with("resume.pdf", "Job description text", None)
        
        # Check if output file was written
        mock_open.assert_called_with("output.json", "w")