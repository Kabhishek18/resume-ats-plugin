# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2024-12-19

### Added
- Advanced CLI with batch processing capabilities
- Resume comparison and ranking features
- Detailed analysis reports with actionable recommendations
- Web API with FastAPI for remote scoring
- Docker containerization with full microservices setup
- Parallel processing for batch resume scoring
- Custom skills database support
- Comprehensive monitoring and health checks
- Production-ready deployment configurations

### Enhanced
- Improved scoring algorithm with 7 detailed categories
- Better NLP processing for job descriptions
- Enhanced resume parsing for multiple formats (PDF, DOCX, TXT)
- More accurate keyword matching and similarity scoring
- Better error handling and logging

### Fixed
- Package entry point configuration
- Import issues with module structure
- PDF parsing reliability improvements
- Memory optimization for large batch processing

### Technical Improvements
- Complete test suite with pytest
- Code quality tools (black, flake8, mypy)
- CI/CD pipeline with GitHub Actions
- Comprehensive documentation
- Docker multi-stage builds for production

## [1.0.0] - 2024-12-18

### Added
- Initial release of ATS Resume Scorer
- Basic resume scoring functionality
- Command-line interface
- Support for PDF, DOCX, and TXT files
- Core scoring engine with configurable weights
