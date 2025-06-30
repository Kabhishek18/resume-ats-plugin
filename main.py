import re
import spacy
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import pandas as pd

class ATSResumeScorer:
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Please install spaCy English model: python -m spacy download en_core_web_sm")
            
        # Common ATS-friendly sections
        self.required_sections = [
            'experience', 'education', 'skills', 'contact'
        ]
        
        # Technical skills database (expand as needed)
        self.tech_skills = {
            'programming': ['python', 'java', 'javascript', 'c++', 'sql', 'r'],
            'frameworks': ['react', 'django', 'flask', 'spring', 'angular'],
            'tools': ['git', 'docker', 'kubernetes', 'aws', 'azure'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis']
        }

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF resume"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text

    def extract_contact_info(self, text):
        """Extract contact information"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        
        return {
            'emails': emails,
            'phones': phones,
            'has_contact': len(emails) > 0 and len(phones) > 0
        }

    def extract_skills(self, text):
        """Extract technical skills from resume"""
        text_lower = text.lower()
        found_skills = []
        
        for category, skills in self.tech_skills.items():
            for skill in skills:
                if skill in text_lower:
                    found_skills.append(skill)
        
        return found_skills

    def check_ats_formatting(self, text):
        """Check ATS-friendly formatting"""
        score = 0
        issues = []
        
        # Check for proper sections
        sections_found = 0
        for section in self.required_sections:
            if section.lower() in text.lower():
                sections_found += 1
        
        score += (sections_found / len(self.required_sections)) * 25
        
        # Check for bullet points (good for ATS)
        if '•' in text or '*' in text or '-' in text:
            score += 15
        else:
            issues.append("No bullet points found - consider using them for better ATS parsing")
        
        # Check length (optimal range)
        word_count = len(text.split())
        if 300 <= word_count <= 800:
            score += 20
        elif word_count < 300:
            issues.append("Resume might be too short")
        else:
            issues.append("Resume might be too long for ATS systems")
        
        # Check for excessive formatting characters
        special_chars = sum(1 for c in text if not c.isalnum() and c not in ' \n\t.,;:()-')
        if special_chars < len(text) * 0.05:  # Less than 5% special characters
            score += 10
        else:
            issues.append("Too many special characters - may confuse ATS")
        
        return score, issues

    def calculate_job_match_score(self, resume_text, job_description):
        """Calculate similarity between resume and job description"""
        # Preprocess texts
        documents = [resume_text.lower(), job_description.lower()]
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000
        )
        
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
        return similarity[0][0] * 100

    def analyze_resume(self, resume_path, job_description=""):
        """Complete resume analysis"""
        # Extract text
        if resume_path.endswith('.pdf'):
            text = self.extract_text_from_pdf(resume_path)
        else:
            with open(resume_path, 'r', encoding='utf-8') as f:
                text = f.read()
        
        # Perform analysis
        contact_info = self.extract_contact_info(text)
        skills = self.extract_skills(text)
        formatting_score, formatting_issues = self.check_ats_formatting(text)
        
        # Calculate job match if job description provided
        job_match_score = 0
        if job_description:
            job_match_score = self.calculate_job_match_score(text, job_description)
        
        # Calculate overall ATS score
        contact_score = 25 if contact_info['has_contact'] else 0
        skills_score = min(len(skills) * 5, 30)  # Max 30 points for skills
        
        total_score = contact_score + skills_score + formatting_score
        if job_description:
            total_score = (total_score + job_match_score) / 2
        
        # Prepare results
        results = {
            'overall_score': round(total_score, 2),
            'contact_info': contact_info,
            'skills_found': skills,
            'skills_count': len(skills),
            'formatting_score': formatting_score,
            'formatting_issues': formatting_issues,
            'job_match_score': round(job_match_score, 2) if job_description else "Not calculated",
            'recommendations': self.get_recommendations(total_score, skills, formatting_issues)
        }
        
        return results

    def get_recommendations(self, score, skills, issues):
        """Provide improvement recommendations"""
        recommendations = []
        
        if score < 50:
            recommendations.append("Major improvements needed for ATS compatibility")
        elif score < 70:
            recommendations.append("Some improvements needed for better ATS scoring")
        else:
            recommendations.append("Good ATS compatibility!")
        
        if len(skills) < 5:
            recommendations.append("Add more relevant technical skills")
        
        recommendations.extend(issues)
        
        return recommendations

# Example usage
if __name__ == "__main__":
    scorer = ATSResumeScorer()
    
    # Example job description
    job_desc = """
    We are looking for a Python developer with experience in Django, 
    machine learning, and cloud technologies. Required skills include 
    Python, SQL, Git, and AWS. Experience with data analysis preferred.
    """
    
    # Analyze resume (replace with actual file path)
    # results = scorer.analyze_resume("resume.pdf", job_desc)
    
    # Print results
    # print(f"ATS Score: {results['overall_score']}/100")
    # print(f"Skills Found: {results['skills_found']}")
    # print(f"Recommendations: {results['recommendations']}")