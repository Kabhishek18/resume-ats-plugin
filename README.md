# Resume ATS Plugin

A Python plugin to analyze and optimize resumes for Applicant Tracking Systems (ATS).

## Features

- **Resume Analysis**: Evaluate how well your resume will perform with ATS systems
- **Keyword Optimization**: Match your resume against job descriptions to identify missing keywords
- **Format Checking**: Verify that your resume follows recommended formatting guidelines
- **Section Analysis**: Identify missing or weak sections in your resume
- **Optimization Suggestions**: Get actionable tips to improve your resume's ATS score

## Installation

You can install the package via pip:
```python
pip install resume-ats-plugin
```
## Usage

### As a Python Library

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
#### The package also provides a command-line interface:

```python 
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

PDF (.pdf)
Microsoft Word (.docx, .doc)

### Development
Clone the repository
Install development dependencies:
```python 
pip install -e ".[dev]"
```

Run tests:
```python 
pytest
```

### License
This project is licensed under the MIT License - see the LICENSE file for details.


### MIT License
Copyright (c) 2025 Kumar Abhishek
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.



THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.