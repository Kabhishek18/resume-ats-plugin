# cli_advanced.py (Fixed with proper imports)
"""
Advanced CLI interface with batch processing and enhanced features
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import csv
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import from our package
from ats_resume_scorer.main import ATSResumeScorer
from ats_resume_scorer.scoring.scoring_engine import ScoringWeights

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def score_single_resume(args):
    """Score a single resume"""
    try:
        # Load custom weights if provided
        weights = None
        if args.weights:
            weights = load_custom_weights(args.weights)
            print(f"✓ Loaded custom weights from: {args.weights}")
        
        # Read job description
        with open(args.jd, 'r', encoding='utf-8') as f:
            jd_text = f.read()
        
        # Initialize scorer
        scorer = ATSResumeScorer(weights=weights, skills_db_path=args.skills_db)
        
        # Score resume
        print(f"🔍 Analyzing resume: {args.resume}")
        print(f"📋 Against job description: {args.jd}")
        print("-" * 60)
        
        result = scorer.score_resume(args.resume, jd_text)
        
        # Output results
        if args.output:
            if args.format == 'json':
                scorer.save_report(result, args.output, 'json')
            else:
                scorer.save_report(result, args.output, 'text')
            print(f"📄 Results saved to: {args.output}")
        elif args.format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print_formatted_result(result)
            
    except Exception as e:
        logger.error(f"Error scoring resume: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def score_batch_resumes(args):
    """Score multiple resumes with optional parallel processing"""
    resume_dir = Path(args.resume_dir)
    
    if not resume_dir.exists():
        print(f"❌ Error: Directory {args.resume_dir} does not exist")
        sys.exit(1)
    
    # Find all resume files
    resume_files = []
    extensions = ['*.pdf', '*.docx', '*.txt']
    for ext in extensions:
        resume_files.extend(resume_dir.glob(ext))
    
    if not resume_files:
        print(f"❌ No resume files found in {args.resume_dir}")
        print(f"   Supported formats: {', '.join(extensions)}")
        sys.exit(1)
    
    print(f"📁 Found {len(resume_files)} resume files")
    
    # Read job description
    with open(args.jd, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    # Load custom weights if provided
    weights = None
    if args.weights:
        weights = load_custom_weights(args.weights)
        print(f"✓ Using custom weights from: {args.weights}")
    
    # Process resumes
    print(f"🚀 Starting batch processing...")
    start_time = time.time()
    
    if args.parallel:
        results = process_resumes_parallel(resume_files, jd_text, weights, args)
    else:
        results = process_resumes_sequential(resume_files, jd_text, weights, args)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Output results
    print(f"\n✅ Batch processing completed in {processing_time:.2f} seconds")
    print(f"📊 Processed {len(results)} resumes")
    
    if args.output:
        output_path = Path(args.output)
        if output_path.suffix == '.csv':
            save_batch_results_csv(results, args.output)
        else:
            save_batch_results_json(results, args.output)
        print(f"📄 Batch results saved to: {args.output}")
    else:
        print_batch_results(results)

def process_resumes_sequential(resume_files, jd_text, weights, args):
    """Process resumes one by one"""
    results = []
    scorer = ATSResumeScorer(weights=weights, skills_db_path=args.skills_db)
    
    for i, resume_file in enumerate(resume_files, 1):
        print(f"📄 Processing {i}/{len(resume_files)}: {resume_file.name}")
        try:
            result = scorer.score_resume(str(resume_file), jd_text)
            results.append({
                'filename': resume_file.name,
                'score': result['overall_score'],
                'grade': result['grade'],
                'ats_status': result['ats_compatibility']['status'],
                'result': result
            })
        except Exception as e:
            logger.error(f"Error processing {resume_file.name}: {e}")
            results.append({
                'filename': resume_file.name,
                'error': str(e)
            })
    
    return results

def process_resumes_parallel(resume_files, jd_text, weights, args):
    """Process resumes in parallel using thread pool"""
    results = []
    max_workers = min(args.workers, len(resume_files))
    
    def score_resume_worker(resume_file):
        """Worker function for parallel processing"""
        scorer = ATSResumeScorer(weights=weights, skills_db_path=args.skills_db)
        try:
            result = scorer.score_resume(str(resume_file), jd_text)
            return {
                'filename': resume_file.name,
                'score': result['overall_score'],
                'grade': result['grade'],
                'ats_status': result['ats_compatibility']['status'],
                'result': result
            }
        except Exception as e:
            logger.error(f"Error processing {resume_file.name}: {e}")
            return {
                'filename': resume_file.name,
                'error': str(e)
            }
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(score_resume_worker, resume_file): resume_file 
                         for resume_file in resume_files}
        
        completed = 0
        for future in as_completed(future_to_file):
            completed += 1
            result = future.result()
            results.append(result)
            
            if 'error' not in result:
                print(f"✅ {completed}/{len(resume_files)}: {result['filename']} - Score: {result['score']:.1f}")
            else:
                print(f"❌ {completed}/{len(resume_files)}: {result['filename']} - Error")
    
    return results

def print_formatted_result(result: Dict[str, Any]):
    """Print result in a formatted way"""
    print("=" * 60)
    print(f"🎯 ATS RESUME SCORE: {result['overall_score']:.1f}/100 (Grade: {result['grade']})")
    print(f"🤖 ATS Compatibility: {result['ats_compatibility']['status']}")
    print("=" * 60)
    
    print("\n📊 DETAILED BREAKDOWN:")
    for category, score in result['detailed_breakdown'].items():
        category_name = category.replace('_', ' ').title()
        # Add emoji indicators
        if score >= 80:
            indicator = "🟢"
        elif score >= 60:
            indicator = "🟡"
        else:
            indicator = "🔴"
        print(f"  {indicator} {category_name:<25}: {score:>5.1f}/100")
    
    print(f"\n📋 RESUME SUMMARY:")
    summary = result['resume_summary']
    print(f"  📧 Contact Info:     {'✅' if summary['has_contact_info'] else '❌'}")
    print(f"  🎯 Summary/Objective: {'✅' if summary['has_summary'] else '❌'}")
    print(f"  🛠️  Skills Listed:     {summary['skills_count']}")
    print(f"  💼 Experience Count:  {summary['experience_count']}")
    print(f"  🎓 Education Count:   {summary['education_count']}")
    print(f"  🏆 Certifications:    {summary['certifications_count']}")
    
    print(f"\n🎯 JOB MATCH ANALYSIS:")
    match = result['job_match_analysis']
    print(f"  ✅ Required Skills:   {match['required_skills_matched']}/{match['required_skills_total']} ({match['required_match_percentage']:.1f}%)")
    print(f"  ⭐ Preferred Skills:  {match['preferred_skills_matched']}/{match['preferred_skills_total']} ({match['preferred_match_percentage']:.1f}%)")
    
    if match['missing_required_skills']:
        print(f"  ❌ Missing Required:  {', '.join(match['missing_required_skills'][:5])}")
        if len(match['missing_required_skills']) > 5:
            print(f"     + {len(match['missing_required_skills']) - 5} more...")
    
    print(f"\n💡 TOP RECOMMENDATIONS:")
    for i, rec in enumerate(result['recommendations'][:5], 1):
        print(f"  {i}. {rec}")
    
    if 'improvement_potential' in result:
        improvement = result['improvement_potential']
        print(f"\n📈 IMPROVEMENT POTENTIAL:")
        print(f"  Current Score:    {improvement['current_score']:.1f}/100")
        print(f"  Potential Score:  {improvement['max_possible_score']:.1f}/100")
        print(f"  Possible Gain:    +{improvement['total_potential_gain']:.1f} points")

def print_batch_results(results: List[Dict[str, Any]]):
    """Print batch results summary"""
    print("\n" + "=" * 80)
    print("📊 BATCH RESUME SCORING RESULTS")
    print("=" * 80)
    
    # Summary statistics
    successful_results = [r for r in results if 'error' not in r]
    error_count = len(results) - len(successful_results)
    
    if successful_results:
        scores = [r['score'] for r in successful_results]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        print(f"\n📈 SUMMARY STATISTICS:")
        print(f"  Total Resumes:    {len(results)}")
        print(f"  Successful:       {len(successful_results)}")
        print(f"  Errors:           {error_count}")
        print(f"  Average Score:    {avg_score:.1f}/100")
        print(f"  Highest Score:    {max_score:.1f}/100")
        print(f"  Lowest Score:     {min_score:.1f}/100")
    
    print(f"\n📋 DETAILED RESULTS:")
    print(f"{'Rank':<6} {'Filename':<35} {'Score':<8} {'Grade':<6} {'ATS Status':<12} {'Top Issue'}")
    print("-" * 95)
    
    for i, result in enumerate(results, 1):
        if 'error' in result:
            print(f"{i:<6} {result['filename']:<35} {'ERROR':<8} {'-':<6} {'-':<12} {result['error'][:30]}")
        else:
            # Get top recommendation
            top_rec = result['result']['recommendations'][0][:35] if result['result']['recommendations'] else 'None'
            print(f"{i:<6} {result['filename']:<35} {result['score']:<8.1f} {result['grade']:<6} {result['ats_status']:<12} {top_rec}")

def save_batch_results_csv(results: List[Dict[str, Any]], output_path: str):
    """Save batch results to CSV"""
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'rank', 'filename', 'score', 'grade', 'ats_status', 
            'keyword_match', 'title_match', 'education_match', 'experience_match',
            'format_compliance', 'action_verbs_grammar', 'readability',
            'top_recommendation', 'required_skills_match_pct', 'error'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for i, result in enumerate(results, 1):
            if 'error' not in result:
                detailed = result['result']['detailed_breakdown']
                job_match = result['result']['job_match_analysis']
                top_rec = result['result']['recommendations'][0] if result['result']['recommendations'] else ''
                
                writer.writerow({
                    'rank': i,
                    'filename': result['filename'],
                    'score': result['score'],
                    'grade': result['grade'],
                    'ats_status': result['ats_status'],
                    'keyword_match': detailed['keyword_match'],
                    'title_match': detailed['title_match'],
                    'education_match': detailed['education_match'],
                    'experience_match': detailed['experience_match'],
                    'format_compliance': detailed['format_compliance'],
                    'action_verbs_grammar': detailed['action_verbs_grammar'],
                    'readability': detailed['readability'],
                    'top_recommendation': top_rec,
                    'required_skills_match_pct': job_match['required_match_percentage'],
                    'error': ''
                })
            else:
                writer.writerow({
                    'rank': i,
                    'filename': result['filename'],
                    'error': result['error']
                })

def save_batch_results_json(results: List[Dict[str, Any]], output_path: str):
    """Save batch results to JSON"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def load_custom_weights(weights_path: str) -> ScoringWeights:
    """Load custom weights from JSON file"""
    try:
        with open(weights_path, 'r') as f:
            weights_data = json.load(f)
        return ScoringWeights(**weights_data)
    except Exception as e:
        logger.error(f"Error loading custom weights: {str(e)}")
        raise

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
  
  # Parallel processing
  python cli_advanced.py batch --resume-dir ./resumes --jd job.txt --parallel --workers 4
  
  # Use custom weights
  python cli_advanced.py single --resume resume.pdf --jd job.txt --weights custom_weights.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single resume scoring
    single_parser = subparsers.add_parser('single', help='Score a single resume')
    single_parser.add_argument('--resume', '-r', required=True, help='Path to resume file')
    single_parser.add_argument('--jd', '-j', required=True, help='Path to job description file')
    single_parser.add_argument('--output', '-o', help='Output file path')
    single_parser.add_argument('--weights', '-w', help='Custom weights JSON file')
    single_parser.add_argument('--skills-db', help='Custom skills database JSON file')
    single_parser.add_argument('--format', '-f', choices=['json', 'text'], default='text', help='Output format')
    single_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Batch resume scoring
    batch_parser = subparsers.add_parser('batch', help='Score multiple resumes')
    batch_parser.add_argument('--resume-dir', '-d', required=True, help='Directory containing resume files')
    batch_parser.add_argument('--jd', '-j', required=True, help='Path to job description file')
    batch_parser.add_argument('--output', '-o', help='Output file path (.json or .csv)')
    batch_parser.add_argument('--weights', '-w', help='Custom weights JSON file')
    batch_parser.add_argument('--skills-db', help='Custom skills database JSON file')
    batch_parser.add_argument('--parallel', '-p', action='store_true', help='Enable parallel processing')
    batch_parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers (default: 4)')
    batch_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Compare resumes command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple resumes against job description')
    compare_parser.add_argument('--resumes', '-r', nargs='+', required=True, help='Resume file paths to compare')
    compare_parser.add_argument('--jd', '-j', required=True, help='Path to job description file')
    compare_parser.add_argument('--weights', '-w', help='Custom weights JSON file')
    compare_parser.add_argument('--output', '-o', help='Output comparison report')
    compare_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Analyze command for detailed analysis
    analyze_parser = subparsers.add_parser('analyze', help='Detailed analysis of resume vs job description')
    analyze_parser.add_argument('--resume', '-r', required=True, help='Path to resume file')
    analyze_parser.add_argument('--jd', '-j', required=True, help='Path to job description file')
    analyze_parser.add_argument('--output', '-o', help='Output detailed analysis report')
    analyze_parser.add_argument('--weights', '-w', help='Custom weights JSON file')
    analyze_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Set logging level
    if getattr(args, 'verbose', False):
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.command == 'single':
            score_single_resume(args)
        elif args.command == 'batch':
            score_batch_resumes(args)
        elif args.command == 'compare':
            compare_resumes(args)
        elif args.command == 'analyze':
            analyze_resume_detailed(args)
            
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()
        sys.exit(1)

def compare_resumes(args):
    """Compare multiple resumes against the same job description"""
    print(f"🔍 Comparing {len(args.resumes)} resumes against job description")
    
    # Read job description
    with open(args.jd, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    # Load custom weights if provided
    weights = None
    if args.weights:
        weights = load_custom_weights(args.weights)
        print(f"✓ Using custom weights from: {args.weights}")
    
    # Score all resumes
    scorer = ATSResumeScorer(weights=weights)
    results = []
    
    for i, resume_path in enumerate(args.resumes, 1):
        resume_file = Path(resume_path)
        if not resume_file.exists():
            print(f"⚠️  Warning: Resume file not found: {resume_path}")
            continue
            
        print(f"📄 Processing {i}/{len(args.resumes)}: {resume_file.name}")
        try:
            result = scorer.score_resume(str(resume_file), jd_text)
            results.append({
                'filename': resume_file.name,
                'filepath': str(resume_file),
                'score': result['overall_score'],
                'grade': result['grade'],
                'result': result
            })
        except Exception as e:
            logger.error(f"Error processing {resume_file.name}: {e}")
            results.append({
                'filename': resume_file.name,
                'filepath': str(resume_file),
                'error': str(e)
            })
    
    # Sort by score
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Display comparison
    print_comparison_results(results)
    
    # Save if requested
    if args.output:
        comparison_report = generate_comparison_report(results, jd_text)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(comparison_report, f, indent=2, ensure_ascii=False)
        print(f"📄 Comparison report saved to: {args.output}")

def analyze_resume_detailed(args):
    """Perform detailed analysis of resume vs job description"""
    print(f"🔬 Performing detailed analysis...")
    
    # Read job description
    with open(args.jd, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    # Load custom weights if provided
    weights = None
    if args.weights:
        weights = load_custom_weights(args.weights)
    
    # Score resume
    scorer = ATSResumeScorer(weights=weights)
    result = scorer.score_resume(args.resume, jd_text)
    
    # Generate detailed analysis
    analysis = generate_detailed_analysis(result, args.resume, jd_text)
    
    # Display analysis
    print_detailed_analysis(analysis)
    
    # Save if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"📄 Detailed analysis saved to: {args.output}")

def print_comparison_results(results):
    """Print comparison results in a ranked format"""
    print("\n" + "🏆" * 20 + " RESUME COMPARISON RESULTS " + "🏆" * 20)
    
    successful_results = [r for r in results if 'error' not in r]
    
    if not successful_results:
        print("❌ No resumes were successfully processed")
        return
    
    print(f"\n📊 RANKING ({len(successful_results)} resumes):")
    print(f"{'Rank':<6} {'Resume':<40} {'Score':<8} {'Grade':<6} {'Status'}")
    print("-" * 70)
    
    for i, result in enumerate(successful_results, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
        filename = result['filename']
        if len(filename) > 35:
            filename = filename[:32] + "..."
        
        status = "✅ Strong" if result['score'] >= 80 else "⚠️  Fair" if result['score'] >= 60 else "❌ Weak"
        
        print(f"{medal:<6} {filename:<40} {result['score']:<8.1f} {result['grade']:<6} {status}")
    
    # Show top performer details
    if successful_results:
        top_performer = successful_results[0]
        print(f"\n🏆 TOP PERFORMER: {top_performer['filename']}")
        print(f"   Score: {top_performer['score']:.1f}/100")
        print(f"   Strengths: {', '.join(get_top_strengths(top_performer['result']))}")

def generate_comparison_report(results, jd_text):
    """Generate a comprehensive comparison report"""
    successful_results = [r for r in results if 'error' not in r]
    
    if not successful_results:
        return {"error": "No resumes successfully processed"}
    
    # Calculate statistics
    scores = [r['score'] for r in successful_results]
    
    return {
        "comparison_summary": {
            "total_resumes": len(results),
            "successfully_processed": len(successful_results),
            "average_score": sum(scores) / len(scores),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "score_range": max(scores) - min(scores)
        },
        "rankings": [
            {
                "rank": i,
                "filename": r['filename'],
                "score": r['score'],
                "grade": r['grade'],
                "strengths": get_top_strengths(r['result']),
                "weaknesses": get_top_weaknesses(r['result'])
            }
            for i, r in enumerate(successful_results, 1)
        ],
        "category_analysis": analyze_category_performance(successful_results),
        "job_description_summary": jd_text[:500] + "..." if len(jd_text) > 500 else jd_text
    }

def generate_detailed_analysis(result, resume_path, jd_text):
    """Generate detailed analysis report"""
    return {
        "resume_file": resume_path,
        "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_assessment": {
            "score": result['overall_score'],
            "grade": result['grade'],
            "ats_compatibility": result['ats_compatibility'],
            "improvement_potential": result.get('improvement_potential', {})
        },
        "detailed_breakdown": result['detailed_breakdown'],
        "strengths_analysis": get_detailed_strengths(result),
        "weaknesses_analysis": get_detailed_weaknesses(result),
        "skill_gap_analysis": analyze_skill_gaps(result),
        "recommendations_prioritized": prioritize_recommendations(result['recommendations']),
        "job_match_deep_dive": result['job_match_analysis'],
        "resume_statistics": result['resume_summary']
    }

def get_top_strengths(result):
    """Get top 3 scoring categories"""
    scores = result['detailed_breakdown']
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [cat.replace('_', ' ').title() for cat, score in sorted_scores[:3] if score >= 70]

def get_top_weaknesses(result):
    """Get bottom 3 scoring categories"""
    scores = result['detailed_breakdown']
    sorted_scores = sorted(scores.items(), key=lambda x: x[1])
    return [cat.replace('_', ' ').title() for cat, score in sorted_scores[:3] if score < 70]

def get_detailed_strengths(result):
    """Get detailed strength analysis"""
    scores = result['detailed_breakdown']
    strengths = []
    
    for category, score in scores.items():
        if score >= 80:
            strengths.append({
                "category": category.replace('_', ' ').title(),
                "score": score,
                "level": "Excellent" if score >= 90 else "Good"
            })
    
    return strengths

def get_detailed_weaknesses(result):
    """Get detailed weakness analysis"""
    scores = result['detailed_breakdown']
    weaknesses = []
    
    for category, score in scores.items():
        if score < 70:
            weaknesses.append({
                "category": category.replace('_', ' ').title(),
                "score": score,
                "level": "Critical" if score < 50 else "Needs Improvement"
            })
    
    return weaknesses

def analyze_skill_gaps(result):
    """Analyze skill gaps in detail"""
    job_match = result['job_match_analysis']
    
    return {
        "critical_missing_skills": job_match['missing_required_skills'][:5],
        "nice_to_have_missing": job_match['missing_preferred_skills'][:5],
        "skills_coverage": {
            "required": f"{job_match['required_match_percentage']:.1f}%",
            "preferred": f"{job_match['preferred_match_percentage']:.1f}%"
        },
        "recommendations": [
            f"Add {skill}" for skill in job_match['missing_required_skills'][:3]
        ]
    }

def prioritize_recommendations(recommendations):
    """Prioritize recommendations by impact"""
    priority_keywords = {
        "missing skills": 1,
        "contact": 1,
        "email": 1,
        "action verbs": 2,
        "quantify": 2,
        "format": 2,
        "structure": 3,
        "readability": 3
    }
    
    prioritized = []
    for rec in recommendations:
        priority = 3  # Default priority
        for keyword, p in priority_keywords.items():
            if keyword.lower() in rec.lower():
                priority = min(priority, p)
                break
        
        prioritized.append({
            "recommendation": rec,
            "priority": priority,
            "category": "Critical" if priority == 1 else "Important" if priority == 2 else "Nice to Have"
        })
    
    return sorted(prioritized, key=lambda x: x['priority'])

def analyze_category_performance(results):
    """Analyze performance across all categories"""
    categories = ['keyword_match', 'title_match', 'education_match', 
                 'experience_match', 'format_compliance', 'action_verbs_grammar', 'readability']
    
    category_stats = {}
    
    for category in categories:
        scores = [r['result']['detailed_breakdown'][category] for r in results]
        category_stats[category] = {
            "average": sum(scores) / len(scores),
            "highest": max(scores),
            "lowest": min(scores),
            "above_80": len([s for s in scores if s >= 80]),
            "below_60": len([s for s in scores if s < 60])
        }
    
    return category_stats

def print_detailed_analysis(analysis):
    """Print detailed analysis in a formatted way"""
    print("\n" + "🔬" * 20 + " DETAILED ANALYSIS REPORT " + "🔬" * 20)
    
    print(f"\n📄 RESUME: {Path(analysis['resume_file']).name}")
    print(f"📅 ANALYZED: {analysis['analysis_timestamp']}")
    
    assessment = analysis['overall_assessment']
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print(f"   Score: {assessment['score']:.1f}/100 (Grade: {assessment['grade']})")
    print(f"   ATS Status: {assessment['ats_compatibility']['status']}")
    
    if analysis['strengths_analysis']:
        print(f"\n💪 STRENGTHS:")
        for strength in analysis['strengths_analysis']:
            print(f"   ✅ {strength['category']}: {strength['score']:.1f}/100 ({strength['level']})")
    
    if analysis['weaknesses_analysis']:
        print(f"\n⚠️  AREAS FOR IMPROVEMENT:")
        for weakness in analysis['weaknesses_analysis']:
            print(f"   ❌ {weakness['category']}: {weakness['score']:.1f}/100 ({weakness['level']})")
    
    skill_gaps = analysis['skill_gap_analysis']
    print(f"\n🎯 SKILL GAP ANALYSIS:")
    print(f"   Required Skills Coverage: {skill_gaps['skills_coverage']['required']}")
    print(f"   Preferred Skills Coverage: {skill_gaps['skills_coverage']['preferred']}")
    
    if skill_gaps['critical_missing_skills']:
        print(f"   Critical Missing: {', '.join(skill_gaps['critical_missing_skills'])}")
    
    print(f"\n🚀 PRIORITIZED RECOMMENDATIONS:")
    for rec in analysis['recommendations_prioritized'][:5]:
        priority_emoji = "🔴" if rec['priority'] == 1 else "🟡" if rec['priority'] == 2 else "🟢"
        print(f"   {priority_emoji} [{rec['category']}] {rec['recommendation']}")

if __name__ == "__main__":
    main()