# tests/conftest.py
"""
Pytest configuration and fixtures
"""

import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing"""
    return """
    John Doe
    Software Engineer
    john.doe@example.com
    +1 (555) 123-4567
    linkedin.com/in/johndoe
    
    SUMMARY
    Experienced software engineer with 5 years in web development.
    
    SKILLS
    - Python programming
    - JavaScript development  
    - SQL databases
    - AWS cloud services
    - Git version control
    - Agile methodology
    
    EXPERIENCE
    Senior Software Engineer | Tech Corp | 2020-2023
    • Developed and maintained web applications using Python and JavaScript
    • Led a team of 5 developers in agile environment
    • Implemented CI/CD pipelines reducing deployment time by 50%
    • Collaborated with cross-functional teams to deliver projects on time
    
    Software Developer | StartupXYZ | 2018-2020
    • Built RESTful APIs using Django framework
    • Optimized database queries improving performance by 30%
    • Participated in code reviews and mentored junior developers
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology | 2014-2018
    GPA: 3.8/4.0
    
    CERTIFICATIONS
    - AWS Certified Solutions Architect
    - Certified Scrum Master
    """

@pytest.fixture
def sample_job_description():
    """Sample job description for testing"""
    return """
    Senior Python Developer
    
    We are seeking a skilled Senior Python Developer to join our growing team.
    
    REQUIRED SKILLS:
    - 5+ years Python development experience
    - Experience with Django or Flask frameworks
    - SQL database management
    - RESTful API development
    - Git version control
    - Agile/Scrum methodology
    
    PREFERRED SKILLS:
    - AWS cloud services
    - Docker containerization
    - React.js frontend development
    - Test-driven development
    - CI/CD pipeline experience
    
    REQUIREMENTS:
    - Bachelor's degree in Computer Science or related field
    - 5+ years of software development experience
    - Strong problem-solving and communication skills
    - Experience leading development teams
    
    RESPONSIBILITIES:
    - Design and develop scalable web applications
    - Lead technical discussions and code reviews
    - Mentor junior developers
    - Collaborate with product and design teams
    - Ensure code quality and best practices
    """

@pytest.fixture
def temp_resume_file(sample_resume_text):
    """Create temporary resume file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_resume_text)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)
