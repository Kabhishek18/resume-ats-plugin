# 🐳 Docker Setup for ATS Resume Scorer

This directory contains Docker configuration for running the ATS Resume Scorer in containerized environments.

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+ 
- Docker Compose 2.0+
- 4GB+ available RAM
- 10GB+ available disk space

### 1. Basic Setup
```bash
# Clone the repository
git clone <repository-url>
cd ats-resume-scorer/Docker

# Start all services
make up

# Check status
make status
```

### 2. Access Services
- **Web API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus Metrics**: http://localhost:9090

## 📋 Available Commands

### Essential Commands
```bash
make help          # Show all available commands
make build         # Build Docker images
make up            # Start all services
make down          # Stop all services
make restart       # Restart services
make logs          # Show logs
make status        # Show service status
```

### Development Commands
```bash
make up-dev        # Start in development mode
make shell         # Open CLI container shell
make test          # Run tests in container
make dev-setup     # Complete development setup
```

### Maintenance Commands
```bash
make clean         # Clean containers and volumes
make backup-db     # Backup database
make health        # Check service health
make monitor       # Monitor resource usage
```

## 🏗️ Architecture

### Services Overview

| Service | Purpose | Port | Dependencies |
|---------|---------|------|--------------|
| `ats-scorer-api` | Main FastAPI application | 8000 | redis, postgres |
| `ats-scorer-cli` | CLI tools and batch processing | - | redis, postgres |
| `postgres` | Database for storing results | 5432 | - |
| `redis` | Caching and session storage | 6379 | - |
| `nginx` | Reverse proxy (optional) | 80, 443 | ats-scorer-api |
| `prometheus` | Metrics collection (optional) | 9090 | - |
| `grafana` | Monitoring dashboard (optional) | 3000 | prometheus |

### Network Architecture
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Nginx     │    │  FastAPI    │    │ PostgreSQL  │
│   :80       │────│    :8000    │────│    :5432    │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                   ┌─────────────┐
                   │    Redis    │
                   │    :6379    │
                   └─────────────┘
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file for custom configuration:

```bash
# Database Configuration
POSTGRES_DB=ats_scorer
POSTGRES_USER=ats_user
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://ats_user:password@postgres:5432/ats_scorer

# Redis Configuration  
REDIS_URL=redis://redis:6379/0

# Application Configuration
LOG_LEVEL=INFO
DEBUG=false
SECRET_KEY=your_secret_key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=4

# File Upload Limits
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=.pdf,.docx,.txt

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
```

### Volume Mounts

| Volume | Purpose | Host Path | Container Path |
|--------|---------|-----------|----------------|
| `data` | Input files | `../data` | `/app/data` |
| `output` | Results | `../output` | `/app/output` |
| `temp` | Temporary files | `../temp` | `/app/temp` |
| `postgres_data` | Database | Docker volume | `/var/lib/postgresql/data` |
| `redis_data` | Redis persistence | Docker volume | `/data` |

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
make test

# Run specific test file
make shell
pytest tests/test_main.py -v

# Run with coverage
pytest tests/ --cov=ats_resume_scorer --cov-report=html
```

### Integration Tests
```bash
# Test API endpoints
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/api/info

# Test file upload
curl -X POST http://localhost:8000/score-resume/ \
  -F "resume_file=@examples/sample_resume.pdf" \
  -F "job_description=Python developer position..."
```

### Load Testing
```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📊 Monitoring

### Health Checks
All services include health checks:
```bash
# Check all services
make health

# Individual service checks
docker-compose exec ats-scorer-api curl -f http://localhost:8000/health
docker-compose exec postgres pg_isready -U ats_user
docker-compose exec redis redis-cli ping
```

### Metrics Collection
Prometheus collects metrics from:
- API response times and error rates
- Database connection status
- Redis cache hit/miss rates
- System resource usage

### Grafana Dashboards
Pre-configured dashboards for:
- API Performance
- Database Metrics
- System Resources
- Business Metrics (scores, file types, etc.)

## 🚀 Deployment

### Development Deployment
```bash
make up-dev
```

### Production Deployment
```bash
# Set production environment
export ENVIRONMENT=production

# Deploy with production settings
make deploy-prod

# Verify deployment
make prod-check
```

### Scaling
```bash
# Scale API service
docker-compose up -d --scale ats-scorer-api=3

# Load balance with nginx
# (nginx.conf automatically handles multiple instances)
```

## 🔒 Security

### Production Security Checklist
- [ ] Change default passwords
- [ ] Use secrets management
- [ ] Enable SSL/TLS
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs

### SSL Configuration
```bash
# Generate SSL certificates
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/server.key -out certs/server.crt

# Update nginx configuration for HTTPS
# (See nginx-ssl.conf example)
```

## 🗄️ Database Management

### Backup and Restore
```bash
# Create backup
make backup-db

# Restore from backup
make restore-db BACKUP_FILE=backups/ats_scorer_20240101_120000.sql

# Scheduled backups (add to crontab)
0 2 * * * cd /path/to/project/Docker && make backup-db
```

### Database Migrations
```bash
# Run migrations
docker-compose exec ats-scorer-api python -c "
from ats_resume_scorer.database import run_migrations
run_migrations()
"

# Reset database
make down-volumes
make up
```

## 🐛 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
make logs-api

# Check system resources
make monitor

# Restart specific service
make restart-api
```

#### Database Connection Issues
```bash
# Check database status
make logs-db

# Verify connection
make db-shell

# Reset database
make down-volumes && make up
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Analyze logs
make logs | grep -i error

# Check disk space
df -h
```

#### File Upload Issues
```bash
# Check file permissions
ls -la data/

# Verify file size limits
docker-compose exec ats-scorer-api env | grep MAX_FILE_SIZE

# Check temporary space
df -h /tmp
```

### Debug Mode
```bash
# Start with debug logging
LOG_LEVEL=DEBUG make up

# Access debug shell
make shell-api
python -c "from ats_resume_scorer.main import ATSResumeScorer; scorer = ATSResumeScorer()"
```

## 📚 Additional Resources

### Documentation Links
- [Docker Best Practices](https://docs.docker.com/develop/best-practices/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [PostgreSQL Docker Guide](https://hub.docker.com/_/postgres)
- [Redis Docker Guide](https://hub.docker.com/_/redis)
- [Nginx Configuration](https://nginx.org/en/docs/)

### Example Usage

#### Scoring a Single Resume
```bash
# Copy resume to data directory
cp /path/to/resume.pdf data/

# Score using CLI
make shell
ats-score --resume data/resume.pdf --jd data/job_description.txt

# Score using API
curl -X POST http://localhost:8000/score-resume/ \
  -F "resume_file=@data/resume.pdf" \
  -F "job_description=$(cat data/job_description.txt)"
```

#### Batch Processing
```bash
# Prepare multiple resumes
mkdir -p data/batch_resumes
cp /path/to/resumes/*.pdf data/batch_resumes/

# Run batch processing
make shell
python cli_advanced.py batch \
  --resume-dir data/batch_resumes \
  --jd data/job_description.txt \
  --output output/batch_results.csv \
  --parallel --workers 4
```

#### Custom Scoring Weights
```bash
# Create custom weights file
cat > data/custom_weights.json << EOF
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

# Use custom weights
ats-score --resume data/resume.pdf --jd data/job_description.txt --weights data/custom_weights.json
```

### Performance Tuning

#### Memory Optimization
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  ats-scorer-api:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
    environment:
      - PYTHONMALLOC=malloc
```

#### CPU Optimization
```bash
# Set CPU limits
docker-compose up -d --scale ats-scorer-api=2

# Monitor CPU usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

#### Database Optimization
```sql
-- Connect to database
-- Run via: make db-shell

-- Analyze table statistics
ANALYZE scoring_results;

-- Check query performance
EXPLAIN ANALYZE SELECT * FROM scoring_results WHERE overall_score > 80;

-- Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_scoring_results_score ON scoring_results(overall_score);
```

### Backup Strategy

#### Automated Backups
```bash
# Create backup script
cat > backup_script.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/ats_scorer"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U ats_user ats_scorer | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup volumes
docker run --rm -v ats_postgres_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/volumes_$DATE.tar.gz -C /data .

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup_script.sh

# Add to crontab
echo "0 2 * * * /path/to/backup_script.sh" | crontab -
```

#### Disaster Recovery
```bash
# Full restore procedure
make down-volumes

# Restore volumes
docker run --rm -v ats_postgres_data:/data -v /backups:/backup alpine tar xzf /backup/volumes_latest.tar.gz -C /data

# Start services
make up

# Restore database
zcat /backups/db_latest.sql.gz | docker-compose exec -T postgres psql -U ats_user ats_scorer
```

### Security Hardening

#### Production Security Settings
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  ats-scorer-api:
    environment:
      - DEBUG=false
      - LOG_LEVEL=WARNING
      - SECURE_HEADERS=true
    networks:
      - internal
    
  postgres:
    environment:
      - POSTGRES_HOST_AUTH_METHOD=md5
    volumes:
      - ./postgres.conf:/etc/postgresql/postgresql.conf
    networks:
      - internal
      
networks:
  internal:
    driver: bridge
    internal: true
```

#### SSL Certificate Setup
```bash
# Using Let's Encrypt
docker run --rm -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot certonly --standalone \
  -d your-domain.com --email your-email@domain.com --agree-tos

# Update nginx configuration
cp nginx-ssl.conf nginx.conf
make restart nginx
```

### Monitoring and Alerting

#### Custom Metrics
```python
# Add to web_api.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('ats_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('ats_request_duration_seconds', 'Request latency')

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_LATENCY.observe(time.time() - start_time)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### Alerting Rules
```yaml
# alerts.yml
groups:
  - name: ats_scorer_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(ats_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "Database is down"
```

### Integration Examples

#### CI/CD Pipeline
```yaml
# .github/workflows/docker.yml
name: Docker Build and Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd Docker
          make build
          make test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          cd Docker
          make deploy-prod
```

#### Kubernetes Deployment
```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ats-scorer-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ats-scorer-api
  template:
    metadata:
      labels:
        app: ats-scorer-api
    spec:
      containers:
      - name: ats-scorer-api
        image: ats-scorer:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ats-secrets
              key: database-url
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes
4. Test with Docker: `make test`
5. Submit pull request

### Adding New Services
1. Update `docker-compose.yml`
2. Add health checks
3. Update Makefile commands
4. Document in README
5. Add monitoring/metrics

### Best Practices
- Use multi-stage builds for smaller images
- Pin dependency versions
- Add comprehensive health checks
- Follow security best practices
- Document all configuration options

## 📞 Support

### Getting Help
- **Issues**: Create GitHub issue with logs and reproduction steps
- **Documentation**: Check main README.md and code comments
- **Community**: Join discussions in GitHub Discussions

### Logs and Debugging
```bash
# Collect debug information
make logs > debug_logs.txt
make status >> debug_logs.txt
docker system info >> debug_logs.txt
docker-compose config >> debug_logs.txt
```

### Performance Issues
```bash
# System resource check
free -h
df -h
docker system df

# Container resource usage
docker stats --no-stream

# Database performance
make db-shell
SELECT * FROM pg_stat_activity;
```

---

**📋 Quick Reference Card**

| Task | Command |
|------|---------|
| Start everything | `make up` |
| Stop everything | `make down` |
| View logs | `make logs` |
| Run tests | `make test` |
| Open shell | `make shell` |
| Check health | `make health` |
| Backup database | `make backup-db` |
| Clean up | `make clean` |
| Show help | `make help` |

---

*For more detailed information, see the main project README.md*