from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ats-resume-scorer",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive ATS Resume Scoring Plugin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ats-resume-scorer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ats-score=ats_resume_scorer.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ats_resume_scorer": ["config/*.json", "data/*.json"],
    },
)

# config/default_weights.json
{
    "keyword_match": 0.30,
    "title_match": 0.10,
    "education_match": 0.10,
    "experience_match": 0.15,
    "format_compliance": 0.15,
    "action_verbs_grammar": 0.10,
    "readability": 0.10
}

# config/skills_database.json
{
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", 
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "sql"
    ],
    "web_technologies": [
        "html", "css", "react", "angular", "vue", "svelte", "node.js", "express",
        "django", "flask", "spring boot", "laravel", "ruby on rails", "asp.net"
    ],
    "databases": [
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra",
        "oracle", "sql server", "sqlite", "dynamodb", "neo4j"
    ],
    "cloud_platforms": [
        "aws", "azure", "gcp", "heroku", "digitalocean", "linode", "cloudflare"
    ],
    "devops_tools": [
        "docker", "kubernetes", "jenkins", "gitlab ci", "github actions", 
        "terraform", "ansible", "puppet", "chef", "vagrant"
    ],
    "data_science": [
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
        "matplotlib", "seaborn", "plotly", "jupyter", "anaconda", "spyder"
    ],
    "mobile_development": [
        "react native", "flutter", "ionic", "xamarin", "android", "ios"
    ],
    "testing_frameworks": [
        "pytest", "unittest", "jest", "mocha", "selenium", "cypress", "junit"
    ],
    "project_management": [
        "agile", "scrum", "kanban", "waterfall", "jira", "confluence", "trello"
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem solving", 
        "critical thinking", "time management", "adaptability"
    ]
}

# config/action_verbs.json
{
    "achievement_verbs": [
        "achieved", "accomplished", "attained", "completed", "delivered", 
        "exceeded", "finished", "fulfilled", "obtained", "reached"
    ],
    "leadership_verbs": [
        "led", "managed", "supervised", "directed", "coordinated", "guided",
        "mentored", "coached", "facilitated", "spearheaded"
    ],
    "creation_verbs": [
        "created", "developed", "designed", "built", "established", "founded",
        "initiated", "launched", "pioneered", "introduced"
    ],
    "improvement_verbs": [
        "improved", "enhanced", "optimized", "streamlined", "upgraded",
        "modernized", "revitalized", "transformed", "revolutionized"
    ],
    "analytical_verbs": [
        "analyzed", "evaluated", "assessed", "researched", "investigated",
        "examined", "studied", "reviewed", "monitored", "measured"
    ],
    "problem_solving_verbs": [
        "solved", "resolved", "troubleshot", "debugged", "fixed", "addressed",
        "handled", "tackled", "overcome", "mitigated"
    ]
}
