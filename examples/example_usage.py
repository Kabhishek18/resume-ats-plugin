
# examples/example_usage.py
"""
Example usage of the ATS Resume Scorer Plugin
"""

import json
from ats_resume_scorer import ATSResumeScorer, ScoringWeights

def basic_example():
    """Basic usage example"""
    print("=== Basic ATS Resume Scoring ===")
    
    # Initialize scorer with default weights
    scorer = ATSResumeScorer()
    
    # Sample job description
    job_description = """
    Software Engineer - Python Developer
    
    We are seeking a skilled Python developer to join our team.
    
    Required Skills:
    - Python programming
    - Django or Flask framework
    - SQL databases
    - Git version control
    - RESTful API development
    
    Preferred Skills:
    - AWS cloud services
    - Docker containerization
    - React.js frontend
    - Agile methodology
    
    Requirements:
    - Bachelor's degree in Computer Science or related field
    - 3+ years of software development experience
    - Strong problem-solving skills
    """
    
    # Score resume (replace with actual resume path)
    try:
        result = scorer.score_resume('sample_resume.pdf', job_description)
        
        print(f"Overall Score: {result['overall_score']}/100")
        print(f"Grade: {result['grade']}")
        print("\nDetailed Breakdown:")
        for category, score in result['detailed_breakdown'].items():
            print(f"  {category.replace('_', ' ').title()}: {score:.1f}")
        
        print("\nRecommendations:")
        for rec in result['recommendations']:
            print(f"  • {rec}")
            
    except FileNotFoundError:
        print("Sample resume file not found. Please provide a valid resume path.")

def custom_weights_example():
    """Example with custom scoring weights"""
    print("\n=== Custom Weights Example ===")
    
    # Define custom weights (emphasizing skills matching)
    custom_weights = ScoringWeights(
        keyword_match=0.40,      # Increased from 30%
        title_match=0.10,
        education_match=0.05,    # Decreased from 10%
        experience_match=0.20,   # Increased from 15%
        format_compliance=0.10,  # Decreased from 15%
        action_verbs_grammar=0.10,
        readability=0.05         # Decreased from 10%
    )
    
    scorer = ATSResumeScorer(weights=custom_weights)
    
    print("Custom weights applied:")
    print(f"  Keyword Match: {custom_weights.keyword_match:.0%}")
    print(f"  Experience Match: {custom_weights.experience_match:.0%}")
    print("  (Other weights adjusted accordingly)")

def api_integration_example():
    """Example for API integration"""
    print("\n=== API Integration Example ===")
    
    def score_resume_api(resume_file, job_desc_text):
        """Function that could be used in a web API"""
        scorer = ATSResumeScorer()
        
        try:
            result = scorer.score_resume(resume_file, job_desc_text)
            
            # Format for API response
            api_response = {
                "status": "success",
                "data": {
                    "score": result['overall_score'],
                    "grade": result['grade'],
                    "analysis": result['detailed_breakdown'],
                    "suggestions": result['recommendations'][:3],  # Top 3 suggestions
                    "match_info": result['job_match_analysis']
                }
            }
            return api_response
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    # Example API call
    sample_jd = "Python developer position requiring Django, SQL, and 2+ years experience."
    api_result = score_resume_api('sample_resume.pdf', sample_jd)
    
    print("API Response Format:")
    print(json.dumps(api_result, indent=2))

def batch_processing_example():
    """Example for processing multiple resumes"""
    print("\n=== Batch Processing Example ===")
    
    def batch_score_resumes(resume_files, job_description):
        """Score multiple resumes against one job description"""
        scorer = ATSResumeScorer()
        results = []
        
        for resume_file in resume_files:
            try:
                result = scorer.score_resume(resume_file, job_description)
                results.append({
                    "file": resume_file,
                    "score": result['overall_score'],
                    "grade": result['grade'],
                    "top_recommendation": result['recommendations'][0] if result['recommendations'] else "No recommendations"
                })
            except Exception as e:
                results.append({
                    "file": resume_file,
                    "error": str(e)
                })
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results
    
    # Example batch processing
    resume_files = ['resume1.pdf', 'resume2.pdf', 'resume3.pdf']
    job_desc = "Senior Python developer with machine learning experience."
    
    print("Batch processing would rank candidates as:")
    print("1. resume1.pdf - Score: 85, Grade: A")
    print("2. resume3.pdf - Score: 78, Grade: B") 
    print("3. resume2.pdf - Score: 65, Grade: C")

def report_customization_example():
    """Example of customizing reports"""
    print("\n=== Report Customization Example ===")
    
    class CustomReportGenerator:
        """Extended report generator with custom formatting"""
        
        @staticmethod
        def generate_executive_summary(result):
            """Generate executive summary for hiring managers"""
            score = result['overall_score']
            grade = result['grade']
            
            if score >= 90:
                recommendation = "HIGHLY RECOMMENDED - Excellent match"
            elif score >= 80:
                recommendation = "RECOMMENDED - Good match with minor gaps"
            elif score >= 70:
                recommendation = "CONDITIONAL - Consider with reservations"
            else:
                recommendation = "NOT RECOMMENDED - Significant gaps"
            
            return {
                "candidate_rating": recommendation,
                "overall_score": score,
                "key_strengths": CustomReportGenerator._get_strengths(result),
                "areas_for_improvement": result['recommendations'][:2],
                "next_steps": CustomReportGenerator._get_next_steps(score)
            }
        
        @staticmethod
        def _get_strengths(result):
            """Identify top performing areas"""
            scores = result['detailed_breakdown']
            strengths = []
            
            for category, score in scores.items():
                if score >= 85:
                    strengths.append(category.replace('_', ' ').title())
            
            return strengths or ["Contact hiring manager for detailed review"]
        
        @staticmethod
        def _get_next_steps(score):
            """Suggest next steps based on score"""
            if score >= 80:
                return "Schedule interview"
            elif score >= 70:
                return "Phone screening recommended"
            else:
                return "Request additional information or updated resume"
    
    # Example usage
    sample_result = {
        'overall_score': 82.5,
        'grade': 'B',
        'detailed_breakdown': {
            'keyword_match': 90,
            'format_compliance': 85,
            'experience_match': 80
        },
        'recommendations': [
            "Add cloud computing skills",
            "Include more quantified achievements"
        ]
    }
    
    executive_summary = CustomReportGenerator.generate_executive_summary(sample_result)
    print("Executive Summary:")
    print(f"  Rating: {executive_summary['candidate_rating']}")
    print(f"  Next Steps: {executive_summary['next_steps']}")

if __name__ == "__main__":
    basic_example()
    custom_weights_example()
    api_integration_example()
    batch_processing_example()
    report_customization_example()

