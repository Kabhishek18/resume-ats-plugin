# tests/test_parser.py
"""
Test cases for resume parser module
"""

import pytest
import tempfile
import os
from ats_resume_scorer.main import ResumeParser, ContactInfo

class TestResumeParser:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = ResumeParser()
        
    def test_contact_info_extraction(self):
        """Test contact information extraction"""
        sample_text = """
        John Doe
        john.doe@example.com
        +1 (555) 123-4567
        linkedin.com/in/johndoe
        github.com/johndoe
        """
        
        contact_info = self.parser.extract_contact_info(sample_text)
        
        assert len(contact_info.emails) == 1
        assert contact_info.emails[0] == "john.doe@example.com"
        assert len(contact_info.phones) >= 1
        assert contact_info.linkedin is not None
        assert contact_info.github is not None
    
    def test_skills_extraction(self):
        """Test skills extraction"""
        sample_text = """
        Technical Skills:
        - Python programming
        - JavaScript development
        - SQL databases
        - AWS cloud services
        - Docker containerization
        """
        
        skills = self.parser.extract_skills(sample_text)
        
        expected_skills = ['python', 'javascript', 'sql', 'aws', 'docker']
        for skill in expected_skills:
            assert skill in skills
    
    def test_education_extraction(self):
        """Test education extraction"""
        sample_text = """
        Education:
        Bachelor of Science in Computer Science
        Master's Degree in Software Engineering
        """
        
        education = self.parser.extract_education(sample_text)
        
        assert len(education) >= 1
        assert any('bachelor' in edu.degree.lower() for edu in education)
    
    def test_txt_file_parsing(self):
        """Test TXT file parsing"""
        sample_content = "John Doe\nSoftware Engineer\njohn@example.com"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_content)
            temp_file = f.name
        
        try:
            content = self.parser.parse_txt(temp_file)
            assert "John Doe" in content
            assert "john@example.com" in content
        finally:
            os.unlink(temp_file)
    
    def test_empty_text_handling(self):
        """Test handling of empty text"""
        contact_info = self.parser.extract_contact_info("")
        assert len(contact_info.emails) == 0
        assert len(contact_info.phones) == 0
        
        skills = self.parser.extract_skills("")
        assert len(skills) == 0

# config/default_weights.json
{
    "keyword_match": 0.30,
    "title_match": 0.10,
    "education_match": 0.10,
    "experience_match": 0.15,
    "format_compliance": 0.15,
    "action_verbs_grammar": 0.10,
    "readability": 0.10
}
