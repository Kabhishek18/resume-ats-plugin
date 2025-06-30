# tests/test_main.py
"""
Test cases for main ATS Resume Scorer functionality
"""

import pytest
import tempfile
import os
from pathlib import Path

from ats_resume_scorer.main import ATSResumeScorer
from ats_resume_scorer.scoring.scoring_engine import ScoringWeights


class TestATSResumeScorer:

    def setup_method(self):
        """Setup test fixtures"""
        self.scorer = ATSResumeScorer()

    def test_scorer_initialization(self):
        """Test scorer initializes correctly"""
        assert self.scorer is not None
        assert self.scorer.weights is not None
        assert self.scorer.resume_parser is not None
        assert self.scorer.jd_parser is not None
        assert self.scorer.scoring_engine is not None
        assert self.scorer.report_generator is not None

    def test_custom_weights_initialization(self):
        """Test scorer with custom weights"""
        custom_weights = ScoringWeights(
            keyword_match=0.40,
            title_match=0.05,
            education_match=0.05,
            experience_match=0.20,
            format_compliance=0.10,
            action_verbs_grammar=0.10,
            readability=0.10,
        )

        scorer = ATSResumeScorer(weights=custom_weights)
        assert scorer.weights.keyword_match == 0.40
        assert scorer.weights.title_match == 0.05

    def test_score_resume_with_text_files(
        self, sample_resume_text, sample_job_description
    ):
        """Test scoring with text files"""
        # Create temporary files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as resume_file:
            resume_file.write(sample_resume_text)
            resume_path = resume_file.name

        try:
            result = self.scorer.score_resume(resume_path, sample_job_description)

            # Check result structure
            assert "overall_score" in result
            assert "grade" in result
            assert "detailed_breakdown" in result
            assert "recommendations" in result
            assert "job_match_analysis" in result
            assert "resume_summary" in result

            # Check score is within valid range
            assert 0 <= result["overall_score"] <= 100

            # Check grade is valid
            assert result["grade"] in ["A", "B", "C", "D", "F"]

            # Check detailed breakdown has all categories
            breakdown = result["detailed_breakdown"]
            expected_categories = [
                "keyword_match",
                "title_match",
                "education_match",
                "experience_match",
                "format_compliance",
                "action_verbs_grammar",
                "readability",
            ]

            for category in expected_categories:
                assert category in breakdown
                assert 0 <= breakdown[category] <= 100

            # Check recommendations exist
            assert isinstance(result["recommendations"], list)
            assert len(result["recommendations"]) > 0

        finally:
            # Cleanup
            if os.path.exists(resume_path):
                os.unlink(resume_path)

    def test_score_resume_from_files(self, sample_resume_text, sample_job_description):
        """Test scoring from separate files"""
        # Create temporary files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as resume_file:
            resume_file.write(sample_resume_text)
            resume_path = resume_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as jd_file:
            jd_file.write(sample_job_description)
            jd_path = jd_file.name

        try:
            result = self.scorer.score_resume_from_files(resume_path, jd_path)

            assert "overall_score" in result
            assert result["overall_score"] > 0  # Should have some score

        finally:
            # Cleanup
            for path in [resume_path, jd_path]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_generate_text_report(self, sample_resume_text, sample_job_description):
        """Test text report generation"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as resume_file:
            resume_file.write(sample_resume_text)
            resume_path = resume_file.name

        try:
            result = self.scorer.score_resume(resume_path, sample_job_description)
            text_report = self.scorer.generate_text_report(result)

            assert isinstance(text_report, str)
            assert "ATS RESUME SCORE REPORT" in text_report
            assert "Overall Score:" in text_report
            assert "RECOMMENDATIONS:" in text_report

        finally:
            if os.path.exists(resume_path):
                os.unlink(resume_path)

    def test_save_report_json(self, sample_resume_text, sample_job_description):
        """Test saving report to JSON file"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as resume_file:
            resume_file.write(sample_resume_text)
            resume_path = resume_file.name

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as output_file:
            output_path = output_file.name

        try:
            result = self.scorer.score_resume(resume_path, sample_job_description)
            self.scorer.save_report(result, output_path, "json")

            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0

            # Verify it's valid JSON
            import json

            with open(output_path, "r") as f:
                loaded_data = json.load(f)
                assert "overall_score" in loaded_data

        finally:
            for path in [resume_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_save_report_text(self, sample_resume_text, sample_job_description):
        """Test saving report to text file"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as resume_file:
            resume_file.write(sample_resume_text)
            resume_path = resume_file.name

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as output_file:
            output_path = output_file.name

        try:
            result = self.scorer.score_resume(resume_path, sample_job_description)
            self.scorer.save_report(result, output_path, "text")

            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0

            # Verify it contains expected content
            with open(output_path, "r") as f:
                content = f.read()
                assert "ATS RESUME SCORE REPORT" in content

        finally:
            for path in [resume_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_error_handling_invalid_file(self):
        """Test error handling for invalid files"""
        with pytest.raises(FileNotFoundError):
            self.scorer.score_resume("nonexistent_file.pdf", "some job description")

    def test_error_handling_unsupported_format(self):
        """Test error handling for unsupported file formats"""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as temp_file:
            temp_file.write(b"some content")
            temp_path = temp_file.name

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                self.scorer.score_resume(temp_path, "job description")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_high_scoring_resume(self):
        """Test with a high-quality resume that should score well"""
        high_quality_resume = """
        John Smith
        Senior Software Engineer
        john.smith@email.com
        +1 (555) 123-4567
        linkedin.com/in/johnsmith
        github.com/johnsmith
        
        PROFESSIONAL SUMMARY
        Experienced Senior Software Engineer with 7+ years developing scalable web applications.
        
        TECHNICAL SKILLS
        • Python, JavaScript, TypeScript, SQL
        • Django, React, Node.js, PostgreSQL
        • AWS, Docker, Kubernetes, CI/CD
        • Git, Agile, Test-driven development
        
        PROFESSIONAL EXPERIENCE
        
        Senior Software Engineer | TechCorp Inc | 2020-2023
        • Developed and maintained 5 high-traffic web applications serving 100K+ users
        • Led a team of 4 developers implementing microservices architecture
        • Improved application performance by 40% through database optimization
        • Implemented CI/CD pipelines reducing deployment time by 60%
        
        Software Engineer | StartupXYZ | 2018-2020
        • Built RESTful APIs using Django serving 50K+ daily requests
        • Collaborated with cross-functional teams to deliver 3 major product features
        • Mentored 2 junior developers in best practices and code review
        • Achieved 95% test coverage across all modules
        
        EDUCATION
        Bachelor of Science in Computer Science
        University of Technology | 2014-2018
        GPA: 3.8/4.0
        
        CERTIFICATIONS
        • AWS Certified Solutions Architect
        • Certified Scrum Master
        """

        job_description = """
        Senior Software Engineer - Python/Django
        
        We seek an experienced Senior Software Engineer to join our team.
        
        REQUIRED SKILLS:
        • 5+ years Python development
        • Django web framework
        • PostgreSQL/SQL databases
        • RESTful API development
        • AWS cloud services
        • Git version control
        
        PREFERRED SKILLS:
        • React.js frontend
        • Docker containerization
        • CI/CD pipelines
        • Team leadership experience
        
        REQUIREMENTS:
        • Bachelor's degree in Computer Science
        • 5+ years software development
        • Strong communication skills
        • Experience with agile methodologies
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as resume_file:
            resume_file.write(high_quality_resume)
            resume_path = resume_file.name

        try:
            result = self.scorer.score_resume(resume_path, job_description)

            # Should score reasonably well
            assert result["overall_score"] >= 70
            assert result["grade"] in ["A", "B", "C"]

            # Should have good keyword match
            assert result["detailed_breakdown"]["keyword_match"] >= 60

            # Should have good format compliance
            assert result["detailed_breakdown"]["format_compliance"] >= 70

        finally:
            if os.path.exists(resume_path):
                os.unlink(resume_path)
