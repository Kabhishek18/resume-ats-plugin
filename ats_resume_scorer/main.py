# ats_resume_scorer/main.py
"""
Main ATS Resume Scorer Module - Orchestrates the complete scoring process
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .parsers.resume_parser import ResumeParser, ResumeData
from .parsers.jd_parser import JobDescriptionParser, JobDescription
from .scoring.scoring_engine import ATSScoringEngine, ScoringWeights
from .utils.report_generator import ReportGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ATSResumeScorer:
    """Main ATS Resume Scorer class that orchestrates the entire process"""

    def __init__(
        self,
        weights: Optional[ScoringWeights] = None,
        skills_db_path: Optional[str] = None,
    ):
        """
        Initialize the ATS Resume Scorer

        Args:
            weights: Custom scoring weights (optional)
            skills_db_path: Path to custom skills database (optional)
        """
        self.weights = weights or ScoringWeights()
        self.resume_parser = ResumeParser(skills_db_path)
        self.jd_parser = JobDescriptionParser()
        self.scoring_engine = ATSScoringEngine(self.weights)
        self.report_generator = ReportGenerator()

        logger.info("ATS Resume Scorer initialized successfully")

    def score_resume(
        self, resume_path: str, job_description_text: str
    ) -> Dict[str, Any]:
        """
        Score a resume against a job description

        Args:
            resume_path: Path to the resume file
            job_description_text: Job description text

        Returns:
            Comprehensive scoring report dictionary
        """
        try:
            # Step 1: Parse resume
            logger.info(f"Parsing resume: {resume_path}")
            resume_data = self.resume_parser.parse_resume(resume_path)

            # Step 2: Parse job description
            logger.info("Parsing job description")
            job_description = self.jd_parser.parse_job_description(job_description_text)

            # Step 3: Calculate scores
            logger.info("Calculating ATS scores")
            scoring_results = self.scoring_engine.calculate_overall_score(
                resume_data, job_description
            )

            # Step 4: Generate comprehensive report
            logger.info("Generating comprehensive report")
            report = self.report_generator.generate_comprehensive_report(
                resume_data, job_description, scoring_results
            )

            logger.info(
                f"Scoring completed. Overall score: {report['overall_score']}/100"
            )
            return report

        except Exception as e:
            logger.error(f"Error during scoring process: {str(e)}")
            raise

    def score_resume_from_files(self, resume_path: str, jd_path: str) -> Dict[str, Any]:
        """
        Score a resume against a job description from files

        Args:
            resume_path: Path to the resume file
            jd_path: Path to the job description file

        Returns:
            Comprehensive scoring report dictionary
        """
        # Read job description from file
        try:
            with open(jd_path, "r", encoding="utf-8") as f:
                job_description_text = f.read()
        except Exception as e:
            logger.error(f"Error reading job description file: {str(e)}")
            raise

        return self.score_resume(resume_path, job_description_text)

    def generate_text_report(self, report: Dict[str, Any]) -> str:
        """Generate a human-readable text report"""
        return self.report_generator.generate_summary_report(report)

    def save_report(
        self, report: Dict[str, Any], output_path: str, format: str = "json"
    ) -> None:
        """
        Save report to file

        Args:
            report: Report dictionary
            output_path: Output file path
            format: Output format ('json' or 'text')
        """
        if format.lower() == "json":
            self.report_generator.export_to_json(report, output_path)
        elif format.lower() == "text":
            self.report_generator.export_to_text(report, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'text'")

        logger.info(f"Report saved to: {output_path}")


def load_custom_weights(weights_path: str) -> ScoringWeights:
    """Load custom weights from JSON file"""
    try:
        with open(weights_path, "r") as f:
            weights_data = json.load(f)
        return ScoringWeights(**weights_data)
    except Exception as e:
        logger.error(f"Error loading custom weights: {str(e)}")
        raise


def main():
    """Command line interface for ATS Resume Scorer"""
    parser = argparse.ArgumentParser(
        description="ATS Resume Scorer - Score resumes against job descriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  ats-score --resume resume.pdf --jd job_description.txt
  
  # Save output to file
  ats-score --resume resume.pdf --jd job.txt --output results.json
  
  # Use custom weights
  ats-score --resume resume.pdf --jd job.txt --weights custom_weights.json
  
  # Text format output
  ats-score --resume resume.pdf --jd job.txt --output report.txt --format text
        """,
    )

    parser.add_argument(
        "--resume", "-r", required=True, help="Path to resume file (.pdf, .docx, .txt)"
    )
    parser.add_argument(
        "--jd", "-j", required=True, help="Path to job description file"
    )
    parser.add_argument("--output", "-o", help="Output file path (optional)")
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--weights", "-w", help="Path to custom weights JSON file")
    parser.add_argument("--skills-db", help="Path to custom skills database JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Validate input files
        resume_path = Path(args.resume)
        jd_path = Path(args.jd)

        if not resume_path.exists():
            print(f"Error: Resume file not found: {resume_path}")
            sys.exit(1)

        if not jd_path.exists():
            print(f"Error: Job description file not found: {jd_path}")
            sys.exit(1)

        # Load custom weights if provided
        weights = None
        if args.weights:
            weights = load_custom_weights(args.weights)
            print(f"Using custom weights from: {args.weights}")

        # Initialize scorer
        scorer = ATSResumeScorer(weights=weights, skills_db_path=args.skills_db)

        # Score resume
        print(f"Scoring resume: {resume_path}")
        print(f"Against job description: {jd_path}")
        print("-" * 50)

        result = scorer.score_resume_from_files(str(resume_path), str(jd_path))

        # Display results
        print(
            f"ATS Score: {result['overall_score']:.1f}/100 (Grade: {result['grade']})"
        )
        print(f"ATS Compatibility: {result['ats_compatibility']['status']}")
        print()

        print("Detailed Breakdown:")
        for category, score in result["detailed_breakdown"].items():
            category_name = category.replace("_", " ").title()
            print(f"  {category_name:<25}: {score:>5.1f}/100")

        print(f"\nTop Recommendations:")
        for i, rec in enumerate(result["recommendations"][:3], 1):
            print(f"  {i}. {rec}")

        # Save to file if requested
        if args.output:
            scorer.save_report(result, args.output, args.format)
            print(f"\nDetailed report saved to: {args.output}")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
