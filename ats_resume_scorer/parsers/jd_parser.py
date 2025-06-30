# ats_resume_scorer/parsers/jd_parser.py
"""
Job Description Parser Module - Extracts structured requirements from job descriptions
"""

import re
import spacy
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class JobDescription:
    """Job description data structure"""

    title: str
    required_skills: List[str]
    preferred_skills: List[str]
    education_requirements: List[str]
    experience_requirements: str
    responsibilities: List[str]
    raw_text: str
    company: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None


class JobDescriptionParser:
    """Parser for job descriptions"""

    def __init__(self):
        """Initialize parser with NLP model"""
        self.nlp = self._load_spacy_model()

        # Common skill keywords
        self.skill_indicators = [
            "experience with",
            "knowledge of",
            "proficiency in",
            "familiarity with",
            "expertise in",
            "skilled in",
            "background in",
            "understanding of",
        ]

        # Education keywords
        self.education_keywords = [
            "bachelor",
            "master",
            "phd",
            "doctorate",
            "degree",
            "diploma",
            "certification",
            "associate",
            "bs",
            "ba",
            "ms",
            "ma",
            "mba",
        ]

        # Experience keywords
        self.experience_keywords = [
            "years",
            "experience",
            "background",
            "track record",
            "history",
        ]

    def _load_spacy_model(self):
        """Load spaCy NLP model"""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Some features may be limited.")
            return None

    def parse_job_description(self, jd_text: str) -> JobDescription:
        """Main method to parse job description"""

        # Extract basic information
        title = self.extract_job_title(jd_text)
        company = self.extract_company_name(jd_text)
        location = self.extract_location(jd_text)
        salary_range = self.extract_salary_range(jd_text)

        # Extract requirements
        required_skills = self.extract_required_skills(jd_text)
        preferred_skills = self.extract_preferred_skills(jd_text)
        education_requirements = self.extract_education_requirements(jd_text)
        experience_requirements = self.extract_experience_requirements(jd_text)
        responsibilities = self.extract_responsibilities(jd_text)

        return JobDescription(
            title=title,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            education_requirements=education_requirements,
            experience_requirements=experience_requirements,
            responsibilities=responsibilities,
            raw_text=jd_text,
            company=company,
            location=location,
            salary_range=salary_range,
        )

    def extract_job_title(self, text: str) -> str:
        """Extract job title from job description"""
        # Look for common title patterns
        title_patterns = [
            r"^([^\n]+)(?:\n|$)",  # First line
            r"(?i)(?:position|role|title):\s*([^\n]+)",
            r"(?i)job\s+title:\s*([^\n]+)",
            r"(?i)we\s+are\s+looking\s+for\s+a\s+([^\n,.]+)",
            r"(?i)seeking\s+(?:a|an)\s+([^\n,.]+)",
        ]

        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                title = match.group(1).strip()
                # Clean up title
                title = re.sub(r"[^\w\s-]", "", title)
                if len(title) > 5 and len(title) < 100:
                    return title

        return "Software Engineer"  # Default fallback

    def extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name"""
        company_patterns = [
            r"(?i)company:\s*([^\n]+)",
            r"(?i)at\s+([A-Z][a-zA-Z\s&]+)(?:\s+we|\s+is|\s+has)",
            r"(?i)([A-Z][a-zA-Z\s&]+)\s+is\s+(?:seeking|looking)",
        ]

        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                company = match.group(1).strip()
                if len(company) > 2 and len(company) < 50:
                    return company

        return None

    def extract_location(self, text: str) -> Optional[str]:
        """Extract job location"""
        location_patterns = [
            r"(?i)location:\s*([^\n]+)",
            r"(?i)based\s+in\s+([^\n,.]+)",
            r"(?i)([A-Z][a-z]+,\s*[A-Z]{2})",  # City, State
            r"(?i)(remote|hybrid|on-site)",
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def extract_salary_range(self, text: str) -> Optional[str]:
        """Extract salary information"""
        salary_patterns = [
            r"(?i)\$[\d,]+\s*-\s*\$[\d,]+",
            r"(?i)\$[\d,]+k?\s*(?:per\s+year|annually|yearly)?",
            r"(?i)salary:\s*([^\n]+)",
            r"(?i)compensation:\s*([^\n]+)",
        ]

        for pattern in salary_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group().strip()

        return None

    def extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills and qualifications"""
        required_skills = []

        # Look for required skills section
        required_patterns = [
            r"(?i)(?:required|must\s+have|essential).*?(?=(?:preferred|nice|bonus)|(?:\n\s*\n)|$)",
            r"(?i)requirements.*?(?=(?:preferred|responsibilities)|(?:\n\s*\n)|$)",
            r"(?i)qualifications.*?(?=(?:preferred|responsibilities)|(?:\n\s*\n)|$)",
        ]

        for pattern in required_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                section_text = match.group()
                skills = self._extract_skills_from_section(section_text)
                required_skills.extend(skills)

        # Also look for "X+ years" requirements
        experience_skills = re.findall(
            r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:experience\s+(?:with|in)\s+)?([^\n,.]+)",
            text,
            re.IGNORECASE,
        )
        for years, skill in experience_skills:
            skill = skill.strip().lower()
            if skill and len(skill) > 2:
                required_skills.append(skill)

        return list(set([skill.lower() for skill in required_skills if skill]))

    def extract_preferred_skills(self, text: str) -> List[str]:
        """Extract preferred/nice-to-have skills"""
        preferred_skills = []

        # Look for preferred skills section
        preferred_patterns = [
            r"(?i)(?:preferred|nice\s+to\s+have|bonus|plus|additional).*?(?=(?:\n\s*\n)|$)",
            r"(?i)(?:would\s+be\s+)?(?:great|nice|good)\s+(?:if|to\s+have).*?(?=(?:\n\s*\n)|$)",
        ]

        for pattern in preferred_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                section_text = match.group()
                skills = self._extract_skills_from_section(section_text)
                preferred_skills.extend(skills)

        return list(set([skill.lower() for skill in preferred_skills if skill]))

    def _extract_skills_from_section(self, section_text: str) -> List[str]:
        """Extract individual skills from a text section"""
        skills = []

        # Extract bullet points
        bullet_pattern = r"[-•*]\s*([^\n]+)"
        bullets = re.findall(bullet_pattern, section_text)
        for bullet in bullets:
            # Clean and split skills
            bullet = re.sub(
                r"(?i)(?:experience\s+(?:with|in)|knowledge\s+of|proficiency\s+in)",
                "",
                bullet,
            )
            bullet = bullet.strip()
            if bullet:
                # Split on common delimiters
                sub_skills = re.split(r"[,;&/]", bullet)
                for skill in sub_skills:
                    skill = skill.strip()
                    if len(skill) > 2 and len(skill) < 50:
                        skills.append(skill)

        # Extract from natural language
        for indicator in self.skill_indicators:
            pattern = rf"{indicator}\s+([^,.;\n]+)"
            matches = re.findall(pattern, section_text, re.IGNORECASE)
            for match in matches:
                skill = match.strip()
                if len(skill) > 2 and len(skill) < 50:
                    skills.append(skill)

        return skills

    def extract_education_requirements(self, text: str) -> List[str]:
        """Extract education requirements"""
        education_requirements = []

        # Look for education mentions
        edu_patterns = [
            r"(?i)(bachelor\'?s?\s+degree)",
            r"(?i)(master\'?s?\s+degree)",
            r"(?i)(phd|doctorate)",
            r"(?i)(associate\'?s?\s+degree)",
            r"(?i)(b\.?[as]\.?)",
            r"(?i)(m\.?[as]\.?)",
            r"(?i)degree\s+in\s+([^\n,.]+)",
            r"(?i)(certification\s+in\s+[^\n,.]+)",
        ]

        for pattern in edu_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                education_requirements.append(match.strip())

        return list(set(education_requirements))

    def extract_experience_requirements(self, text: str) -> str:
        """Extract experience requirements"""
        exp_patterns = [
            r"(\d+)\+?\s*years?\s+(?:of\s+)?experience",
            r"minimum\s+of\s+(\d+)\s+years?",
            r"at\s+least\s+(\d+)\s+years?",
            r"(\d+)-(\d+)\s+years?\s+(?:of\s+)?experience",
        ]

        for pattern in exp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group().strip()

        return "Experience level not specified"

    def extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities"""
        responsibilities = []

        # Look for responsibilities section
        resp_patterns = [
            r"(?i)(?:responsibilities|duties|role).*?(?=(?:requirements|qualifications)|(?:\n\s*\n)|$)",
            r"(?i)(?:you\s+will|what\s+you\'ll\s+do).*?(?=(?:requirements|qualifications)|(?:\n\s*\n)|$)",
        ]

        for pattern in resp_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                section_text = match.group()

                # Extract bullet points
                bullets = re.findall(r"[-•*]\s*([^\n]+)", section_text)
                responsibilities.extend(
                    [bullet.strip() for bullet in bullets if bullet.strip()]
                )

        return responsibilities
