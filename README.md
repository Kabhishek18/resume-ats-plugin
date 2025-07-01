# 🚀 Enhanced ATS Resume Scorer with AI Integration

A comprehensive Python-based plugin to score resumes against ATS standards with **AI-powered recommendations** and multiple detail levels.

## ✨ New Features (v2.0)

- **🤖 AI-Enhanced Recommendations**: Get intelligent, context-aware suggestions powered by LLMs
- **📊 Multiple Recommendation Levels**: Choose between Concise, Normal, and Detailed analysis
- **🔧 LLM Integration**: Support for OpenAI, Anthropic, and local models
- **⚡ Enhanced Performance**: Improved scoring algorithms and batch processing
- **🌐 Upgraded Web Interface**: Modern, responsive UI with AI features

---

## 🎯 Recommendation Levels

### 📝 **Concise** 
- **Best for**: Quick reviews, batch processing
- **Output**: 3-5 high-priority recommendations
- **Focus**: Critical issues only

### 📋 **Normal** (Default)
- **Best for**: Regular analysis, balanced detail
- **Output**: 5-8 recommendations with action steps
- **Focus**: Important improvements with guidance

### 🔬 **Detailed**
- **Best for**: Deep analysis, comprehensive improvement
- **Output**: 8+ recommendations with examples, explanations, and step-by-step guides
- **Focus**: Complete optimization roadmap

---

## 🚀 Quick Start

### 1. Installation

```bash
# Install the package
pip install ats-resume-scorer

# Install spaCy model
python -m spacy download en_core_web_sm

# Optional: Install LLM dependencies
pip install openai anthropic  # for AI features
```

### 2. Basic Usage

```bash
# Simple scoring
ats-score --resume resume.pdf --jd job_description.txt

# Choose recommendation level
ats-score --resume resume.pdf --jd job.txt --level detailed

# Enable AI recommendations (requires API key)
export ATS_LLM_ENABLED=true
export ATS_LLM_API_KEY=your-api-key
ats-score --resume resume.pdf --jd job.txt --level detailed
```

---

## 🤖 AI Integration Setup

### OpenAI Setup
```bash
export ATS_LLM_ENABLED=true
export ATS_LLM_PROVIDER=openai
export ATS_LLM_API_KEY=sk-your-openai-key
export ATS_LLM_MODEL=gpt-3.5-turbo  # or gpt-4
```

### Anthropic Claude Setup
```bash
export ATS_LLM_ENABLED=true
export ATS_LLM_PROVIDER=anthropic
export ATS_LLM_API_KEY=your-anthropic-key
export ATS_LLM_MODEL=claude-3-sonnet
```

### Google Gemini Setup
```bash
export ATS_LLM_ENABLED=true
export ATS_LLM_PROVIDER=gemini
export ATS_LLM_API_KEY=your-gemini-api-key
export ATS_LLM_MODEL=gemini-pro  # or gemini-1.5-pro
```

### Local Model Setup (Ollama)
```bash
export ATS_LLM_ENABLED=true
export ATS_LLM_PROVIDER=local
export ATS_LLM_ENDPOINT=http://localhost:11434/api/generate
export ATS_LLM_MODEL=llama3.2:latest
```

---

## 📚 Complete Usage Guide

### 🔧 **Command Line Interface**

#### Basic Commands
```bash
# Standard analysis
ats-score --resume resume.pdf --jd job.txt

# Concise recommendations (great for quick review)
ats-score --resume resume.pdf --jd job.txt --level concise

# Normal recommendations (balanced detail)
ats-score --resume resume.pdf --jd job.txt --level normal

# Detailed analysis (comprehensive guidance)
ats-score --resume resume.pdf --jd job.txt --level detailed

# Save results to file
ats-score --resume resume.pdf --jd job.txt --output results.json
ats-score --resume resume.pdf --jd job.txt --output report.txt --format text
```

#### AI-Enhanced Commands
```bash
# Enable AI recommendations
ats-score --resume resume.pdf --jd job.txt --level detailed --enable-llm

# Use specific AI provider
ats-score --resume resume.pdf --jd job.txt --enable-llm --llm-provider anthropic
ats-score --resume resume.pdf --jd job.txt --enable-llm --llm-provider gemini

# Custom AI model
ats-score --resume resume.pdf --jd job.txt --enable-llm --llm-model gpt-4
ats-score --resume resume.pdf --jd job.txt --enable-llm --llm-provider gemini --llm-model gemini-1.5-pro
```

#### Advanced Features
```bash
# Custom scoring weights
ats-score --resume resume.pdf --jd job.txt --weights custom_weights.json

# Custom skills database
ats-score --resume resume.pdf --jd job.txt --skills-db my_skills.json

# Verbose output with debugging
ats-score --resume resume.pdf --jd job.txt --verbose
```

### 🎛️ **Advanced CLI Tool**

#### Single Resume Analysis
```bash
# Basic analysis
python cli_advanced.py single --resume resume.pdf --jd job.txt

# AI-enhanced detailed analysis
python cli_advanced.py single \
  --resume resume.pdf \
  --jd job.txt \
  --level detailed \
  --enable-llm \
  --llm-provider gemini

# Custom configuration
python cli_advanced.py single \
  --resume resume.pdf \
  --jd job.txt \
  --weights custom_weights.json \
  --enable-llm \
  --llm-model gpt-4 \
  --output detailed_report.json
```

#### Batch Processing
```bash
# Process multiple resumes
python cli_advanced.py batch \
  --resume-dir ./resumes \
  --jd job_description.txt \
  --level concise \
  --output batch_results.csv

# Parallel processing with AI
python cli_advanced.py batch \
  --resume-dir ./resumes \
  --jd job.txt \
  --parallel \
  --workers 4 \
  --enable-llm \
  --level normal
```

#### Resume Comparison
```bash
# Compare multiple resumes
python cli_advanced.py compare \
  --resumes resume1.pdf resume2.pdf resume3.pdf \
  --jd job.txt \
  --level normal \
  --enable-llm

# Compare with detailed AI analysis
python cli_advanced.py compare \
  --resumes *.pdf \
  --jd job.txt \
  --level detailed \
  --enable-llm \
  --output comparison_report.json
```

#### Deep Analysis
```bash
# Comprehensive analysis
python cli_advanced.py analyze \
  --resume resume.pdf \
  --jd job.txt \
  --level detailed \
  --enable-llm \
  --output deep_analysis.json
```

### 🌐 **Web Interface**

#### Start Web Server
```bash
# Basic server
python web_api.py

# With AI features enabled
export ATS_LLM_ENABLED=true
export ATS_LLM_API_KEY=your-key
python web_api.py --enable-llm

# Custom configuration
python web_api.py --host 0.0.0.0 --port 8080 --reload
```

#### API Usage Examples

**Score Single Resume:**
```bash
curl -X POST http://localhost:8000/score-resume/ \
  -F "resume_file=@resume.pdf" \
  -F "job_description=Python developer position..." \
  -F "recommendation_level=detailed" \
  -F "enable_llm=true"
```

**Batch Processing:**
```bash
curl -X POST http://localhost:8000/batch-score/ \
  -F "resume_files=@resume1.pdf" \
  -F "resume_files=@resume2.pdf" \
  -F "job_description=Job description text..." \
  -F "recommendation_level=normal"
```

**Check LLM Status:**
```bash
curl http://localhost:8000/api/llm-status
```

---

## 📝 Configuration Files

### Custom Weights Example
```json
{
    "keyword_match": 0.40,
    "title_match": 0.05,
    "education_match": 0.05,
    "experience_match": 0.20,
    "format_compliance": 0.10,
    "action_verbs_grammar": 0.10,
    "readability": 0.10
}
```

### LLM Configuration Example
```json
{
    "enabled": true,
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "your-api-key",
    "max_tokens": 500,
    "temperature": 0.7
}
```

### Custom Skills Database Example
```json
{
    "ai_ml": [
        "machine learning", "deep learning", "neural networks",
        "tensorflow", "pytorch", "scikit-learn", "nlp"
    ],
    "blockchain": [
        "blockchain", "ethereum", "smart contracts", "solidity", "web3"
    ],
    "cloud_native": [
        "kubernetes", "docker", "microservices", "serverless", "istio"
    ]
}
```

---

## 🎯 Example Outputs

### Concise Level Output
```
🎯 ATS Score: 78.5/100 (Grade: B)
🤖 ATS Compatibility: Good

💡 Recommendations (CONCISE Level):
1. Add these critical missing skills: Docker, Kubernetes, AWS
2. Include a professional email address
3. Quantify your achievements with numbers and percentages
```

### Normal Level Output
```
🎯 ATS Score: 78.5/100 (Grade: B)
🤖 ATS Compatibility: Good
✨ AI-Enhanced Recommendations

📊 Detailed Breakdown:
🟢 Keyword Match: 85.2/100
🟡 Format Compliance: 72.3/100
🔴 Experience Match: 45.1/100

💡 Recommendations (NORMAL Level):
1. Add these critical missing skills: Docker, Kubernetes, AWS
   📝 Action Steps:
   • Add 'Docker' to your skills section
   • Include containerization experience in job descriptions

2. Quantify your achievements with numbers and percentages
   📝 Action Steps:
   • Replace vague statements with specific metrics
   • Include percentage improvements and team sizes
```

### Detailed Level Output
```
🎯 ATS Score: 78.5/100 (Grade: B)
🤖 ATS Compatibility: Good
✨ AI-Enhanced Recommendations

📋 Detailed Action Plans:

1. Add these critical missing skills: Docker, Kubernetes, AWS
   📊 Priority: High | Impact: Could increase keyword match by 15-25 points
   📝 Explanation: These containerization and cloud skills are explicitly required
   🎯 Action Steps:
      • Add 'Docker, Kubernetes, AWS' to your technical skills section
      • Include containerization experience in job descriptions
      • Mention specific AWS services you've used (EC2, S3, RDS)
      • Add any container orchestration projects
   💭 Examples:
      • "Skills: Python, JavaScript, Docker, Kubernetes, AWS"
      • "Deployed applications using Docker containers on AWS ECS"
```

---

## 🐳 Docker Usage

### Quick Start with Docker
```bash
# Build and run
cd Docker
make up

# Access services
open http://localhost:8000  # Web interface
open http://localhost:8000/docs  # API docs

# Enable AI features
echo "ATS_LLM_ENABLED=true" >> .env
echo "ATS_LLM_API_KEY=your-key" >> .env
make restart
```

### Docker Commands
```bash
# Start all services
make up

# Enable AI with environment variables
ATS_LLM_ENABLED=true ATS_LLM_API_KEY=your-key make up

# Batch processing
make shell
python cli_advanced.py batch --resume-dir /app/data --jd /app/data/job.txt --enable-llm

# View logs
make logs-api
```

---

## 🎨 Python API Examples

### Basic Usage
```python
from ats_resume_scorer import ATSResumeScorer

# Simple scoring
scorer = ATSResumeScorer()
result = scorer.score_resume('resume.pdf', 'job description text')
print(f"Score: {result['overall_score']}/100")
```

### AI-Enhanced Scoring
```python
from ats_resume_scorer import ATSResumeScorer
from ats_resume_scorer.utils.report_generator import LLMConfig

# Configure Gemini AI-enhanced scoring
llm_config = LLMConfig(
    enabled=True,
    provider="gemini",
    model="gemini-pro",
    api_key="your-gemini-api-key"
)

scorer = ATSResumeScorer(llm_config=llm_config)
result = scorer.score_resume('resume.pdf', 'job description', 'detailed')

print(f"AI Enhanced: {result['llm_enhanced']}")
print(f"Score: {result['overall_score']}/100")
for rec in result['detailed_recommendations'][:3]:
    print(f"- {rec['message']}")
    if rec.get('action_steps'):
        for step in rec['action_steps'][:2]:
            print(f"  • {step}")
```

### Batch Processing
```python
from ats_resume_scorer import ATSResumeScorer

scorer = ATSResumeScorer()
resume_files = ['resume1.pdf', 'resume2.pdf', 'resume3.pdf']
job_description = "Python developer position..."

results = scorer.batch_score_resumes(
    resume_files, 
    job_description, 
    recommendation_level='concise',
    max_workers=4
)

for result in results:
    if result['success']:
        print(f"{result['file_name']}: {result['result']['overall_score']:.1f}/100")
    else:
        print(f"{result['file_name']}: Error - {result['error']}")
```

### Custom Configuration
```python
from ats_resume_scorer import ATSResumeScorer, ScoringWeights
from ats_resume_scorer.utils.report_generator import LLMConfig

# Custom weights (emphasize skills matching)
weights = ScoringWeights(
    keyword_match=0.40,
    experience_match=0.25,
    format_compliance=0.15,
    title_match=0.05,
    education_match=0.05,
    action_verbs_grammar=0.05,
    readability=0.05
)

# LLM configuration
llm_config = LLMConfig(
    enabled=True,
    provider="gemini",
    model="gemini-1.5-pro",
    api_key="your-gemini-api-key",
    temperature=0.5
)

scorer = ATSResumeScorer(weights=weights, llm_config=llm_config)
result = scorer.score_resume('resume.pdf', job_description, 'detailed')
```

### API Integration Example
```python
import requests
import json

# Score resume via API
files = {'resume_file': open('resume.pdf', 'rb')}
data = {
    'job_description': 'Python developer position...',
    'recommendation_level': 'detailed',
    'enable_llm': 'true',
    'llm_provider': 'gemini'
}

response = requests.post('http://localhost:8000/score-resume/', files=files, data=data)
result = response.json()

if result['status'] == 'success':
    print(f"Score: {result['result']['overall_score']}/100")
    print(f"AI Enhanced: {result['llm_enhanced']}")
    
    # Display recommendations by level
    level = result['recommendation_level']
    if level == 'detailed':
        for rec in result['result']['detailed_recommendations'][:3]:
            print(f"\n{rec['message']}")
            if rec.get('action_steps'):
                for step in rec['action_steps']:
                    print(f"  • {step}")
    else:
        for i, rec in enumerate(result['result']['recommendations'][:5], 1):
            print(f"{i}. {rec}")
```

---

## 🔧 Environment Variables

```bash
# Core Settings
ATS_LLM_ENABLED=true                    # Enable/disable AI features
ATS_LLM_PROVIDER=gemini                 # AI provider (openai/anthropic/gemini/local)
ATS_LLM_MODEL=gemini-pro                # Model name
ATS_LLM_API_KEY=your-api-key            # API key for the provider

# Advanced LLM Settings
ATS_LLM_MAX_TOKENS=500                  # Maximum tokens per request
ATS_LLM_TEMPERATURE=0.7                 # Temperature for generation
ATS_LLM_ENDPOINT=http://localhost:11434 # Custom endpoint for local models

# Application Settings
LOG_LEVEL=INFO                          # Logging level
DEBUG=false                             # Debug mode
MAX_FILE_SIZE=10485760                  # Max file size (10MB)
```

---

## 📊 Scoring Breakdown

### Categories Explained

| Category | Weight | Description |
|----------|--------|-------------|
| **Keyword Match** | 30% | Skills and requirement alignment |
| **Experience Match** | 15% | Relevant experience years and domain |
| **Format Compliance** | 15% | ATS-friendly formatting |
| **Action Verbs & Grammar** | 10% | Professional language usage |
| **Title Match** | 10% | Job title alignment |
| **Education Match** | 10% | Educational requirements |
| **Readability** | 10% | Structure and clarity |

### Grade Scale
- **A (90-100)**: Excellent ATS compatibility
- **B (80-89)**: Good, minor improvements needed
- **C (70-79)**: Fair, several improvements needed
- **D (60-69)**: Poor, major improvements required
- **F (0-59)**: Very poor, significant overhaul needed

---

## 🚀 Performance Tips

### For Better AI Recommendations
1. **Use Detailed Level**: Get comprehensive analysis with examples
2. **Provide Complete Job Descriptions**: More context = better recommendations
3. **Enable Verbose Mode**: Get insights into the analysis process

### For Batch Processing
1. **Use Concise Level**: Faster processing for multiple resumes
2. **Enable Parallel Processing**: Use `--parallel` for faster execution
3. **Optimize Workers**: Set `--workers` based on your system specs

### For Production Use
1. **Set API Limits**: Configure rate limiting for AI providers
2. **Monitor Usage**: Track API costs and usage patterns
3. **Cache Results**: Implement caching for repeated analyses

---

## 🔍 Troubleshooting

### Common Issues

#### AI Features Not Working
```bash
# Check API key
echo $ATS_LLM_API_KEY

# Test API connection
curl -H "Authorization: Bearer $ATS_LLM_API_KEY" \
  https://api.openai.com/v1/models

# Enable debug logging
ATS_LLM_ENABLED=true LOG_LEVEL=DEBUG ats-score --resume resume.pdf --jd job.txt
```

#### Installation Issues
```bash
# Install missing dependencies
pip install --upgrade ats-resume-scorer
python -m spacy download en_core_web_sm

# For M1 Macs
pip install --upgrade pip setuptools wheel
pip install ats-resume-scorer --no-cache-dir
```

#### File Processing Errors
```bash
# Check file format
file resume.pdf

# Test with simple text file
echo "John Doe, Software Engineer" > test_resume.txt
ats-score --resume test_resume.txt --jd job.txt

# Check file permissions
ls -la resume.pdf
```

#### Memory Issues (Large Batches)
```bash
# Reduce batch size
python cli_advanced.py batch --resume-dir ./resumes --jd job.txt --workers 2

# Use concise level
python cli_advanced.py batch --resume-dir ./resumes --jd job.txt --level concise

# Monitor memory usage
docker stats  # if using Docker
```

---

## 🆕 What's New in v2.0

### AI-Powered Recommendations
- **Context-Aware Suggestions**: AI understands your specific job requirements
- **Actionable Guidance**: Step-by-step improvement plans
- **Industry-Specific Advice**: Tailored recommendations for different roles

### Enhanced User Experience
- **Modern Web Interface**: Responsive design with real-time feedback
- **Multiple Detail Levels**: Choose the right amount of detail for your needs
- **Batch Processing**: Efficiently process multiple resumes

### Developer Features
- **Flexible LLM Integration**: Support for multiple AI providers
- **Enhanced API**: RESTful endpoints with comprehensive documentation
- **Docker Support**: Complete containerization with monitoring

---

## 🛣️ Roadmap

### Upcoming Features
- **Resume Builder Integration**: Generate optimized resumes based on job descriptions
- **Industry Templates**: Pre-configured settings for different industries
- **Advanced Analytics**: Historical tracking and improvement metrics
- **Integration APIs**: Connect with popular HR platforms

### AI Enhancements
- **Multi-Language Support**: Recommendations in multiple languages
- **Visual Analysis**: AI-powered formatting and design suggestions
- **Competitive Analysis**: Compare against industry benchmarks

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**
3. **Add your enhancements**
4. **Test thoroughly** (including AI features)
5. **Submit a pull request**

### Development Setup
```bash
# Clone and setup
git clone https://github.com/yourusername/ats-resume-scorer.git
cd ats-resume-scorer

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Test AI features (requires API key)
export ATS_LLM_API_KEY=your-test-key
pytest tests/test_llm_integration.py
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🆘 Support

### Get Help
- **📚 Documentation**: Check this README and code comments
- **🐛 Issues**: Create GitHub issue with logs and reproduction steps
- **💬 Discussions**: Join GitHub Discussions for community help

### Professional Support
For enterprise support, custom integrations, or consulting services, contact us at [your-email@domain.com].

---

## ⭐ Show Your Support

If this project helps you land your dream job, please:
- ⭐ Star the repository
- 🐛 Report issues and suggest improvements
- 🤝 Contribute code or documentation
- 📢 Share with others who might benefit

---

**🎯 Start optimizing resumes with AI today!**

```bash
pip install ats-resume-scorer
export ATS_LLM_API_KEY=your-key
ats-score --resume your_resume.pdf --jd job_description.txt --level detailed --enable-llm
```