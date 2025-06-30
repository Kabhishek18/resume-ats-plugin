# ats_resume_scorer/parsers/resume_parser.py
"""
Resume Parser Module - Extracts structured data from resume files
"""

import re
import json
import spacy
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import logging

# File parsing imports
try:
    import fitz  # PyMuPDF
except ImportError:
    import PyPDF2

    fitz = None

try:
    from docx import Document
except ImportError:
    Document = None

logger = logging.getLogger(__name__)


@dataclass
class ContactInfo:
    """Contact information data structure"""

    emails: List[str]
    phones: List[str]
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None


@dataclass
class Experience:
    """Work experience data structure"""

    title: str
    company: str
    duration: str
    description: List[str]
    location: Optional[str] = None


@dataclass
class Education:
    """Education data structure"""

    degree: str
    institution: str
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None
    location: Optional[str] = None


@dataclass
class ResumeData:
    """Complete resume data structure"""

    contact_info: ContactInfo
    summary: Optional[str]
    skills: List[str]
    education: List[Education]
    experience: List[Experience]
    certifications: List[str]
    raw_text: str


class ResumeParser:
    """Main resume parser class"""

    def __init__(self, skills_db_path: Optional[str] = None):
        """Initialize parser with NLP model and skills database"""
        self.nlp = self._load_spacy_model()
        self.skills_db = self._load_skills_database(skills_db_path)

    def _load_spacy_model(self):
        """Load spaCy NLP model"""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            logger.warning(
                "spaCy model not found. Install with: python -m spacy download en_core_web_sm"
            )
            return None

    def _load_skills_database(self, skills_db_path: Optional[str]) -> Dict:
        """Load skills database from JSON file"""
        if skills_db_path:
            try:
                with open(skills_db_path, "r") as f:
                    return json.load(f)
            except FileNotFoundError:
                logger.warning(f"Skills database not found at {skills_db_path}")

        # Default skills database
        return {
            "programming_languages": [
                "python",
                "java",
                "javascript",
                "typescript",
                "c++",
                "c#",
                "go",
                "rust",
                "ruby",
                "php",
                "swift",
                "kotlin",
                "scala",
                "r",
                "matlab",
                "sql",
            ],
            "web_technologies": [
                "html",
                "css",
                "react",
                "angular",
                "vue",
                "node.js",
                "express",
                "django",
                "flask",
                "spring boot",
                "laravel",
                "rails",
            ],
            "databases": [
                "mysql",
                "postgresql",
                "mongodb",
                "redis",
                "elasticsearch",
                "oracle",
                "sql server",
                "sqlite",
                "dynamodb",
            ],
            "cloud_platforms": ["aws", "azure", "gcp", "heroku", "digitalocean"],
            "devops_tools": [
                "docker",
                "kubernetes",
                "jenkins",
                "gitlab ci",
                "github actions",
                "terraform",
                "ansible",
            ],
            "data_science": [
                "pandas",
                "numpy",
                "scikit-learn",
                "tensorflow",
                "pytorch",
                "matplotlib",
                "jupyter",
            ],
        }

    def parse_resume(self, file_path: str) -> ResumeData:
        """Main method to parse resume from file"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        # Extract text based on file type
        if file_path.suffix.lower() == ".pdf":
            raw_text = self.parse_pdf(str(file_path))
        elif file_path.suffix.lower() == ".docx":
            raw_text = self.parse_docx(str(file_path))
        elif file_path.suffix.lower() == ".txt":
            raw_text = self.parse_txt(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        # Extract structured data
        contact_info = self.extract_contact_info(raw_text)
        summary = self.extract_summary(raw_text)
        skills = self.extract_skills(raw_text)
        education = self.extract_education(raw_text)
        experience = self.extract_experience(raw_text)
        certifications = self.extract_certifications(raw_text)

        return ResumeData(
            contact_info=contact_info,
            summary=summary,
            skills=skills,
            education=education,
            experience=experience,
            certifications=certifications,
            raw_text=raw_text,
        )

    def parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""

        if fitz:  # PyMuPDF
            try:
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text()
                doc.close()
            except Exception as e:
                logger.error(f"Error parsing PDF with PyMuPDF: {e}")
                raise
        else:  # PyPDF2 fallback
            try:
                import PyPDF2

                with open(file_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text()
            except Exception as e:
                logger.error(f"Error parsing PDF with PyPDF2: {e}")
                raise

        return text

    def parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        if not Document:
            raise ImportError(
                "python-docx not installed. Install with: pip install python-docx"
            )

        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"Error parsing DOCX: {e}")
            raise

    def parse_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
                try:
                    with open(file_path, "r", encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Could not decode text file: {file_path}")

    def extract_contact_info(self, text: str) -> ContactInfo:
        """Extract contact information from text"""
        # Email patterns
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, text)

        # Phone patterns
        phone_patterns = [
            r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            r"\+\d{1,3}\s?\d{1,14}",
            r"\(\d{3}\)\s?\d{3}-\d{4}",
        ]
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))

        # Social media profiles
        linkedin_pattern = r"linkedin\.com/in/[\w-]+"
        github_pattern = r"github\.com/[\w-]+"
        website_pattern = r"https?://[\w.-]+\.[a-zA-Z]{2,}"

        linkedin = re.search(linkedin_pattern, text)
        github = re.search(github_pattern, text)
        websites = re.findall(website_pattern, text)

        return ContactInfo(
            emails=list(set(emails)),
            phones=list(set([phone.strip() for phone in phones if phone.strip()])),
            linkedin=linkedin.group() if linkedin else None,
            github=github.group() if github else None,
            website=websites[0] if websites else None,
        )

    def extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary/objective"""
        summary_patterns = [
            r"(?i)(?:summary|objective|profile|about)\s*[:;]?\s*(.*?)(?=\n\s*\n|\n\s*[A-Z])",
            r"(?i)(professional\s+summary.*?)(?=\n\s*\n|\n\s*[A-Z])",
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 50:  # Ensure it's substantial
                    return summary

        return None

    def extract_skills(self, text: str) -> List[str]:
        """Extract technical and professional skills"""
        text_lower = text.lower()
        found_skills = set()

        # Extract from skills database
        for category, skills in self.skills_db.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills.add(skill.lower())

        # Extract from skills section specifically
        skills_section_pattern = r"(?i)(?:skills|technologies|technical\s+skills).*?(?=\n\s*\n|\n\s*[A-Z][A-Z\s]+:)"
        skills_match = re.search(skills_section_pattern, text, re.DOTALL)

        if skills_match:
            skills_text = skills_match.group()
            # Extract bullet points and comma-separated items
            bullet_skills = re.findall(r"[-•*]\s*([^\n]+)", skills_text)
            comma_skills = re.findall(r"([^,\n]+)(?:,|$)", skills_text)

            for skill_list in [bullet_skills, comma_skills]:
                for skill in skill_list:
                    skill = skill.strip().lower()
                    if len(skill) > 2 and len(skill) < 30:
                        found_skills.add(skill)

        return list(found_skills)

    def extract_education(self, text: str) -> List[Education]:
        """Extract education information"""
        education_list = []

        # Education section pattern
        edu_pattern = r"(?i)(?:education|academic.*?)(?=\n\s*\n|\n\s*[A-Z][A-Z\s]+:|$)"
        edu_match = re.search(edu_pattern, text, re.DOTALL)

        if edu_match:
            edu_text = edu_match.group()

            # Degree patterns
            degree_patterns = [
                r"((?:Bachelor|Master|PhD|Doctorate|Associate).*?)(?:\n|$)",
                r"(B\.?[AS]\.?.*?)(?:\n|$)",
                r"(M\.?[AS]\.?.*?)(?:\n|$)",
            ]

            for pattern in degree_patterns:
                matches = re.findall(pattern, edu_text, re.IGNORECASE)
                for match in matches:
                    # Extract institution
                    lines = match.split("\n")
                    degree = lines[0].strip()
                    institution = (
                        lines[1].strip() if len(lines) > 1 else "Unknown Institution"
                    )

                    # Extract graduation year
                    year_match = re.search(r"(\d{4})", match)
                    graduation_year = year_match.group(1) if year_match else None

                    education_list.append(
                        Education(
                            degree=degree,
                            institution=institution,
                            graduation_year=graduation_year,
                        )
                    )

        return education_list

    def extract_experience(self, text: str) -> List[Experience]:
        """Extract work experience"""
        experience_list = []

        # Experience section pattern
        exp_pattern = r"(?i)(?:experience|employment|work\s+history).*?(?=\n\s*\n[A-Z][A-Z\s]+:|$)"
        exp_match = re.search(exp_pattern, text, re.DOTALL)

        if exp_match:
            exp_text = exp_match.group()

            # Split into individual jobs (look for job titles)
            job_pattern = r"([^\n]+)\s*\|\s*([^\n]+)\s*\|\s*([^\n]+)(?:\n(.*?))?(?=\n[A-Z]|\n\s*\n|$)"
            jobs = re.findall(job_pattern, exp_text, re.DOTALL)

            for job in jobs:
                title = job[0].strip()
                company = job[1].strip()
                duration = job[2].strip()
                description_text = job[3].strip() if len(job) > 3 else ""

                # Extract bullet points from description
                description = []
                if description_text:
                    bullets = re.findall(r"[-•*]\s*([^\n]+)", description_text)
                    description = [
                        bullet.strip() for bullet in bullets if bullet.strip()
                    ]

                experience_list.append(
                    Experience(
                        title=title,
                        company=company,
                        duration=duration,
                        description=description,
                    )
                )

        return experience_list

    def extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        cert_patterns = [
            r"(?i)(?:certification|certificate)s?.*?(?=\n\s*\n|\n\s*[A-Z][A-Z\s]+:|$)",
            r"(?i)certified.*?(?=\n|$)",
        ]

        certifications = []
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                # Extract individual certifications
                certs = re.findall(r"[-•*]\s*([^\n]+)", match)
                certifications.extend([cert.strip() for cert in certs if cert.strip()])

        return list(set(certifications))
