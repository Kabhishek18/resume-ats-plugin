"""
Resume anonymization functionality for Resume ATS Plugin.
"""

import re
import os
from typing import Dict, List, Any, Tuple, Optional
import spacy
import random
from datetime import datetime, timedelta

# Try to load a more accurate spaCy model if available
try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    try:
        nlp = spacy.load("en_core_web_md")
    except OSError:
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")


class ResumeAnonymizer:
    """Class to anonymize resumes by removing personally identifiable information."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the anonymizer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Default anonymization settings
        self.anonymize_settings = self.config.get("anonymize_settings", {
            "name": True,
            "contact_info": True,
            "education_institutions": False,
            "company_names": False,
            "dates": False,
            "addresses": True,
            "links": True,
            "age": True,
            "gender_clues": True
        })
        
        # Replacement patterns
        self.replacements = {
            "name": "[NAME]",
            "email": "[EMAIL]",
            "phone": "[PHONE]",
            "address": "[ADDRESS]",
            "url": "[URL]",
            "link": "[LINK]",
            "social": "[SOCIAL MEDIA]",
            "date": "[DATE]",
            "age": "[AGE]",
            "school": "[EDUCATIONAL INSTITUTION]",
            "company": "[COMPANY]",
            "city": "[CITY]",
            "state": "[STATE]",
            "zip": "[ZIP CODE]",
            "country": "[COUNTRY]"
        }
        
        # Custom replacements from config
        if "replacements" in self.config:
            self.replacements.update(self.config["replacements"])
    
    def anonymize_text(self, text: str) -> Tuple[str, Dict[str, List[str]]]:
        """
        Anonymize resume text by replacing personally identifiable information.
        
        Args:
            text: Resume text to anonymize
            
        Returns:
            Tuple of (anonymized text, dict of replaced items)
        """
        # Store original items for reference
        replaced_items = {
            "names": [],
            "emails": [],
            "phones": [],
            "addresses": [],
            "links": [],
            "dates": [],
            "institutions": [],
            "companies": []
        }
        
        # Process with spaCy for named entity recognition
        doc = nlp(text)
        
        # Create a copy of the text we'll modify
        anonymized = text
        
        # Process named entities
        for ent in doc.ents:
            original = ent.text
            
            # Handle entities based on type
            if ent.label_ == "PERSON" and self.anonymize_settings["name"]:
                anonymized = self._replace_text(anonymized, original, self.replacements["name"])
                replaced_items["names"].append(original)
                
            elif ent.label_ == "ORG":
                # Check if it looks like an educational institution
                if any(edu_term in original.lower() for edu_term in ["university", "college", "school", "institute"]):
                    if self.anonymize_settings["education_institutions"]:
                        anonymized = self._replace_text(anonymized, original, self.replacements["school"])
                        replaced_items["institutions"].append(original)
                # Otherwise treat as company
                elif self.anonymize_settings["company_names"]:
                    anonymized = self._replace_text(anonymized, original, self.replacements["company"])
                    replaced_items["companies"].append(original)
                    
            elif ent.label_ in ["GPE", "LOC"] and self.anonymize_settings["addresses"]:
                # If it's a city, state, country, etc.
                anonymized = self._replace_text(anonymized, original, self.replacements["city"])
                replaced_items["addresses"].append(original)
                
            elif ent.label_ == "DATE" and self.anonymize_settings["dates"]:
                anonymized = self._replace_text(anonymized, original, self.replacements["date"])
                replaced_items["dates"].append(original)
        
        # Process with regex patterns for items NER might miss
        
        # Email addresses
        if self.anonymize_settings["contact_info"]:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            for match in re.finditer(email_pattern, anonymized):
                original = match.group(0)
                anonymized = self._replace_text(anonymized, original, self.replacements["email"])
                replaced_items["emails"].append(original)
            
            # Phone numbers - various formats
            phone_patterns = [
                r'\b\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',  # North American
                r'\b\+?[1-9]\d{1,3}[-.\s]?\d{1,3}[-.\s]?\d{3,5}\b'  # International
            ]
            
            for pattern in phone_patterns:
                for match in re.finditer(pattern, anonymized):
                    original = match.group(0)
                    anonymized = self._replace_text(anonymized, original, self.replacements["phone"])
                    replaced_items["phones"].append(original)
            
            # URLs and links
            if self.anonymize_settings["links"]:
                # General URLs
                url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
                for match in re.finditer(url_pattern, anonymized):
                    original = match.group(0)
                    anonymized = self._replace_text(anonymized, original, self.replacements["url"])
                    replaced_items["links"].append(original)
                
                # LinkedIn URLs
                linkedin_pattern = r'linkedin\.com/in/[\w-]+'
                for match in re.finditer(linkedin_pattern, anonymized):
                    original = match.group(0)
                    anonymized = self._replace_text(anonymized, original, self.replacements["social"])
                    replaced_items["links"].append(original)
                
                # GitHub URLs
                github_pattern = r'github\.com/[\w-]+'
                for match in re.finditer(github_pattern, anonymized):
                    original = match.group(0)
                    anonymized = self._replace_text(anonymized, original, self.replacements["social"])
                    replaced_items["links"].append(original)
        
        # Addresses
        if self.anonymize_settings["addresses"]:
            # Street addresses (simplified)
            address_pattern = r'\b\d{1,5}\s+[A-Za-z0-9\s,]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl|Terrace|Ter)\b'
            for match in re.finditer(address_pattern, anonymized, re.IGNORECASE):
                original = match.group(0)
                anonymized = self._replace_text(anonymized, original, self.replacements["address"])
                replaced_items["addresses"].append(original)
            
            # ZIP/Postal codes
            zip_pattern = r'\b\d{5}(?:-\d{4})?\b'  # US ZIP codes
            for match in re.finditer(zip_pattern, anonymized):
                original = match.group(0)
                anonymized = self._replace_text(anonymized, original, self.replacements["zip"])
                replaced_items["addresses"].append(original)
        
        # Age indicators
        if self.anonymize_settings["age"]:
            age_patterns = [
                r'\b(?:age|aged)[\s:]+\d{1,2}\b',
                r'\b\d{1,2}[\s-]+years[\s-]+old\b'
            ]
            for pattern in age_patterns:
                for match in re.finditer(pattern, anonymized, re.IGNORECASE):
                    original = match.group(0)
                    anonymized = self._replace_text(anonymized, original, self.replacements["age"])
        
        # Gender indicators
        if self.anonymize_settings["gender_clues"]:
            gender_indicators = [
                r'\b(?:Mr|Ms|Mrs|Miss|He|She|Him|Her|His|Hers)\b'
            ]
            for pattern in gender_indicators:
                for match in re.finditer(pattern, anonymized, re.IGNORECASE):
                    # Only replace if it's standalone or at start of sentence
                    if match.start() == 0 or anonymized[match.start()-1].isspace():
                        original = match.group(0)
                        # Replace with appropriate neutral form
                        replacement = "They" if original.lower() in ["he", "she"] else \
                                     "Them" if original.lower() in ["him", "her"] else \
                                     "Their" if original.lower() in ["his", "hers"] else \
                                     "Mx" if original.lower() in ["mr", "ms", "mrs", "miss"] else \
                                     original
                        anonymized = self._replace_text(anonymized, original, replacement)
        
        return anonymized, replaced_items
    
    def anonymize_file(self, input_path: str, output_path: Optional[str] = None) -> Tuple[str, Dict[str, List[str]]]:
        """
        Anonymize a resume file.
        
        Args:
            input_path: Path to the resume file
            output_path: Optional path to save the anonymized file. If None, will use input_path with "_anon" suffix.
            
        Returns:
            Tuple of (output file path, dict of replaced items)
        """
        from .utils import extract_text_from_pdf, extract_text_from_docx
        
        # Determine file type and extract text
        file_ext = os.path.splitext(input_path)[1].lower()
        
        if file_ext == '.pdf':
            text = extract_text_from_pdf(input_path)
        elif file_ext in ['.docx', '.doc']:
            text = extract_text_from_docx(input_path)
        else:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
        
        # Anonymize the text
        anonymized_text, replaced_items = self.anonymize_text(text)
        
        # If no output path provided, create one
        if output_path is None:
            base_name, ext = os.path.splitext(input_path)
            output_path = f"{base_name}_anonymized{ext}"
        
        # Write the anonymized text to the output file
        if file_ext == '.pdf':
            self._write_anonymized_pdf(input_path, output_path, anonymized_text)
        elif file_ext in ['.docx', '.doc']:
            self._write_anonymized_docx(input_path, output_path, anonymized_text)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(anonymized_text)
        
        return output_path, replaced_items
    
    def _replace_text(self, text: str, original: str, replacement: str) -> str:
        """
        Replace all occurrences of original with replacement in text.
        Uses word boundaries to avoid partial matches.
        
        Args:
            text: Text to modify
            original: Text to replace
            replacement: Replacement text
            
        Returns:
            Modified text
        """
        # Escape special regex characters in the original text
        escaped_original = re.escape(original)
        
        # Replace with word boundaries when appropriate
        if original[0].isalnum() and original[-1].isalnum():
            pattern = r'\b' + escaped_original + r'\b'
        else:
            pattern = escaped_original
            
        return re.sub(pattern, replacement, text)
    
    def _write_anonymized_pdf(self, input_path: str, output_path: str, anonymized_text: str) -> None:
        """
        Write anonymized text to a PDF file.
        
        Args:
            input_path: Original PDF path
            output_path: Output PDF path
            anonymized_text: Anonymized text content
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.platypus import SimpleDocTemplate, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            
            # Simple approach: create a new PDF with the anonymized text
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Split into paragraphs and create content
            paragraphs = []
            for para in anonymized_text.split('\n\n'):
                if para.strip():
                    paragraphs.append(Paragraph(para.replace('\n', '<br/>'), styles["Normal"]))
            
            # Build document
            doc.build(paragraphs)
            
        except ImportError:
            # Fallback if ReportLab is not available: just write to text file
            with open(output_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
                f.write(anonymized_text)
    
    def _write_anonymized_docx(self, input_path: str, output_path: str, anonymized_text: str) -> None:
        """
        Write anonymized text to a DOCX file.
        
        Args:
            input_path: Original DOCX path
            output_path: Output DOCX path
            anonymized_text: Anonymized text content
        """
        try:
            from docx import Document
            
            # Create a new document
            doc = Document()
            
            # Add paragraphs
            for para in anonymized_text.split('\n\n'):
                if para.strip():
                    doc.add_paragraph(para)
            
            # Save the document
            doc.save(output_path)
            
        except ImportError:
            # Fallback if python-docx is not available: just write to text file
            with open(output_path.replace('.docx', '.txt'), 'w', encoding='utf-8') as f:
                f.write(anonymized_text)


# Convenience functions
def anonymize_resume_text(text: str, config: Optional[Dict] = None) -> Tuple[str, Dict[str, List[str]]]:
    """
    Anonymize resume text.
    
    Args:
        text: Resume text to anonymize
        config: Optional configuration dictionary
        
    Returns:
        Tuple of (anonymized text, dict of replaced items)
    """
    anonymizer = ResumeAnonymizer(config)
    return anonymizer.anonymize_text(text)


def anonymize_resume_file(file_path: str, output_path: Optional[str] = None, 
                         config: Optional[Dict] = None) -> Tuple[str, Dict[str, List[str]]]:
    """
    Anonymize a resume file.
    
    Args:
        file_path: Path to the resume file
        output_path: Optional path to save the anonymized file
        config: Optional configuration dictionary
        
    Returns:
        Tuple of (output file path, dict of replaced items)
    """
    anonymizer = ResumeAnonymizer(config)
    return anonymizer.anonymize_file(file_path, output_path)
