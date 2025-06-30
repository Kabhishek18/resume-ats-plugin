# 🚀 Complete ATS Resume Scorer Command Reference

## 🖥️ **Basic CLI Commands**

### Single Resume Scoring

```bash
# Basic usage
ats-score --resume resume.pdf --jd job_description.txt

# Save to file
ats-score --resume resume.pdf --jd job.txt --output results.json

# Text format output
ats-score --resume resume.pdf --jd job.txt --output report.txt --format text

# Custom weights
ats-score --resume resume.pdf --jd job.txt --weights custom_weights.json

# Verbose output
ats-score --resume resume.pdf --jd job.txt --verbose

# Custom skills database
ats-score --resume resume.pdf --jd job.txt --skills-db custom_skills.json
```

### Python Module Usage (if ats-score not working)

```bash
# Direct module execution
python -m ats_resume_scorer.main --resume resume.pdf --jd job.txt
python -m ats_resume_scorer.main --help

# Python API
python -c "
from ats_resume_scorer import ATSResumeScorer
scorer = ATSResumeScorer()
result = scorer.score_resume('resume.pdf', 'job description text')
print(f'Score: {result[\"overall_score\"]}/100')
"
```

---

## 🔧 **Advanced CLI Commands**

### Single Resume Analysis

```bash
# Advanced single resume scoring
python cli_advanced.py single --resume resume.pdf --jd job.txt

# With all options
python cli_advanced.py single \
  --resume resume.pdf \
  --jd job.txt \
  --weights custom_weights.json \
  --skills-db custom_skills.json \
  --output detailed_report.json \
  --format json \
  --verbose
```

### Batch Processing

```bash
# Basic batch processing
python cli_advanced.py batch --resume-dir ./resumes --jd job.txt

# Parallel processing
python cli_advanced.py batch \
  --resume-dir ./resumes \
  --jd job.txt \
  --parallel \
  --workers 4 \
  --output batch_results.csv

# Batch with custom weights
python cli_advanced.py batch \
  --resume-dir ./resumes \
  --jd job.txt \
  --weights custom_weights.json \
  --output results.json \
  --verbose
```

### Resume Comparison

```bash
# Compare specific resumes
python cli_advanced.py compare \
  --resumes resume1.pdf resume2.pdf resume3.pdf \
  --jd job.txt \
  --output comparison_report.json

# Compare all PDFs in directory
python cli_advanced.py compare \
  --resumes *.pdf \
  --jd job.txt \
  --weights custom_weights.json \
  --verbose
```

### Detailed Analysis

```bash
# Comprehensive analysis
python cli_advanced.py analyze \
  --resume resume.pdf \
  --jd job.txt \
  --output detailed_analysis.json \
  --verbose

# Analysis with custom settings
python cli_advanced.py analyze \
  --resume resume.pdf \
  --jd job.txt \
  --weights custom_weights.json \
  --output analysis.json
```

---

## 🌐 **Web API Commands**

### Start Web Server

```bash
# Basic server
python web_api.py

# Custom host/port
python web_api.py --host 0.0.0.0 --port 8080

# Development mode (auto-reload)
python web_api.py --reload

# Production server
uvicorn web_api:app --host 0.0.0.0 --port 8000 --workers 4

# Background server
nohup python web_api.py > api.log 2>&1 &
```

### API Testing with curl

```bash
# Health check
curl -X GET http://localhost:8000/health

# API info
curl -X GET http://localhost:8000/api/info

# Get default weights
curl -X GET http://localhost:8000/api/default-weights

# Score resume
curl -X POST http://localhost:8000/score-resume/ \
  -F "resume_file=@resume.pdf" \
  -F "job_description=Python developer position requiring Django, SQL..."

# Score with custom weights
curl -X POST http://localhost:8000/score-resume/ \
  -F "resume_file=@resume.pdf" \
  -F "job_description=Job description..." \
  -F "keyword_weight=0.40" \
  -F "experience_weight=0.20"

# Web interface
open http://localhost:8000
```

---

## 🧪 **Testing Commands**

### Run Tests

```bash
# All tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=ats_resume_scorer --cov-report=html

# Specific test file
pytest tests/test_main.py -v

# Specific test method
pytest tests/test_main.py::TestATSResumeScorer::test_score_resume -v

# Fast tests only
pytest tests/ -v -m "not slow"

# Integration tests
pytest tests/ -v -m "integration"
```

### Code Quality

```bash
# Format code
black ats_resume_scorer tests

# Lint
flake8 ats_resume_scorer tests

# Type checking
mypy ats_resume_scorer

# Security scan
bandit -r ats_resume_scorer

# Dependency check
safety check

# All quality checks
black ats_resume_scorer tests && \
flake8 ats_resume_scorer tests && \
mypy ats_resume_scorer && \
pytest tests/ -v
```

---

## 🐳 **Docker Commands**

### Docker Setup

```bash
# Navigate to Docker directory
cd Docker

# Build images
make build

# Fast build (with cache)
make build-fast

# Start all services
make up

# Start only API
make up-api-only

# Development mode
make up-dev

# Check status
make status

# Show service URLs
make show-urls
```

### Docker Service Management

```bash
# Stop services
make down

# Stop and remove volumes
make down-volumes

# Restart all services
make restart

# Restart API only
make restart-api

# Check health
make health

# Monitor resources
make monitor
```

### Docker Logs & Debugging

```bash
# View all logs
make logs

# API logs only
make logs-api

# Database logs
make logs-db

# Follow logs in real-time
make logs -f

# Open shells
make shell          # CLI container
make shell-api      # API container
make db-shell       # PostgreSQL
make redis-shell    # Redis
```

### Docker Testing

```bash
# Run tests in Docker
make test

# Build and test
make test-build

# Score example resume
make score-example

# Batch processing example
make batch-example
```

### Docker Data Management

```bash
# Backup database
make backup-db

# Restore database
make restore-db BACKUP_FILE=backups/backup_20240101.sql

# Clean containers
make clean

# Deep clean (including images)
make clean-all

# Clean system
docker system prune -f
```

### Production Docker

```bash
# Production readiness check
make prod-check

# Deploy to production
make deploy-prod

# Update services
make update

# Scale services
docker-compose up -d --scale ats-scorer-api=3
```

---

## 📊 **Monitoring & Maintenance**

### Health Checks

```bash
# API health
curl -f http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready -U ats_user

# Redis health
docker-compose exec redis redis-cli ping

# All services health
make health
```

### Access Monitoring Tools

```bash
# Grafana dashboard
open http://localhost:3000
# Login: admin/admin123

# Prometheus metrics
open http://localhost:9090

# API documentation
open http://localhost:8000/docs

# Web interface
open http://localhost:8000
```

### Database Operations

```bash
# Connect to database
make db-shell

# Check database stats
docker-compose exec postgres psql -U ats_user -d ats_scorer -c "\l+"

# View tables
docker-compose exec postgres psql -U ats_user -d ats_scorer -c "\dt"

# Performance analysis
docker-compose exec postgres psql -U ats_user -d ats_scorer -c "
SELECT schemaname,tablename,n_tup_ins,n_tup_upd,n_tup_del 
FROM pg_stat_user_tables;
"

# Vacuum database
docker-compose exec postgres psql -U ats_user -d ats_scorer -c "VACUUM ANALYZE;"
```

---

## 🛠️ **Configuration & Customization**

### Create Custom Weights

```bash
cat > custom_weights.json << EOF
{
    "keyword_match": 0.40,
    "title_match": 0.05,
    "education_match": 0.05,
    "experience_match": 0.20,
    "format_compliance": 0.10,
    "action_verbs_grammar": 0.10,
    "readability": 0.10
}
EOF
```

### Create Custom Skills Database

```bash
cat > custom_skills.json << EOF
{
    "ai_ml": ["machine learning", "deep learning", "nlp", "computer vision"],
    "blockchain": ["blockchain", "ethereum", "solidity", "web3"],
    "data_science": ["pandas", "numpy", "scikit-learn", "tensorflow"]
}
EOF
```

### Environment Configuration

```bash
# Create .env file for Docker
cat > Docker/.env << EOF
POSTGRES_DB=ats_scorer
POSTGRES_USER=ats_user
POSTGRES_PASSWORD=secure_password
LOG_LEVEL=INFO
DEBUG=false
MAX_FILE_SIZE=10485760
EOF
```

---

## 🚀 **Complete Workflow Examples**

### Quick Start Workflow

```bash
# 1. Setup
pip install -r requirements.txt && python -m spacy download en_core_web_sm && pip install -e .

# 2. Test
echo "John Doe, Software Engineer, Python, Django" > sample_resume.txt
echo "Python developer with Django experience" > sample_jd.txt
ats-score --resume sample_resume.txt --jd sample_jd.txt

# 3. Web interface
python web_api.py &
open http://localhost:8000
```

### Development Workflow

```bash
# 1. Setup development environment
cd Docker && make dev-setup

# 2. Run tests
make test

# 3. Start development server
make up-dev

# 4. Monitor logs
make logs -f
```

### Production Deployment

```bash
# 1. Pre-deployment checks
cd Docker && make prod-check

# 2. Deploy
make build && make deploy-prod

# 3. Verify
make health && make show-urls

# 4. Monitor
make monitor
```

### Batch Processing Workflow

```bash
# 1. Prepare data
mkdir -p data/resumes && cp /path/to/resumes/*.pdf data/resumes/

# 2. Process
python cli_advanced.py batch \
  --resume-dir data/resumes \
  --jd data/job_description.txt \
  --parallel --workers 4 \
  --output results/batch_results.csv

# 3. Analyze results
python -c "
import pandas as pd
df = pd.read_csv('results/batch_results.csv')
print(f'Average: {df[\"score\"].mean():.1f}')
print(f'Top 3: {df.head(3)[\"filename\"].tolist()}')
"
```

---

## 📚 **Quick Reference Summary**

| **Purpose** | **Command** |
|-------------|-------------|
| **Score single resume** | `ats-score --resume resume.pdf --jd job.txt` |
| **Batch processing** | `python cli_advanced.py batch --resume-dir ./resumes --jd job.txt --parallel` |
| **Start web API** | `python web_api.py` |
| **Start Docker services** | `cd Docker && make up` |
| **Run tests** | `pytest tests/ -v` |
| **View Docker logs** | `make logs` |
| **Health check** | `make health` |
| **Clean Docker** | `make clean` |
| **Compare resumes** | `python cli_advanced.py compare --resumes *.pdf --jd job.txt` |
| **Detailed analysis** | `python cli_advanced.py analyze --resume resume.pdf --jd job.txt` |

---

## 🆘 **Troubleshooting Commands**

```bash
# If ats-score not found
python -m ats_resume_scorer.main --help
alias ats-score="python -m ats_resume_scorer.main"

# Check installation
pip show ats-resume-scorer
python -c "from ats_resume_scorer import ATSResumeScorer; print('OK')"

# Fix Docker issues
make down && make clean && make build && make up

# Check Docker resources
docker stats --no-stream
df -h
free -h

# Reset everything
make clean-all && make build && make up
```

**🎯 Start with basic commands, progress to CLI advanced features, then use Docker for production!**