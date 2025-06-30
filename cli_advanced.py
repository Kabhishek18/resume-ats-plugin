
# cli_advanced.py (Advanced CLI with more options)
"""
Advanced CLI interface with additional features
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import csv

from ats_resume_scorer.main import ATSResumeScorer, ScoringWeights

def score_single_resume(args):
    """Score a single resume"""
    # Load custom weights if provided
    weights = None
    if args.weights:
        with open(args.weights, 'r') as f:
            weights_data = json.load(f)
            weights = ScoringWeights(**weights_data)
    
    # Read job description
    with open(args.jd, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    # Score resume
    scorer = ATSResumeScorer(weights)
    result = scorer.score_resume(args.resume, jd_text)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    elif args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print_formatted_result(result)

def score_batch_resumes(args):
    """Score multiple resumes"""
    resume_dir = Path(args.resume_dir)
    
    if not resume_dir.exists():
        print(f"Error: Directory {args.resume_dir} does not exist")
        sys.exit(1)
    
    # Find all resume files
    resume_files = []
    for ext in ['*.pdf', '*.docx', '*.txt']:
        resume_files.extend(resume_dir.glob(ext))
    
    if not resume_files:
        print(f"No resume files found in {args.resume_dir}")
        sys.exit(1)
    
    # Read job description
    with open(args.jd, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    # Load custom weights if provided
    weights = None
    if args.weights:
        with open(args.weights, 'r') as f:
            weights_data = json.load(f)
            weights = ScoringWeights(**weights_data)
    
    # Score all resumes
    scorer = ATSResumeScorer(weights)
    results = []
    
    for resume_file in resume_files:
        print(f"Processing {resume_file.name}...")
        try:
            result = scorer.score_resume(str(resume_file), jd_text)
            results.append({
                'filename': resume_file.name,
                'score': result['overall_score'],
                'grade': result['grade'],
                'result': result
            })
        except Exception as e:
            print(f"Error processing {resume_file.name}: {e}")
            results.append({
                'filename': resume_file.name,
                'error': str(e)
            })
    
    # Sort by score
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Output results
    if args.output:
        output_path = Path(args.output)
        if output_path.suffix == '.csv':
            save_batch_results_csv(results, args.output)
        else:
            save_batch_results_json(results, args.output)
        print(f"Batch results saved to {args.output}")
    else:
        print_batch_results(results)

def print_formatted_result(result: Dict[str, Any]):
    """Print result in a formatted way"""
    print("=" * 50)
    print(f"ATS RESUME SCORE: {result['overall_score']:.1f}/100 (Grade: {result['grade']})")
    print("=" * 50)
    
    print("\nDETAILED BREAKDOWN:")
    for category, score in result['detailed_breakdown'].items():
        category_name = category.replace('_', ' ').title()
        print(f"  {category_name:20}: {score:5.1f}/100")
    
    print(f"\nRESUME SUMMARY:")
    summary = result['resume_summary']
    print(f"  Skills Found:     {summary['skills_count']}")
    print(f"  Experience Count: {summary['experience_count']}")
    print(f"  Education Count:  {summary['education_count']}")
    print(f"  Has Contact Info: {'Yes' if summary['has_contact_info'] else 'No'}")
    
    print(f"\nJOB MATCH ANALYSIS:")
    match = result['job_match_analysis']
    print(f"  Required Skills Matched:  {match['required_skills_matched']}")
    print(f"  Preferred Skills Matched: {match['preferred_skills_matched']}")
    
    if match['missing_required_skills']:
        print(f"  Missing Required Skills:  {', '.join(match['missing_required_skills'][:5])}")
    
    print(f"\nRECOMMENDATIONS:")
    for i, rec in enumerate(result['recommendations'][:5], 1):
        print(f"  {i}. {rec}")

def print_batch_results(results: List[Dict[str, Any]]):
    """Print batch results summary"""
    print("=" * 80)
    print("BATCH RESUME SCORING RESULTS")
    print("=" * 80)
    
    print(f"{'Rank':<4} {'Filename':<30} {'Score':<8} {'Grade':<6} {'Top Recommendation'}")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        if 'error' in result:
            print(f"{i:<4} {result['filename']:<30} {'ERROR':<8} {'-':<6} {result['error'][:30]}")
        else:
            top_rec = result['result']['recommendations'][0][:30] if result['result']['recommendations'] else 'None'
            print(f"{i:<4} {result['filename']:<30} {result['score']:<8.1f} {result['grade']:<6} {top_rec}")

def save_batch_results_csv(results: List[Dict[str, Any]], output_path: str):
    """Save batch results to CSV"""
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['rank', 'filename', 'score', 'grade', 'top_recommendation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for i, result in enumerate(results, 1):
            if 'error' not in result:
                top_rec = result['result']['recommendations'][0] if result['result']['recommendations'] else ''
                writer.writerow({
                    'rank': i,
                    'filename': result['filename'],
                    'score': result['score'],
                    'grade': result['grade'],
                    'top_recommendation': top_rec
                })

def save_batch_results_json(results: List[Dict[str, Any]], output_path: str):
    """Save batch results to JSON"""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Advanced CLI main function"""
    parser = argparse.ArgumentParser(
        description="Advanced ATS Resume Scoring Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Score single resume
  python cli_advanced.py single --resume resume.pdf --jd job.txt
  
  # Score multiple resumes
  python cli_advanced.py batch --resume-dir ./resumes --jd job.txt --output results.csv
  
  # Use custom weights
  python cli_advanced.py single --resume resume.pdf --jd job.txt --weights custom_weights.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single resume scoring
    single_parser = subparsers.add_parser('single', help='Score a single resume')
    single_parser.add_argument('--resume', required=True, help='Path to resume file')
    single_parser.add_argument('--jd', required=True, help='Path to job description file')
    single_parser.add_argument('--output', help='Output file path')
    single_parser.add_argument('--weights', help='Custom weights JSON file')
    single_parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    
    # Batch resume scoring
    batch_parser = subparsers.add_parser('batch', help='Score multiple resumes')
    batch_parser.add_argument('--resume-dir', required=True, help='Directory containing resume files')
    batch_parser.add_argument('--jd', required=True, help='Path to job description file')
    batch_parser.add_argument('--output', help='Output file path (.json or .csv)')
    batch_parser.add_argument('--weights', help='Custom weights JSON file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'single':
        score_single_resume(args)
    elif args.command == 'batch':
        score_batch_resumes(args)

if __name__ == "__main__":
    main()