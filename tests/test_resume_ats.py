"""
Unit tests for resume_ats plugin including enhanced features.
"""

import json
import os
import tempfile
import shutil
from unittest import TestCase, mock
import uuid

import pytest

from src.resume_ats import (
    ResumeATS, 
    analyze_resume, 
    optimize_resume,
    EnhancedResumeATS,
    analyze_and_report,
    optimize_and_report,
    ResumeAnonymizer,
    anonymize_resume_text,
    anonymize_resume_file,
    ResumeVersionTracker,
    ResumeComparer,
    compare_resumes,
    compare_resume_to_jobs
)
from src.resume_ats.utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    normalize_text,
    get_keywords_from_job_description,
    calculate_similarity_score
)

# Mock pypdf for tests
import sys
from unittest.mock import MagicMock
sys.modules['pypdf'] = MagicMock()
sys.modules['reportlab'] = MagicMock()
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()


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
        
        # Create a temporary directory for multi-file tests
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize ResumeATS
        self.ats = ResumeATS()
    
    def tearDown(self):
        """Clean up test environment."""
        os.unlink(self.temp_file.name)
        shutil.rmtree(self.temp_dir)
    
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


class TestEnhancedFeatures(TestCase):
    """Test enhanced features."""
    
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
        """
        
        # Create mock resume file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        self.temp_file.write(self.sample_resume_text.encode('utf-8'))
        self.temp_file.close()
        
        # Create a second mock resume file
        self.temp_file2 = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        self.temp_file2.write("""
        JANE SMITH
        Data Scientist
        jane.smith@example.com | (987) 654-3210

        SUMMARY
        Data scientist with expertise in machine learning and statistics.

        EXPERIENCE
        Senior Data Scientist, DataCorp Inc.
        • Built predictive models using Python and TensorFlow
        • Analyzed large datasets to extract insights

        SKILLS
        Python, TensorFlow, Pandas, NumPy, SQL, R, Machine Learning

        EDUCATION
        Master of Science in Data Science
        University of Analytics, 2019
        """.encode('utf-8'))
        self.temp_file2.close()
        
        # Create a temporary directory for version tracking
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize EnhancedResumeATS
        self.enhanced_ats = EnhancedResumeATS({
            'version_storage_dir': self.temp_dir
        })
    
    def tearDown(self):
        """Clean up test environment."""
        os.unlink(self.temp_file.name)
        os.unlink(self.temp_file2.name)
        shutil.rmtree(self.temp_dir)
    
    @mock.patch('src.resume_ats.pdf_reporter.generate_pdf_report')
    @mock.patch('src.resume_ats.core.ResumeATS.analyze')
    def test_analyze_and_report(self, mock_analyze, mock_generate_pdf):
        """Test analyze_and_report functionality."""
        # Mock analyze return value
        mock_analyze.return_value = {
            "status": "success",
            "stats": {"overall_ats_score": 85},
            "sections_detected": ["summary", "experience", "skills"]
        }
        
        # Mock PDF generation
        mock_generate_pdf.return_value = "report.pdf"
        
        # Test analyze_and_report
        analysis, pdf_path = self.enhanced_ats.analyze_and_report(
            self.temp_file.name, 
            self.sample_job_description
        )
        
        # Check results
        self.assertEqual(analysis["status"], "success")
        self.assertEqual(pdf_path, "report.pdf")
        
        # Check if analyze was called with correct arguments
        mock_analyze.assert_called_once_with(self.temp_file.name, self.sample_job_description)
        
        # Check if generate_pdf_report was called
        mock_generate_pdf.assert_called_once()
    
    @mock.patch('src.resume_ats.enhanced.ResumeAnonymizer.anonymize_file')
    def test_anonymize_resume(self, mock_anonymize_file):
        """Test resume anonymization."""
        # Mock anonymize_file return value
        mock_anonymize_file.return_value = ("anonymized.pdf", {"names": ["John Doe"]})
        
        # Test anonymize_resume
        output_path, replaced_items = self.enhanced_ats.anonymize_resume(self.temp_file.name)
        
        # Check results
        self.assertEqual(output_path, "anonymized.pdf")
        self.assertEqual(replaced_items["names"], ["John Doe"])
        
        # Check if anonymize_file was called with correct arguments
        mock_anonymize_file.assert_called_once_with(self.temp_file.name, None)
    
    @mock.patch('src.resume_ats.resume_anonymizer.ResumeAnonymizer._extract_text')
    def test_anonymize_text(self, mock_extract_text):
        """Test text anonymization."""
        # Create anonymizer
        anonymizer = ResumeAnonymizer()
        
        # Test text with PII
        text = "John Doe works at ABC Corp. Contact: john.doe@example.com or 123-456-7890."
        mock_extract_text.return_value = text
        
        # Test anonymize_text
        anonymized, replaced = anonymizer.anonymize_text(text)
        
        # Check if PII is replaced
        self.assertNotIn("John Doe", anonymized)
        self.assertNotIn("john.doe@example.com", anonymized)
        self.assertNotIn("123-456-7890", anonymized)
    
    @mock.patch('src.resume_ats.core.ResumeATS.analyze')
    def test_version_tracking(self, mock_analyze):
        """Test resume version tracking."""
        # Mock analyze return value
        mock_analyze.return_value = {
            "status": "success",
            "stats": {
                "overall_ats_score": 75,
                "keyword_match_score": 0.6,
                "format_score": 0.8,
                "word_count": 300
            },
            "sections_detected": ["summary", "experience", "skills"]
        }
        
        # Test tracking a version
        version_id = self.enhanced_ats.track_version(
            self.temp_file.name, 
            mock_analyze.return_value,
            "Initial Version"
        )
        
        # Check if version was saved
        versions = self.enhanced_ats.get_version_history()
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]["version_name"], "Initial Version")
        
        # Update the mock to simulate an improved resume
        mock_analyze.return_value = {
            "status": "success",
            "stats": {
                "overall_ats_score": 85,  # Improved score
                "keyword_match_score": 0.7,
                "format_score": 0.8,
                "word_count": 320
            },
            "sections_detected": ["summary", "experience", "skills", "education"]  # Added section
        }
        
        # Track another version
        version_id2 = self.enhanced_ats.track_version(
            self.temp_file.name, 
            mock_analyze.return_value,
            "Improved Version"
        )
        
        # Compare versions
        comparison = self.enhanced_ats.compare_versions(version_id, version_id2)
        
        # Check comparison results
        self.assertEqual(comparison["scores"]["overall_ats_score"]["difference"], 10)
        self.assertEqual(len(comparison["sections"]["added"]), 1)
    
    @mock.patch('src.resume_ats.core.ResumeATS.analyze')
    def test_compare_multiple_resumes(self, mock_analyze):
        """Test comparing multiple resumes."""
        # Mock analyze return values for different resumes
        def mock_analyze_side_effect(resume_path, job_desc=None):
            if resume_path == self.temp_file.name:
                return {
                    "status": "success",
                    "stats": {
                        "overall_ats_score": 75,
                        "keyword_match_score": 0.6,
                        "format_score": 0.8,
                        "word_count": 300,
                        "keyword_matches": ["python", "flask", "react"],
                        "missing_keywords": ["django"]
                    },
                    "sections_detected": ["summary", "experience", "skills"]
                }
            else:
                return {
                    "status": "success",
                    "stats": {
                        "overall_ats_score": 80,
                        "keyword_match_score": 0.7,
                        "format_score": 0.75,
                        "word_count": 350,
                        "keyword_matches": ["python", "tensorflow", "pandas"],
                        "missing_keywords": ["django", "flask"]
                    },
                    "sections_detected": ["summary", "experience", "skills", "education"]
                }
        
        mock_analyze.side_effect = mock_analyze_side_effect
        
        # Test comparing multiple resumes
        comparison = self.enhanced_ats.compare_multiple_resumes(
            [self.temp_file.name, self.temp_file2.name], 
            self.sample_job_description
        )
        
        # Check comparison results
        self.assertEqual(len(comparison["metrics"]), 2)
        self.assertEqual(comparison["rankings"]["overall_ats_score"][0], os.path.basename(self.temp_file2.name))
        self.assertIn("keyword_analysis", comparison)
        self.assertIn("section_analysis", comparison)
    
    @mock.patch('src.resume_ats.core.ResumeATS.analyze')
    def test_compare_resume_to_multiple_jobs(self, mock_analyze):
        """Test comparing one resume to multiple jobs."""
        # Mock analyze return values for different job descriptions
        def mock_analyze_side_effect(resume_path, job_desc=None):
            if "Python" in job_desc:
                return {
                    "status": "success",
                    "stats": {
                        "overall_ats_score": 85,
                        "keyword_match_score": 0.8,
                        "format_score": 0.8,
                        "word_count": 300,
                        "keyword_matches": ["python", "flask", "react"],
                        "missing_keywords": ["django"]
                    },
                    "sections_detected": ["summary", "experience", "skills"]
                }
            else:
                return {
                    "status": "success",
                    "stats": {
                        "overall_ats_score": 65,
                        "keyword_match_score": 0.5,
                        "format_score": 0.8,
                        "word_count": 300,
                        "keyword_matches": ["react"],
                        "missing_keywords": ["nodejs", "express", "mongodb"]
                    },
                    "sections_detected": ["summary", "experience", "skills"]
                }
        
        mock_analyze.side_effect = mock_analyze_side_effect
        
        # Test comparing resume to multiple jobs
        job_descriptions = {
            "Python Developer": "Python developer with Flask experience",
            "Node.js Developer": "Node.js developer with Express and MongoDB"
        }
        
        comparison = self.enhanced_ats.compare_resume_to_multiple_jobs(
            self.temp_file.name, 
            job_descriptions
        )
        
        # Check comparison results
        self.assertEqual(len(comparison["metrics"]), 2)
        self.assertEqual(comparison["rankings"]["overall_ats_score"][0], "Python Developer")
        self.assertIn("keyword_analysis", comparison)
    
    @mock.patch('src.resume_ats.enhanced.analyze_resume')
    @mock.patch('src.resume_ats.pdf_reporter.generate_pdf_report')
    def test_analyze_and_report_function(self, mock_generate_pdf, mock_analyze):
        """Test analyze_and_report convenience function."""
        # Mock function return values
        mock_analyze.return_value = {"status": "success", "test": True}
        mock_generate_pdf.return_value = "report.pdf"
        
        # Test function
        result, pdf_path = analyze_and_report("fakepath.pdf", "job description")
        
        # Check results
        self.assertEqual(result, {"status": "success", "test": True})
        self.assertEqual(pdf_path, "report.pdf")
        
        # Check if analyze_resume was called with correct arguments
        mock_analyze.assert_called_once_with("fakepath.pdf", "job description")
    
    @mock.patch('src.resume_ats.enhanced.optimize_resume')
    @mock.patch('src.resume_ats.pdf_reporter.generate_pdf_report')
    def test_optimize_and_report_function(self, mock_generate_pdf, mock_optimize):
        """Test optimize_and_report convenience function."""
        # Mock function return values
        mock_optimize.return_value = {"status": "success", "test": True}
        mock_generate_pdf.return_value = "report.pdf"
        
        # Test function
        result, pdf_path = optimize_and_report("fakepath.pdf", "job description")
        
        # Check results
        self.assertEqual(result, {"status": "success", "test": True})
        self.assertEqual(pdf_path, "report.pdf")
        
        # Check if optimize_resume was called with correct arguments
        mock_optimize.assert_called_once_with("fakepath.pdf", "job description")
