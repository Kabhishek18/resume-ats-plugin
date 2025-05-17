# Resume ATS Plugin

A Python plugin to analyze and optimize resumes for Applicant Tracking Systems (ATS).

## Features

- **Resume Analysis**: Evaluate how well your resume will perform with ATS systems
- **Keyword Optimization**: Match your resume against job descriptions to identify missing keywords
- **Format Checking**: Verify that your resume follows recommended formatting guidelines
- **Section Analysis**: Identify missing or weak sections in your resume
- **Optimization Suggestions**: Get actionable tips to improve your resume's ATS score
- **PDF Reports**: Generate comprehensive PDF reports with visualizations
- **Resume Anonymization**: Remove personally identifiable information for sharing
- **Version Tracking**: Keep track of resume revisions and improvements over time
- **Resume Comparison**: Compare multiple resumes or one resume against multiple job descriptions

## Installation

You can install the package via pip:
```bash
pip install resume-ats-plugin
```

## Usage

### Basic Usage

```python
from resume_ats import ResumeATS, analyze_resume, optimize_resume

# Quick analysis
result = analyze_resume('path/to/resume.pdf')
print(f"ATS Format Score: {result['stats']['format_score']:.2f}")

# Analyze against a job description
with open('job_description.txt', 'r') as f:
    job_description = f.read()

result = analyze_resume('path/to/resume.pdf', job_description)
print(f"ATS Score: {result['stats']['overall_ats_score']}%")
print(f"Keyword Match: {result['stats']['keyword_match_score']:.2f}")
print(f"Matched Keywords: {', '.join(result['stats']['keyword_matches'][:5])}")

# Get optimization suggestions
suggestions = optimize_resume('path/to/resume.pdf', job_description)
for suggestion in suggestions['optimization_suggestions']:
    print(f"- {suggestion['message']}")
```

### Enhanced Features

#### PDF Report Generation

```python
from resume_ats import analyze_and_report, optimize_and_report

# Analyze resume and generate PDF report
analysis, pdf_path = analyze_and_report('path/to/resume.pdf', job_description)
print(f"Report saved to: {pdf_path}")

# Get optimization suggestions with PDF report
optimization, pdf_path = optimize_and_report('path/to/resume.pdf', job_description)
print(f"Optimization report saved to: {pdf_path}")
```

#### Resume Anonymization

```python
from resume_ats import anonymize_resume_file, ResumeAnonymizer

# Quick anonymization with default settings
anonymized_path, replaced_items = anonymize_resume_file('path/to/resume.pdf')
print(f"Anonymized resume saved to: {anonymized_path}")
print(f"Replaced {len(replaced_items['names'])} names, {len(replaced_items['emails'])} emails")

# Advanced anonymization with custom settings
anonymizer = ResumeAnonymizer({
    "anonymize_settings": {
        "name": True,
        "contact_info": True,
        "education_institutions": False,
        "company_names": False,
        "dates": True,
        "addresses": True
    }
})
anonymized_path, _ = anonymizer.anonymize_file('path/to/resume.pdf', 'path/to/output.pdf')
```

#### Resume Version Tracking

```python
from resume_ats import EnhancedResumeATS, ResumeVersionTracker

# Initialize with version tracking
ats = EnhancedResumeATS()

# Analyze resume and automatically track version
analysis = ats.analyze('path/to/resume.pdf', job_description)
version_id = ats.track_version('path/to/resume.pdf', analysis, "Version 1")

# View version history
versions = ats.get_version_history()
for version in versions:
    print(f"{version['version_name']} - {version['timestamp']} - Score: {version['overall_ats_score']}%")

# Later, analyze an updated version
analysis2 = ats.analyze('path/to/updated_resume.pdf', job_description)
version_id2 = ats.track_version('path/to/updated_resume.pdf', analysis2, "Version 2")

# Compare versions
comparison = ats.compare_versions(version_id, version_id2)
print(f"Score improved by {comparison['scores']['overall_ats_score']['difference']}%")
```

#### Resume Comparison

```python
from resume_ats import compare_resumes, compare_resume_to_jobs

# Compare multiple resumes against one job description
comparison = compare_resumes(
    ['resume1.pdf', 'resume2.pdf', 'resume3.pdf'], 
    job_description
)
print(f"Best resume: {comparison['rankings']['overall_ats_score'][0]}")

# Compare one resume against multiple job descriptions
job_descriptions = {
    "Software Engineer": open("se_job.txt").read(),
    "Data Scientist": open("ds_job.txt").read(),
    "Product Manager": open("pm_job.txt").read()
}
comparison = compare_resume_to_jobs('my_resume.pdf', job_descriptions)
print(f"Best job match: {comparison['rankings']['overall_ats_score'][0]}")

# Generate comparison charts
from resume_ats import EnhancedResumeATS

ats = EnhancedResumeATS()
comparison = ats.compare_multiple_resumes(['resume1.pdf', 'resume2.pdf'], job_description)
chart_paths = ats.generate_comparison_charts(comparison, 'charts_directory')
print(f"Charts saved to: {chart_paths}")
```

### Using the ResumeATS Class

```python
from resume_ats import ResumeATS

# Initialize with custom scoring weights
ats = ResumeATS(config={
    'weights': {
        'keyword_match': 0.5,
        'format_score': 0.2,
        'section_coverage': 0.2,
        'readability': 0.1
    }
})

# Analyze resume
analysis = ats.analyze('path/to/resume.pdf', job_description)

# Get optimization suggestions
optimization = ats.optimize('path/to/resume.pdf', job_description)
```

### Command Line Interface

The package also provides a command-line interface:

```bash
# Basic analysis
resume-ats path/to/resume.pdf

# Analyze against a job description
resume-ats path/to/resume.pdf --job job_description.txt

# Get optimization suggestions
resume-ats path/to/resume.pdf --job job_description.txt --optimize

# Save results to file
resume-ats path/to/resume.pdf --job job_description.txt --output results.json

# Set logging level
resume-ats path/to/resume.pdf --log-level DEBUG
```

### Supported File Formats

- PDF (.pdf)
- Microsoft Word (.docx, .doc)

## Advanced Configuration

The package supports various configuration options:

```python
config = {
    # Scoring weights
    'weights': {
        'keyword_match': 0.4,
        'format_score': 0.2,
        'section_coverage': 0.3,
        'readability': 0.1
    },
    
    # Anonymization settings
    'anonymize_settings': {
        'name': True,
        'contact_info': True,
        'education_institutions': False,
        'company_names': False,
        'dates': False,
        'addresses': True,
        'links': True,
        'age': True,
        'gender_clues': True
    },
    
    # Version tracking
    'version_storage_dir': '/path/to/storage',
    'auto_track_versions': True
}

ats = EnhancedResumeATS(config)
```

## Development

Clone the repository and install development dependencies:

```bash
git clone https://github.com/yourusername/resume-ats-plugin.git
cd resume-ats-plugin
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
