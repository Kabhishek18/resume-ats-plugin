# tests/test_scoring.py
"""
Test cases for scoring engine module
"""

import pytest
from ats_resume_scorer.main import (
    ATSScoringEngine,
    ScoringWeights,
    ResumeData,
    JobDescription,
    ContactInfo,
    Experience,
    Education,
)


class TestATSScoringEngine:

    def setup_method(self):
        """Setup test fixtures"""
        self.scorer = ATSScoringEngine()

        # Sample resume data
        self.sample_resume = ResumeData(
            contact_info=ContactInfo(
                emails=["test@example.com"], phones=["+1234567890"]
            ),
            summary="Experienced software engineer",
            skills=["python", "javascript", "sql", "aws"],
            education=[
                Education(
                    degree="Bachelor of Science in Computer Science",
                    institution="Test University",
                )
            ],
            experience=[
                Experience(
                    title="Software Engineer",
                    company="Tech Corp",
                    duration="2020-2023",
                    description=[
                        "Developed web applications",
                        "Led team of 5 developers",
                    ],
                )
            ],
            certifications=[],
            raw_text="Sample resume text with various action verbs like developed and led.",
        )

        # Sample job description
        self.sample_jd = JobDescription(
            title="Senior Software Engineer",
            required_skills=["python", "sql", "aws"],
            preferred_skills=["javascript", "docker"],
            education_requirements=["bachelor"],
            experience_requirements="3+ years",
            responsibilities=["Develop software", "Lead projects"],
            raw_text="Job description text",
        )

    def test_keyword_match_scoring(self):
        """Test keyword matching score calculation"""
        score = self.scorer.calculate_keyword_match_score(
            self.sample_resume, self.sample_jd
        )

        # Should have high score since resume has all required skills
        assert score >= 70  # At least 70% match
        assert score <= 100

    def test_title_match_scoring(self):
        """Test title matching score calculation"""
        score = self.scorer.calculate_title_match_score(
            self.sample_resume, self.sample_jd
        )

        # Should have some match between "Software Engineer" and "Senior Software Engineer"
        assert score >= 30
        assert score <= 100

    def test_format_compliance_scoring(self):
        """Test format compliance scoring"""
        score = self.scorer.calculate_format_compliance_score(self.sample_resume)

        # Should have good score since resume has all required sections
        assert score >= 80
        assert score <= 100

    def test_action_verbs_scoring(self):
        """Test action verbs scoring"""
        score = self.scorer.calculate_action_verbs_grammar_score(self.sample_resume)

        # Resume contains "developed" and "led" which are action verbs
        assert score >= 25  # Should get some points
        assert score <= 100

    def test_overall_scoring(self):
        """Test overall score calculation"""
        result = self.scorer.calculate_overall_score(self.sample_resume, self.sample_jd)

        assert "total_score" in result
        assert "detailed_scores" in result
        assert "weights_used" in result

        assert 0 <= result["total_score"] <= 100

        # Check all score categories are present
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
            assert category in result["detailed_scores"]

    def test_custom_weights(self):
        """Test custom scoring weights"""
        custom_weights = ScoringWeights(
            keyword_match=0.50,  # Higher weight for keywords
            title_match=0.05,
            education_match=0.05,
            experience_match=0.10,
            format_compliance=0.10,
            action_verbs_grammar=0.10,
            readability=0.10,
        )

        custom_scorer = ATSScoringEngine(weights=custom_weights)
        result = custom_scorer.calculate_overall_score(
            self.sample_resume, self.sample_jd
        )

        assert result["weights_used"]["keyword_match"] == 0.50
