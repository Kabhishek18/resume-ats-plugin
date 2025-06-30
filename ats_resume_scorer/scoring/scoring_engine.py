# ats_resume_scorer/scoring/scoring_engine.py
"""
ATS Scoring Engine - Core scoring logic for resume evaluation
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from ..parsers.resume_parser import ResumeData
from ..parsers.jd_parser import JobDescription

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """Configurable scoring weights for different categories"""

    keyword_match: float = 0.30
    title_match: float = 0.10
    education_match: float = 0.10
    experience_match: float = 0.15
    format_compliance: float = 0.15
    action_verbs_grammar: float = 0.10
    readability: float = 0.10

    def __post_init__(self):
        """Validate that weights sum to 1.0"""
        total = (
            self.keyword_match
            + self.title_match
            + self.education_match
            + self.experience_match
            + self.format_compliance
            + self.action_verbs_grammar
            + self.readability
        )

        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")


class ATSScoringEngine:
    """Main ATS scoring engine"""

    def __init__(self, weights: Optional[ScoringWeights] = None):
        """Initialize scoring engine with weights"""
        self.weights = weights or ScoringWeights()
        self.action_verbs = self._load_action_verbs()

    def _load_action_verbs(self) -> List[str]:
        """Load action verbs database"""
        # Default action verbs database
        return [
            # Achievement verbs
            "achieved",
            "accomplished",
            "attained",
            "completed",
            "delivered",
            "exceeded",
            "finished",
            "fulfilled",
            "obtained",
            "reached",
            # Leadership verbs
            "led",
            "managed",
            "supervised",
            "directed",
            "coordinated",
            "guided",
            "mentored",
            "coached",
            "facilitated",
            "spearheaded",
            # Creation verbs
            "created",
            "developed",
            "designed",
            "built",
            "established",
            "founded",
            "initiated",
            "launched",
            "pioneered",
            "introduced",
            # Improvement verbs
            "improved",
            "enhanced",
            "optimized",
            "streamlined",
            "upgraded",
            "modernized",
            "revitalized",
            "transformed",
            "revolutionized",
            # Analytical verbs
            "analyzed",
            "evaluated",
            "assessed",
            "researched",
            "investigated",
            "examined",
            "studied",
            "reviewed",
            "monitored",
            "measured",
            # Problem solving verbs
            "solved",
            "resolved",
            "troubleshot",
            "debugged",
            "fixed",
            "addressed",
            "handled",
            "tackled",
            "overcome",
            "mitigated",
        ]

    def calculate_overall_score(
        self, resume_data: ResumeData, job_description: JobDescription
    ) -> Dict[str, Any]:
        """Calculate comprehensive ATS score"""

        # Calculate individual scores
        keyword_score = self.calculate_keyword_match_score(resume_data, job_description)
        title_score = self.calculate_title_match_score(resume_data, job_description)
        education_score = self.calculate_education_match_score(
            resume_data, job_description
        )
        experience_score = self.calculate_experience_match_score(
            resume_data, job_description
        )
        format_score = self.calculate_format_compliance_score(resume_data)
        action_verbs_score = self.calculate_action_verbs_grammar_score(resume_data)
        readability_score = self.calculate_readability_score(resume_data)

        # Calculate weighted total
        total_score = (
            keyword_score * self.weights.keyword_match
            + title_score * self.weights.title_match
            + education_score * self.weights.education_match
            + experience_score * self.weights.experience_match
            + format_score * self.weights.format_compliance
            + action_verbs_score * self.weights.action_verbs_grammar
            + readability_score * self.weights.readability
        )

        return {
            "total_score": round(total_score, 2),
            "detailed_scores": {
                "keyword_match": round(keyword_score, 2),
                "title_match": round(title_score, 2),
                "education_match": round(education_score, 2),
                "experience_match": round(experience_score, 2),
                "format_compliance": round(format_score, 2),
                "action_verbs_grammar": round(action_verbs_score, 2),
                "readability": round(readability_score, 2),
            },
            "weights_used": {
                "keyword_match": self.weights.keyword_match,
                "title_match": self.weights.title_match,
                "education_match": self.weights.education_match,
                "experience_match": self.weights.experience_match,
                "format_compliance": self.weights.format_compliance,
                "action_verbs_grammar": self.weights.action_verbs_grammar,
                "readability": self.weights.readability,
            },
        }

    def calculate_keyword_match_score(
        self, resume_data: ResumeData, job_description: JobDescription
    ) -> float:
        """Calculate keyword/skills matching score"""
        resume_skills = set([skill.lower() for skill in resume_data.skills])
        required_skills = set(
            [skill.lower() for skill in job_description.required_skills]
        )
        preferred_skills = set(
            [skill.lower() for skill in job_description.preferred_skills]
        )

        # Calculate matches
        required_matches = len(resume_skills.intersection(required_skills))
        preferred_matches = len(resume_skills.intersection(preferred_skills))

        # Scoring logic
        if len(required_skills) == 0:
            required_score = 100
        else:
            required_score = (required_matches / len(required_skills)) * 100

        if len(preferred_skills) == 0:
            preferred_score = 0
        else:
            preferred_score = (
                (preferred_matches / len(preferred_skills)) * 100 * 0.3
            )  # 30% weight for preferred

        # Use TF-IDF similarity for overall text matching
        try:
            documents = [resume_data.raw_text.lower(), job_description.raw_text.lower()]
            vectorizer = TfidfVectorizer(
                stop_words="english", ngram_range=(1, 2), max_features=1000
            )
            tfidf_matrix = vectorizer.fit_transform(documents)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            text_similarity_score = similarity * 100
        except:
            text_similarity_score = 0

        # Combine scores (70% skills match, 30% text similarity)
        final_score = (
            (required_score * 0.7)
            + (preferred_score * 0.1)
            + (text_similarity_score * 0.2)
        )
        return min(final_score, 100)

    def calculate_title_match_score(
        self, resume_data: ResumeData, job_description: JobDescription
    ) -> float:
        """Calculate job title matching score"""
        if not resume_data.experience:
            return 0

        # Get most recent job title
        recent_title = resume_data.experience[0].title.lower()
        target_title = job_description.title.lower()

        # Calculate similarity using word overlap
        recent_words = set(recent_title.split())
        target_words = set(target_title.split())

        if len(target_words) == 0:
            return 50  # Default score if no target title

        overlap = len(recent_words.intersection(target_words))
        similarity = (overlap / len(target_words)) * 100

        # Bonus for exact match
        if recent_title == target_title:
            similarity = 100
        elif target_title in recent_title or recent_title in target_title:
            similarity = min(similarity + 20, 100)

        return similarity

    def calculate_education_match_score(
        self, resume_data: ResumeData, job_description: JobDescription
    ) -> float:
        """Calculate education matching score"""
        if not job_description.education_requirements:
            return 100  # No requirements specified

        if not resume_data.education:
            return 0  # No education listed

        score = 0
        total_requirements = len(job_description.education_requirements)

        for requirement in job_description.education_requirements:
            requirement_lower = requirement.lower()

            for education in resume_data.education:
                degree_lower = education.degree.lower()

                # Check for degree level matches
                if any(
                    keyword in requirement_lower
                    for keyword in ["bachelor", "undergraduate", "bs", "ba"]
                ):
                    if any(
                        keyword in degree_lower
                        for keyword in ["bachelor", "undergraduate", "bs", "ba"]
                    ):
                        score += 100 / total_requirements
                        break

                elif any(
                    keyword in requirement_lower
                    for keyword in ["master", "graduate", "ms", "ma", "mba"]
                ):
                    if any(
                        keyword in degree_lower
                        for keyword in ["master", "graduate", "ms", "ma", "mba"]
                    ):
                        score += 100 / total_requirements
                        break

                elif any(
                    keyword in requirement_lower for keyword in ["phd", "doctorate"]
                ):
                    if any(keyword in degree_lower for keyword in ["phd", "doctorate"]):
                        score += 100 / total_requirements
                        break

                # General degree match
                elif "degree" in requirement_lower and "degree" in degree_lower:
                    score += 50 / total_requirements
                    break

        return min(score, 100)

    def calculate_experience_match_score(
        self, resume_data: ResumeData, job_description: JobDescription
    ) -> float:
        """Calculate experience matching score"""
        if not resume_data.experience:
            return 0

        # Extract years from job description
        exp_requirement = job_description.experience_requirements
        required_years = self._extract_years_from_text(exp_requirement)

        # Calculate total experience years from resume
        total_years = 0
        for exp in resume_data.experience:
            years = self._extract_years_from_duration(exp.duration)
            total_years += years

        if required_years == 0:
            return 100  # No specific requirement

        # Score based on experience ratio
        ratio = total_years / required_years
        if ratio >= 1.0:
            score = 100
        elif ratio >= 0.8:
            score = 80 + (ratio - 0.8) * 100  # 80-100 for 80-100% of requirement
        elif ratio >= 0.5:
            score = 50 + (ratio - 0.5) * 100  # 50-80 for 50-80% of requirement
        else:
            score = ratio * 100  # 0-50 for <50% of requirement

        return min(score, 100)

    def _extract_years_from_text(self, text: str) -> int:
        """Extract years from text like '3+ years' or '2-5 years'"""
        if not text:
            return 0

        # Look for patterns like "3+ years", "2-5 years", "minimum 4 years"
        patterns = [
            r"(\d+)\+?\s*years?",
            r"minimum\s+of\s+(\d+)",
            r"at\s+least\s+(\d+)",
            r"(\d+)-\d+\s*years?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))

        return 0

    def _extract_years_from_duration(self, duration: str) -> float:
        """Extract years from duration string like '2020-2023' or '2 years'"""
        if not duration:
            return 0

        # Try to extract year range
        year_match = re.search(r"(\d{4})\s*-\s*(\d{4})", duration)
        if year_match:
            start_year = int(year_match.group(1))
            end_year = int(year_match.group(2))
            return end_year - start_year

        # Try to extract explicit years
        years_match = re.search(r"(\d+(?:\.\d+)?)\s*years?", duration.lower())
        if years_match:
            return float(years_match.group(1))

        # Try to extract months and convert
        months_match = re.search(r"(\d+)\s*months?", duration.lower())
        if months_match:
            return int(months_match.group(1)) / 12

        return 1.0  # Default assumption: 1 year

    def calculate_format_compliance_score(self, resume_data: ResumeData) -> float:
        """Calculate ATS format compliance score"""
        score = 0
        max_score = 100

        # Check for contact information (25 points)
        if resume_data.contact_info.emails:
            score += 15
        if resume_data.contact_info.phones:
            score += 10

        # Check for required sections (40 points)
        if resume_data.experience:
            score += 20
        if resume_data.education:
            score += 10
        if resume_data.skills:
            score += 10

        # Check for proper formatting indicators (35 points)
        text = resume_data.raw_text

        # Bullet points usage
        if re.search(r"[•\-\*]\s+", text):
            score += 10

        # Consistent structure (check for section headers)
        section_headers = len(re.findall(r"\n[A-Z][A-Z\s]+:\s*\n", text))
        if section_headers >= 3:
            score += 10
        elif section_headers >= 1:
            score += 5

        # Length check (not too short, not too long)
        word_count = len(text.split())
        if 300 <= word_count <= 1000:
            score += 10
        elif 200 <= word_count <= 1500:
            score += 5

        # Check for excessive special characters
        special_char_ratio = len(re.findall(r"[^\w\s\-\.\,\(\)]", text)) / len(text)
        if special_char_ratio < 0.05:
            score += 5

        return min(score, max_score)

    def calculate_action_verbs_grammar_score(self, resume_data: ResumeData) -> float:
        """Calculate action verbs and grammar score"""
        text = resume_data.raw_text.lower()
        score = 0

        # Count action verbs usage
        action_verb_count = 0
        for verb in self.action_verbs:
            action_verb_count += len(re.findall(rf"\b{verb}\b", text))

        # Score based on action verb density
        word_count = len(text.split())
        if word_count > 0:
            verb_density = action_verb_count / word_count
            verb_score = min(verb_density * 1000, 60)  # Cap at 60 points
        else:
            verb_score = 0

        # Check for passive voice (deduct points)
        passive_indicators = ["was", "were", "been", "being"]
        passive_count = sum(
            len(re.findall(rf"\b{indicator}\b", text))
            for indicator in passive_indicators
        )
        passive_penalty = min(passive_count * 2, 20)  # Max 20 point penalty

        # Check for quantified achievements (bonus points)
        numbers_pattern = r"\d+%|\d+\s*(?:percent|million|thousand|k\b)"
        quantified_achievements = len(re.findall(numbers_pattern, text))
        quantified_bonus = min(quantified_achievements * 5, 20)  # Max 20 point bonus

        # Professional language check (basic grammar)
        grammar_score = 20  # Base score

        # Check for common grammar issues
        if re.search(r"\bi\s", text):  # First person usage (should be avoided)
            grammar_score -= 10

        total_score = verb_score + grammar_score + quantified_bonus - passive_penalty
        return max(0, min(total_score, 100))

    def calculate_readability_score(self, resume_data: ResumeData) -> float:
        """Calculate readability and structure score"""
        text = resume_data.raw_text
        score = 0

        # Sentence length analysis
        sentences = re.split(r"[.!?]+", text)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(
                sentences
            )
            if 10 <= avg_sentence_length <= 20:  # Optimal range
                score += 25
            elif 8 <= avg_sentence_length <= 25:
                score += 15
            else:
                score += 5

        # Paragraph structure
        paragraphs = text.split("\n\n")
        if len(paragraphs) >= 3:
            score += 20
        elif len(paragraphs) >= 2:
            score += 10

        # White space usage (indicates good formatting)
        lines = text.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]
        if len(lines) > len(non_empty_lines):  # Has empty lines for spacing
            score += 15

        # Section organization
        if resume_data.summary:
            score += 10
        if len(resume_data.experience) > 0:
            score += 10
        if len(resume_data.education) > 0:
            score += 10
        if len(resume_data.skills) > 0:
            score += 10

        return min(score, 100)
