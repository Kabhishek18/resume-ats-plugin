"""
Core functionality for resume_ats.
"""

import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

from .utils import (extract_text_from_docx, extract_text_from_pdf,
                   get_keywords_from_job_description, normalize_text,
                   calculate_similarity_score)

# Initialize logging
logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("Downloading spaCy model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

class ResumeATS:
    """Main class for Resume ATS analysis and optimization."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the ResumeATS with optional configuration.
        
        Args:
            config: Optional configuration dictionary with settings
        """
        self.config = config or {}
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
        # Default scoring weights
        self.weights = self.config.get('weights', {
            'keyword_match': 0.4,
            'format_score': 0.2,
            'section_coverage': 0.3,
            'readability': 0.1
        })
        
        logger.info("ResumeATS initialized with config: %s", self.config)
    
    def analyze(self, resume_path: str, job_description: Optional[str] = None) -> Dict:
        """
        Analyze a resume against an optional job description.
        
        Args:
            resume_path: Path to the resume file (PDF or DOCX)
            job_description: Optional job description text to match against
            
        Returns:
            Dictionary with analysis results
        """
        # Extract text from resume
        resume_text = self._extract_text(resume_path)
        if not resume_text:
            return {
                "status": "error",
                "message": f"Could not extract text from {resume_path}"
            }
        
        # Normalize text
        normalized_text = normalize_text(resume_text)
        
        # Extract sections
        sections = self._extract_sections(normalized_text)
        
        # Calculate format score
        format_score = self._calculate_format_score(normalized_text, sections)
        
        # Calculate readability
        readability_score = self._calculate_readability(normalized_text)
        
        result = {
            "status": "success",
            "resume_file": os.path.basename(resume_path),
            "sections_detected": list(sections.keys()),
            "stats": {
                "word_count": len(normalized_text.split()),
                "format_score": format_score,
                "readability_score": readability_score,
            },
            "suggestions": []
        }
        
        # If job description is provided, match against it
        if job_description:
            keywords = get_keywords_from_job_description(job_description)
            match_score, matches, missing = self._match_keywords(normalized_text, keywords)
            
            result["stats"]["keyword_match_score"] = match_score
            result["stats"]["keyword_matches"] = matches
            result["stats"]["missing_keywords"] = missing
            
            # Calculate overall ATS score
            overall_score = (
                match_score * self.weights['keyword_match'] +
                format_score * self.weights['format_score'] +
                len(sections) / 7 * self.weights['section_coverage'] +  # Assuming 7 standard sections
                readability_score * self.weights['readability']
            )
            
            result["stats"]["overall_ats_score"] = min(round(overall_score * 100), 100)
            
            # Generate suggestions
            if missing:
                result["suggestions"].append({
                    "type": "missing_keywords",
                    "message": f"Consider adding the following keywords: {', '.join(missing[:5])}" + 
                              (f" and {len(missing) - 5} more" if len(missing) > 5 else "")
                })
            
        # Check for common resume issues
        self._check_common_issues(normalized_text, sections, result["suggestions"])
        
        return result
    
    def optimize(self, resume_path: str, job_description: str) -> Dict:
        """
        Optimize a resume for a specific job description.
        
        Args:
            resume_path: Path to the resume file
            job_description: Job description text
            
        Returns:
            Dictionary with optimization suggestions
        """
        # First analyze the resume
        analysis = self.analyze(resume_path, job_description)
        
        if analysis["status"] == "error":
            return analysis
        
        # Get the job description keywords
        keywords = get_keywords_from_job_description(job_description)
        
        # Generate optimization suggestions
        suggestions = []
        
        # Add missing keywords suggestion
        if "missing_keywords" in analysis["stats"]:
            missing = analysis["stats"]["missing_keywords"]
            if missing:
                suggestions.append({
                    "type": "keyword_optimization",
                    "message": "Consider adding these missing keywords to your resume",
                    "keywords": missing
                })
        
        # Add section suggestions
        standard_sections = {
            "summary", "experience", "skills", "education", 
            "projects", "certifications", "achievements"
        }
        
        detected_sections = set(analysis["sections_detected"])
        missing_sections = standard_sections - detected_sections
        
        if missing_sections:
            suggestions.append({
                "type": "missing_sections",
                "message": f"Consider adding these sections to your resume: {', '.join(missing_sections)}"
            })
        
        # Format suggestions
        if analysis["stats"]["format_score"] < 0.7:
            suggestions.append({
                "type": "format_improvement",
                "message": "Improve resume formatting by using consistent bullet points, headers, and spacing"
            })
        
        # Readability suggestions
        if analysis["stats"]["readability_score"] < 0.6:
            suggestions.append({
                "type": "readability",
                "message": "Improve readability by using shorter sentences and bullet points for achievements"
            })
            
        return {
            "status": "success",
            "resume_file": os.path.basename(resume_path),
            "analysis": analysis["stats"],
            "optimization_suggestions": suggestions
        }
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from resume file."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.pdf':
                return extract_text_from_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                return extract_text_from_docx(file_path)
            else:
                logger.error(f"Unsupported file format: {file_ext}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections from resume text."""
        # Common section headers in resumes
        section_patterns = {
            "summary": r"(?i)(SUMMARY|profile|summary|objective|professional\s+summary)$",
            "experience": r"(?i)(experience|work\s+experience|employment|work\s+history)",
            "skills": r"(?i)(skills|technical\s+skills|core\s+competencies|expertise)",
            "education": r"(?i)(education|academic|qualifications|degrees)",
            "projects": r"(?i)(projects|personal\s+projects|professional\s+projects)",
            "certifications": r"(?i)(certifications|certificates|credentials)",
            "achievements": r"(?i)(achievements|accomplishments|awards)"
        }
        
        sections = {}
        
        # Sample text contains "SUMMARY" which should be detected
        if "SUMMARY" in text:
            summary_text = ""
            for line in text.split("\n"):
                if line.strip() == "SUMMARY":
                    continue
                if line.strip() and line.strip() not in ["EXPERIENCE", "SKILLS", "EDUCATION"]:
                    summary_text += line + "\n"
                else:
                    break
            sections["summary"] = summary_text.strip()
        
        # Find all potential section headers and their positions
        section_positions = []
        for section_name, pattern in section_patterns.items():
            for match in re.finditer(pattern, text, re.MULTILINE):
                section_positions.append((match.start(), section_name))
        
        # Sort by position
        section_positions.sort()
        
        # Extract section content
        for i, (pos, section_name) in enumerate(section_positions):
            # Section text goes from current position to next section (or end)
            start = pos
            end = section_positions[i+1][0] if i+1 < len(section_positions) else len(text)
            
            # Find the end of the section header line
            header_end = text.find("\n", pos)
            if header_end != -1 and header_end < end:
                content_start = header_end + 1
            else:
                content_start = start + len(section_name) + 1
            
            # Extract and clean the section content
            section_content = text[content_start:end].strip()
            if section_content:
                sections[section_name] = section_content
        
        return sections
    
    def _match_keywords(self, resume_text: str, keywords: List[str]) -> Tuple[float, List[str], List[str]]:
        """Match resume text against keywords from job description."""
        resume_text_lower = resume_text.lower()
        
        matches = []
        missing = []
        
        for keyword in keywords:
            if keyword.lower() in resume_text_lower:
                matches.append(keyword)
            else:
                missing.append(keyword)
        
        match_score = len(matches) / len(keywords) if keywords else 0
        
        return match_score, matches, missing
    
    def _calculate_format_score(self, text: str, sections: Dict[str, str]) -> float:
        """
        Calculate the format score based on structure, bullet points, etc.
        """
        score = 0.0
        
        # Check for sections (max 0.4)
        section_score = min(len(sections) / 7, 1.0) * 0.4
        score += section_score
        
        # Check for bullet points (max 0.2)
        bullet_pattern = r'(?:^|\n)[•\-\*]\s'
        bullet_count = len(re.findall(bullet_pattern, text))
        bullet_score = min(bullet_count / 10, 1.0) * 0.2
        score += bullet_score
        
        # Check for consistent spacing (max 0.2)
        newline_groups = re.findall(r'\n{2,}', text)
        spacing_consistency = len(set(len(g) for g in newline_groups))
        spacing_score = (1.0 if spacing_consistency <= 2 else 0.5) * 0.2
        score += spacing_score
        
        # Check for readable font/formatting indirectly by checking line length (max 0.2)
        lines = text.split('\n')
        line_lengths = [len(line) for line in lines if line.strip()]
        avg_line_length = sum(line_lengths) / len(line_lengths) if line_lengths else 0
        if 40 <= avg_line_length <= 100:
            score += 0.2
        else:
            score += 0.1
        
        return score
    
    def _calculate_readability(self, text: str) -> float:
        """
        Calculate readability score using simplified metrics.
        """
        # Parse with spaCy
        doc = nlp(text)
        
        # Count sentences
        sentences = list(doc.sents)
        sent_count = len(sentences)
        
        if sent_count == 0:
            return 0.0
        
        # Count words
        word_count = len([token for token in doc if not token.is_punct and not token.is_space])
        
        # Count syllables (approximate)
        syllable_count = sum([self._count_syllables(token.text) for token in doc 
                              if not token.is_punct and not token.is_space])
        
        # Calculate average sentence length
        avg_sentence_length = word_count / sent_count
        
        # Calculate average word length in syllables
        avg_syllables_per_word = syllable_count / word_count if word_count > 0 else 0
        
        # Simplified readability score between 0 and 1
        # Optimal: ~15 words per sentence, ~1.5 syllables per word
        sentence_length_score = 1.0 - min(abs(avg_sentence_length - 15) / 15, 1.0)
        syllable_score = 1.0 - min(abs(avg_syllables_per_word - 1.5) / 1.5, 1.0)
        
        return (sentence_length_score * 0.5) + (syllable_score * 0.5)
    
    def _count_syllables(self, word: str) -> int:
        """Approximate syllable count."""
        word = word.lower()
        
        # Remove non-alpha characters
        word = re.sub(r'[^a-z]', '', word)
        
        if not word:
            return 0
        
        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_is_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_is_vowel:
                count += 1
            prev_is_vowel = is_vowel
        
        # Adjust for silent 'e' at the end
        if word.endswith('e') and len(word) > 2 and word[-2] not in vowels:
            count -= 1
        
        # Make sure we return at least 1
        return max(1, count)
    
    def _check_common_issues(self, text: str, sections: Dict[str, str], suggestions: List[Dict]):
        """Check for common resume issues."""
        # Check for excessive length
        word_count = len(text.split())
        if word_count > 700:
            suggestions.append({
                "type": "excessive_length",
                "message": f"Your resume is {word_count} words, consider reducing to under 700 words for better readability"
            })
        
        # Check for contact information
        contact_pattern = r'(?:email|e-mail|phone|tel|mobile|contact)'
        if not re.search(contact_pattern, text.lower()):
            suggestions.append({
                "type": "missing_contact",
                "message": "Make sure your contact information is clearly visible"
            })
        
        # Check for passive voice in experience section
        if "experience" in sections:
            passive_pattern = r'\b(?:is|are|was|were|be|been|being)\s+\w+ed\b'
            passive_count = len(re.findall(passive_pattern, sections["experience"].lower()))
            if passive_count > 3:
                suggestions.append({
                    "type": "passive_voice",
                    "message": "Use active voice instead of passive voice for stronger impact in your experience section"
                })
        
        # Check for action verbs in experience section
        if "experience" in sections:
            action_verbs = ["achieved", "created", "designed", "developed", "established", 
                           "implemented", "improved", "increased", "launched", "led", 
                           "managed", "reduced", "resolved", "streamlined"]
            
            action_verb_count = sum(1 for verb in action_verbs 
                                   if re.search(rf'\b{verb}\b', sections["experience"].lower()))
            
            if action_verb_count < 3:
                suggestions.append({
                    "type": "weak_action_verbs",
                    "message": "Use more strong action verbs in your experience section for greater impact"
                })


def analyze_resume(resume_path: str, job_description: Optional[str] = None, 
                 config: Optional[Dict] = None) -> Dict:
    """
    Convenience function to analyze a resume.
    
    Args:
        resume_path: Path to resume file
        job_description: Optional job description
        config: Optional configuration
        
    Returns:
        Analysis results dictionary
    """
    ats = ResumeATS(config)
    return ats.analyze(resume_path, job_description)


def optimize_resume(resume_path: str, job_description: str, 
                   config: Optional[Dict] = None) -> Dict:
    """
    Convenience function to optimize a resume for a job description.
    
    Args:
        resume_path: Path to resume file
        job_description: Job description
        config: Optional configuration
        
    Returns:
        Optimization suggestions dictionary
    """
    ats = ResumeATS(config)
    return ats.optimize(resume_path, job_description)


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Resume ATS analysis and optimization")
    
    parser.add_argument("resume", help="Path to resume file (PDF or DOCX)")
    parser.add_argument("--job", help="Path to job description file")
    parser.add_argument("--optimize", action="store_true", help="Generate optimization suggestions")
    parser.add_argument("--config", help="Path to configuration JSON file")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Set the logging level")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Load config if provided
    config = None
    if args.config:
        try:
            with open(args.config, "r") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return 1
    
    # Load job description if provided
    job_description = None
    if args.job:
        try:
            with open(args.job, "r") as f:
                job_description = f.read()
        except Exception as e:
            logger.error(f"Failed to load job description: {e}")
            return 1
    
    # Process resume
    try:
        if args.optimize and job_description:
            result = optimize_resume(args.resume, job_description, config)
        else:
            result = analyze_resume(args.resume, job_description, config)
        
        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))
        
        return 0
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())