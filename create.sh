#!/bin/bash

# Root directory
mkdir -p resume-ats-plugin/.github/workflows
mkdir -p resume-ats-plugin/src/resume_ats
mkdir -p resume-ats-plugin/tests

# Files in root directory
touch resume-ats-plugin/.gitignore
touch resume-ats-plugin/LICENSE
touch resume-ats-plugin/pyproject.toml
touch resume-ats-plugin/README.md
touch resume-ats-plugin/setup.py

# GitHub Actions workflow
touch resume-ats-plugin/.github/workflows/publish.yml

# Python package files
touch resume-ats-plugin/src/resume_ats/__init__.py
touch resume-ats-plugin/src/resume_ats/core.py
touch resume-ats-plugin/src/resume_ats/utils.py

# Test files
touch resume-ats-plugin/tests/__init__.py
touch resume-ats-plugin/tests/test_resume_ats.py

echo "Project structure created successfully."
