"""
Enhanced command-line interface for Resume ATS Plugin.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional

from .core import analyze_resume, optimize_resume, main as core_main
from .enhanced import (
    analyze_and_report,
    optimize_and_report,
    anonymize_resume_file,
    compare_resumes,
    compare_resume_to_jobs
)

logger = logging.getLogger(__name__)

def enhanced_main():
    """Enhanced command-line entry point with additional features."""
    parser = argparse.ArgumentParser(description="Resume ATS analysis and optimization with enhanced features")
    
    parser.add_argument("resume", help="Path to resume file (PDF or DOCX)")
    parser.add_argument("--job", help="Path to job description file")
    parser.add_argument("--output", help="Output file for results (JSON or PDF)")
    
    # Action arguments
    action_group = parser.add_argument_group("Actions")
    action_group.add_argument("--analyze", action="store_true", help="Analyze resume (default action)")
    action_group.add_argument("--optimize", action="store_true", help="Generate optimization suggestions")
    action_group.add_argument("--anonymize", action="store_true", help="Anonymize the resume")
    action_group.add_argument("--compare", nargs="+", metavar="RESUME", help="Compare with additional resumes")
    action_group.add_argument("--multi-job-compare", nargs="+", metavar="JOB_FILE", help="Compare resume against multiple job descriptions")
    
    # Report options
    report_group = parser.add_argument_group("Report Options")
    report_group.add_argument("--pdf-report", action="store_true", help="Generate PDF report")
    report_group.add_argument("--charts-dir", help="Directory to save visualization charts")
    
    # Configuration options
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument("--config", help="Path to configuration JSON file")
    config_group.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Set the logging level")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Load config if provided
    config = None
    if args.config:
        try:
            with open(args.config, "r") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return 1
    
    # Determine output path
    output_path = args.output
    if not output_path:
        # Generate default output path based on action
        base_name = os.path.splitext(args.resume)[0]
        if args.anonymize:
            output_path = f"{base_name}_anonymized.pdf"
        elif args.pdf_report:
            output_path = f"{base_name}_report.pdf"
        else:
            output_path = f"{base_name}_analysis.json"
    
    try:
        # Load job description if provided
        job_description = None
        if args.job:
            try:
                with open(args.job, "r") as f:
                    job_description = f.read()
            except Exception as e:
                logger.error(f"Failed to load job description: {e}")
                return 1
        
        # Process based on action
        if args.anonymize:
            # Anonymize resume
            anonymized_path, replaced_items = anonymize_resume_file(
                args.resume, 
                output_path,
                config
            )
            
            print(f"Anonymized resume saved to: {anonymized_path}")
            print(f"Items anonymized:")
            for category, items in replaced_items.items():
                if items:
                    print(f"  - {category.capitalize()}: {len(items)} items")
            
            return 0
            
        elif args.compare:
            # Compare multiple resumes
            resume_paths = [args.resume] + args.compare
            comparison = compare_resumes(resume_paths, job_description, config)
            
            # Save comparison results
            with open(output_path, "w") as f:
                json.dump(comparison, f, indent=2)
            
            print(f"Resume comparison saved to: {output_path}")
            
            # Generate charts if requested
            if args.charts_dir:
                from .resume_comparer import ResumeComparer
                comparer = ResumeComparer(config)
                charts = comparer.generate_comparison_charts(comparison)
                
                os.makedirs(args.charts_dir, exist_ok=True)
                for name, chart_buffer in charts.items():
                    chart_path = os.path.join(args.charts_dir, f"{name}.png")
                    with open(chart_path, "wb") as f:
                        f.write(chart_buffer.getvalue())
                
                print(f"Comparison charts saved to: {args.charts_dir}")
            
            return 0
            
        elif args.multi_job_compare:
            # Compare resume to multiple job descriptions
            job_descriptions = {}
            for job_file in args.multi_job_compare:
                try:
                    job_name = os.path.splitext(os.path.basename(job_file))[0]
                    with open(job_file, "r") as f:
                        job_descriptions[job_name] = f.read()
                except Exception as e:
                    logger.error(f"Failed to load job description {job_file}: {e}")
                    return 1
            
            comparison = compare_resume_to_jobs(args.resume, job_descriptions, config)
            
            # Save comparison results
            with open(output_path, "w") as f:
                json.dump(comparison, f, indent=2)
            
            print(f"Job comparison saved to: {output_path}")
            
            # Generate charts if requested
            if args.charts_dir:
                from .resume_comparer import ResumeComparer
                comparer = ResumeComparer(config)
                charts = comparer.generate_comparison_charts(comparison)
                
                os.makedirs(args.charts_dir, exist_ok=True)
                for name, chart_buffer in charts.items():
                    chart_path = os.path.join(args.charts_dir, f"{name}.png")
                    with open(chart_path, "wb") as f:
                        f.write(chart_buffer.getvalue())
                
                print(f"Comparison charts saved to: {args.charts_dir}")
            
            return 0
            
        elif args.optimize:
            # Get optimization suggestions with PDF report if requested
            if args.pdf_report:
                result, pdf_path = optimize_and_report(
                    args.resume, 
                    job_description, 
                    output_path,
                    config
                )
                print(f"Optimization report saved to: {pdf_path}")
            else:
                # Use standard optimize
                result = optimize_resume(args.resume, job_description, config)
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2)
                print(f"Optimization results saved to: {output_path}")
            
            return 0
            
        else:  # Default: analyze
            # Analyze resume with PDF report if requested
            if args.pdf_report:
                result, pdf_path = analyze_and_report(
                    args.resume, 
                    job_description, 
                    output_path,
                    config
                )
                print(f"Analysis report saved to: {pdf_path}")
            else:
                # Use standard analyze
                result = analyze_resume(args.resume, job_description, config)
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2)
                print(f"Analysis results saved to: {output_path}")
            
            return 0
            
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(enhanced_main())
