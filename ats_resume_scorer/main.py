# ats_resume_scorer/main.py
"""
Enhanced Main ATS Resume Scorer Module with LLM Integration and Multiple Recommendation Levels
"""

import argparse
import json
import sys
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Literal, List

from .parsers.resume_parser import ResumeParser, ResumeData
from .parsers.jd_parser import JobDescriptionParser, JobDescription
from .scoring.scoring_engine import ATSScoringEngine, ScoringWeights
from .utils.report_generator import ReportGenerator, LLMConfig, RecommendationLevel

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ATSResumeScorer:
    """Enhanced ATS Resume Scorer class with LLM integration and flexible recommendation levels"""

    def __init__(
        self,
        weights: Optional[ScoringWeights] = None,
        skills_db_path: Optional[str] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        """
        Initialize the ATS Resume Scorer

        Args:
            weights: Custom scoring weights (optional)
            skills_db_path: Path to custom skills database (optional)
            llm_config: Configuration for LLM integration (optional)
        """
        self.weights = weights or ScoringWeights()
        self.resume_parser = ResumeParser(skills_db_path)
        self.jd_parser = JobDescriptionParser()
        self.scoring_engine = ATSScoringEngine(self.weights)
        
        # Initialize report generator with LLM config
        self.llm_config = llm_config or self._load_llm_config_from_env()
        self.report_generator = ReportGenerator(self.llm_config)

        logger.info("ATS Resume Scorer initialized successfully")
        if self.llm_config.enabled:
            logger.info(f"LLM integration enabled with provider: {self.llm_config.provider}")

    def _load_llm_config_from_env(self) -> LLMConfig:
        """Load LLM configuration from environment variables"""
        enabled = os.getenv("ATS_LLM_ENABLED", "false").lower() == "true"
        provider = os.getenv("ATS_LLM_PROVIDER", "openai")
        
        # For local models, API key is not required
        api_key = os.getenv("ATS_LLM_API_KEY")
        if provider == "local":
            api_key = api_key or "local_model"  # Set default for local models
        
        return LLMConfig(
            enabled=enabled,
            provider=provider,
            model=os.getenv("ATS_LLM_MODEL", "gpt-3.5-turbo"),
            api_key=api_key,
            endpoint=os.getenv("ATS_LLM_ENDPOINT"),
            max_tokens=int(os.getenv("ATS_LLM_MAX_TOKENS", "500")),
            temperature=float(os.getenv("ATS_LLM_TEMPERATURE", "0.7")),
        )

    def score_resume(
        self, 
        resume_path: str, 
        job_description_text: str,
        recommendation_level: RecommendationLevel = "normal"
    ) -> Dict[str, Any]:
        """
        Score a resume against a job description

        Args:
            resume_path: Path to the resume file
            job_description_text: Job description text
            recommendation_level: Level of detail for recommendations ("concise", "normal", "detailed")

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

            # Step 4: Generate comprehensive report with specified recommendation level
            logger.info(f"Generating comprehensive report (level: {recommendation_level})")
            report = self.report_generator.generate_comprehensive_report(
                resume_data, job_description, scoring_results, recommendation_level
            )

            logger.info(
                f"Scoring completed. Overall score: {report['overall_score']}/100"
            )
            return report

        except Exception as e:
            logger.error(f"Error during scoring process: {str(e)}")
            raise

    def score_resume_from_files(
        self, 
        resume_path: str, 
        jd_path: str,
        recommendation_level: RecommendationLevel = "normal"
    ) -> Dict[str, Any]:
        """
        Score a resume against a job description from files

        Args:
            resume_path: Path to the resume file
            jd_path: Path to the job description file
            recommendation_level: Level of detail for recommendations

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

        return self.score_resume(resume_path, job_description_text, recommendation_level)

    def generate_text_report(
        self, 
        report: Dict[str, Any],
        level: Optional[RecommendationLevel] = None
    ) -> str:
        """Generate a human-readable text report"""
        level = level or report.get("recommendation_level", "normal")
        return self.report_generator.generate_summary_report(report, level)

    def save_report(
        self, 
        report: Dict[str, Any], 
        output_path: str, 
        format: str = "json"
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

    def configure_llm(
        self, 
        provider: str = "openai", 
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        enabled: bool = True
    ) -> None:
        """
        Configure LLM integration

        Args:
            provider: LLM provider ("openai", "anthropic", "local")
            model: Model name
            api_key: API key for the provider
            enabled: Whether to enable LLM integration
        """
        self.llm_config = LLMConfig(
            enabled=enabled,
            provider=provider,
            model=model,
            api_key=api_key or os.getenv("ATS_LLM_API_KEY"),
        )
        
        # Reinitialize report generator with new config
        self.report_generator = ReportGenerator(self.llm_config)
        
        logger.info(f"LLM configuration updated: {provider}/{model} ({'enabled' if enabled else 'disabled'})")

    def batch_score_resumes(
        self,
        resume_paths: List[str],
        job_description_text: str,
        recommendation_level: RecommendationLevel = "concise",
        max_workers: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Score multiple resumes in batch

        Args:
            resume_paths: List of resume file paths
            job_description_text: Job description text
            recommendation_level: Level of recommendations (usually "concise" for batch)
            max_workers: Maximum number of parallel workers

        Returns:
            List of scoring results
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        
        def score_single_resume(resume_path):
            try:
                result = self.score_resume(resume_path, job_description_text, recommendation_level)
                return {
                    "file_path": resume_path,
                    "file_name": Path(resume_path).name,
                    "success": True,
                    "result": result
                }
            except Exception as e:
                return {
                    "file_path": resume_path,
                    "file_name": Path(resume_path).name,
                    "success": False,
                    "error": str(e)
                }
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {executor.submit(score_single_resume, path): path for path in resume_paths}
            
            for future in as_completed(future_to_path):
                result = future.result()
                results.append(result)
                
                if result["success"]:
                    logger.info(f"✅ Scored {result['file_name']}: {result['result']['overall_score']:.1f}/100")
                else:
                    logger.error(f"❌ Failed {result['file_name']}: {result['error']}")
        
        # Sort by score (highest first)
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        successful_results.sort(key=lambda x: x["result"]["overall_score"], reverse=True)
        
        return successful_results + failed_results


def load_custom_weights(weights_path: str) -> ScoringWeights:
    """Load custom weights from JSON file"""
    try:
        with open(weights_path, "r") as f:
            weights_data = json.load(f)
        return ScoringWeights(**weights_data)
    except Exception as e:
        logger.error(f"Error loading custom weights: {str(e)}")
        raise


def create_sample_llm_config() -> str:
    """Create a sample LLM configuration file"""
    sample_config = {
        "enabled": False,
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "api_key": "your-api-key-here",
        "max_tokens": 500,
        "temperature": 0.7,
        "endpoint": None
    }
    
    config_path = "llm_config.json"
    with open(config_path, "w") as f:
        json.dump(sample_config, f, indent=2)
    
    return config_path


def main():
    """Enhanced command line interface for ATS Resume Scorer"""
    parser = argparse.ArgumentParser(
        description="Enhanced ATS Resume Scorer with AI-powered recommendations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  ats-score --resume resume.pdf --jd job_description.txt
  
  # With detailed recommendations
  ats-score --resume resume.pdf --jd job.txt --level detailed
  
  # Save output to file
  ats-score --resume resume.pdf --jd job.txt --output results.json --level normal
  
  # Use custom weights
  ats-score --resume resume.pdf --jd job.txt --weights custom_weights.json
  
  # Enable AI-enhanced recommendations
  export ATS_LLM_ENABLED=true
  export ATS_LLM_API_KEY=your-api-key
  ats-score --resume resume.pdf --jd job.txt --level detailed
  
  # Create sample LLM config
  ats-score --create-llm-config
        """,
    )

    parser.add_argument(
        "--resume", "-r", help="Path to resume file (.pdf, .docx, .txt)"
    )
    parser.add_argument(
        "--jd", "-j", help="Path to job description file"
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
    parser.add_argument(
        "--level", 
        "-l",
        choices=["concise", "normal", "detailed"],
        default="normal",
        help="Recommendation detail level (default: normal)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--create-llm-config", 
        action="store_true", 
        help="Create sample LLM configuration file"
    )
    parser.add_argument(
        "--enable-llm",
        action="store_true",
        help="Enable LLM-enhanced recommendations (requires API key)"
    )
    parser.add_argument(
        "--llm-provider",
        choices=["openai", "anthropic", "gemini", "local"],
        default="openai",
        help="LLM provider (default: openai)"
    )
    parser.add_argument(
        "--llm-model",
        default="gpt-3.5-turbo",
        help="LLM model name (default: gpt-3.5-turbo)"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle special commands
    if args.create_llm_config:
        config_path = create_sample_llm_config()
        print(f"✅ Sample LLM configuration created: {config_path}")
        print("Edit the file with your API key and settings, then set ATS_LLM_ENABLED=true")
        return

    # Validate required arguments
    if not args.resume or not args.jd:
        parser.print_help()
        print("\nError: Both --resume and --jd arguments are required")
        sys.exit(1)

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

        # Configure LLM if requested
        llm_config = None
        if args.enable_llm:
            api_key = os.getenv("ATS_LLM_API_KEY")
            # For local models, API key is not required
            if args.llm_provider == "local":
                api_key = api_key or "local_model"  # Set default for local models
                endpoint = os.getenv("ATS_LLM_ENDPOINT")
                if not endpoint:
                    print("Warning: Local model requires ATS_LLM_ENDPOINT to be set")
                else:
                    llm_config = LLMConfig(
                        enabled=True,
                        provider=args.llm_provider,
                        model=args.llm_model,
                        api_key=api_key,
                        endpoint=endpoint
                    )
                    print(f"✨ Local AI model enabled ({args.llm_model} at {endpoint})")
            elif not api_key:
                print("Warning: LLM enabled but no API key found. Set ATS_LLM_API_KEY environment variable.")
                print("Proceeding with standard recommendations...")
            else:
                llm_config = LLMConfig(
                    enabled=True,
                    provider=args.llm_provider,
                    model=args.llm_model,
                    api_key=api_key,
                    endpoint=os.getenv("ATS_LLM_ENDPOINT")
                )
                print(f"✨ AI-enhanced recommendations enabled ({args.llm_provider}/{args.llm_model})")

        # Initialize scorer
        scorer = ATSResumeScorer(
            weights=weights, 
            skills_db_path=args.skills_db,
            llm_config=llm_config
        )

        # Score resume
        print(f"📄 Analyzing resume: {resume_path}")
        print(f"📋 Against job description: {jd_path}")
        print(f"🎯 Recommendation level: {args.level}")
        print("-" * 60)

        result = scorer.score_resume_from_files(
            str(resume_path), 
            str(jd_path),
            args.level
        )

        # Display results
        print(
            f"🎯 ATS Score: {result['overall_score']:.1f}/100 (Grade: {result['grade']})"
        )
        print(f"🤖 ATS Compatibility: {result['ats_compatibility']['status']}")
        if result.get('llm_enhanced'):
            print("✨ AI-Enhanced Recommendations")
        print()

        print("📊 Detailed Breakdown:")
        for category, score in result["detailed_breakdown"].items():
            category_name = category.replace("_", " ").title()
            # Add visual indicators
            if score >= 80:
                indicator = "🟢"
            elif score >= 60:
                indicator = "🟡"
            else:
                indicator = "🔴"
            print(f"  {indicator} {category_name:<25}: {score:>5.1f}/100")

        print(f"\n💡 Recommendations ({args.level.upper()} Level):")
        rec_count = len(result["recommendations"])
        display_count = min(3 if args.level == "concise" else 5 if args.level == "normal" else rec_count, rec_count)
        
        for i, rec in enumerate(result["recommendations"][:display_count], 1):
            print(f"  {i}. {rec}")

        if args.level == "detailed" and "detailed_recommendations" in result:
            print(f"\n📋 Detailed Action Plans:")
            for i, detailed_rec in enumerate(result["detailed_recommendations"][:3], 1):
                print(f"\n{i}. {detailed_rec['message']}")
                if detailed_rec.get("action_steps"):
                    print("   📝 Action Steps:")
                    for step in detailed_rec["action_steps"][:3]:
                        print(f"      • {step}")
                if detailed_rec.get("examples"):
                    print("   💭 Examples:")
                    for example in detailed_rec["examples"][:2]:
                        print(f"      • {example}")

        # Save to file if requested
        if args.output:
            scorer.save_report(result, args.output, args.format)
            print(f"\n📄 Detailed report saved to: {args.output}")
        
        # Show improvement potential
        improvement = result["improvement_potential"]
        print(f"\n📈 Improvement Potential:")
        print(f"  Current Score: {improvement['current_score']:.1f}/100")
        print(f"  Potential Score: {improvement['max_possible_score']:.1f}/100")
        print(f"  Possible Gain: +{improvement['total_potential_gain']:.1f} points")

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