
# README.md
# ATS Resume Scorer Plugin

A comprehensive Python-based plugin to score resumes against ATS (Applicant Tracking System) standards and job descriptions with actionable feedback.

## Features

### 📄 Resume Parsing Module
- Supports `.pdf`, `.docx`, and `.txt` formats
- Extracts structured data: contact info, skills, education, experience
- Uses native Python libraries for reliable parsing

### 📑 Job Description Matching Module  
- Parses job descriptions and extracts key requirements
- Identifies required vs preferred skills
- Extracts education and experience requirements

### 🧠 Configurable ATS Scoring Engine
- **Keyword Match** (30%): Skills and responsibility overlap
- **Title Match** (10%): Job title alignment  
- **Education Match** (10%): Degree/qualification comparison
- **Experience Match** (15%): Relevant experience assessment
- **Format Compliance** (15%): ATS-friendly formatting
- **Action Verbs & Grammar** (10%): Professional language usage
- **Readability** (10%): Structure and clarity

### 📊 Detailed Reporting
- Overall ATS score (0-100) with letter grade
- Sectional breakdown of all scoring categories
- Actionable improvement recommendations
- Missing skills identification
- Job match analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ats-resume-scorer
cd ats-resume-scorer

# Install dependencies
pip install -r requirements.txt

# Install spaCy language model
python -m spacy download en_core_web_sm

# Install the package
pip install -e .
```

## Quick Start

### Command Line Usage

```bash
# Basic usage
ats-score --resume resume.pdf --jd job_description.txt

# Save output to file
ats-score --resume resume.pdf --jd job_description.txt --output results.json

# Use custom scoring weights
ats-score --resume resume.pdf --jd job_description.txt --weights custom_weights.json
```

### Python API Usage

```python
from ats_resume_scorer import ATSResumeScorer

# Initialize scorer
scorer = ATSResumeScorer()

# Read job description
with open('job_description.txt', 'r') as f:
    jd_text = f.read()

# Score resume
result = scorer.score_resume('resume.pdf', jd_text)

print(f"ATS Score: {result['overall_score']}/100")
print(f"Grade: {result['grade']}")
print("Recommendations:", result['recommendations'])
```

## Configuration

### Custom Scoring Weights

Create a JSON file with custom weights:

```json
{
    "keyword_match": 0.35,
    "title_match": 0.15,
    "education_match": 0.10,
    "experience_match": 0.15,
    "format_compliance": 0.10,
    "action_verbs_grammar": 0.10,
    "readability": 0.05
}
```

### Extending Skills Database

Add new skills to `config/skills_database.json`:

```json
{
    "ai_ml": [
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "scikit-learn"
    ]
}
```

## Project Structure

```
ats-resume-scorer/
├── ats_resume_scorer/
│   ├── __init__.py
│   ├── main.py              # Main plugin file
│   ├── parsers/
│   │   ├── resume_parser.py
│   │   └── jd_parser.py
│   ├── scoring/
│   │   └── scoring_engine.py
│   └── utils/
│       └── report_generator.py
├── config/
│   ├── default_weights.json
│   ├── skills_database.json
│   └── action_verbs.json
├── tests/
│   ├── test_parser.py
│   ├── test_scoring.py
│   └── sample_data/
├── examples/
│   ├── sample_resume.pdf
│   ├── sample_jd.txt
│   └── example_usage.py
├── requirements.txt
├── setup.py
└── README.md
```

## API Reference

### ATSResumeScorer Class

```python
class ATSResumeScorer:
    def __init__(self, weights: Optional[ScoringWeights] = None)
    def score_resume(self, resume_path: str, jd_text: str) -> Dict[str, Any]
```

### Response Format

```json
{
    "overall_score": 78.5,
    "grade": "B",
    "detailed_breakdown": {
        "keyword_match": 85.0,
        "title_match": 60.0,
        "education_match": 90.0,
        "experience_match": 75.0,
        "format_compliance": 80.0,
        "action_verbs_grammar": 70.0,
        "readability": 85.0
    },
    "recommendations": [
        "Add these missing required skills: docker, kubernetes",
        "Use more action verbs in experience descriptions"
    ],
    "job_match_analysis": {
        "required_skills_matched": 8,
        "preferred_skills_matched": 3,
        "missing_required_skills": ["docker", "kubernetes"],
        "missing_preferred_skills": ["react", "aws"]
    }
}
```

## Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=ats_resume_scorer
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.
