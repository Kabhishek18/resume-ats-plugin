# Docker/Dockerfile (Fixed with multi-stage build)
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Production stage
FROM python:3.9-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app directory and user
WORKDIR /app
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Copy application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/data /app/output /app/temp
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from ats_resume_scorer.main import ATSResumeScorer; ATSResumeScorer()" || exit 1

# Expose ports
EXPOSE 8000

# Default command (can be overridden)
CMD ["python", "-m", "ats_resume_scorer.main", "--help"]

# Alternative commands (uncomment as needed):
# For web API:
# CMD ["python", "web_api.py"]
# For interactive shell:
# CMD ["/bin/bash"]