# cli_advanced.py
"""
Enhanced Advanced CLI interface with LLM integration and multiple recommendation levels
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import csv
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import from our package
from ats_resume_scorer.main import ATSResumeScorer
from ats_resume_scorer.scoring.scoring_engine import ScoringWeights
from ats_resume_scorer.utils.report_generator import LLMConfig, RecommendationLevel

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def score_single_resume(args):
    """Score a single resume with enhanced features"""
    try:
        # Load custom weights if provided
        weights = None
        if args.weights:
            weights = load_custom_weights(args.weights)
            print(f"✓ Loaded custom weights from: {args.weights}")
        
        # Configure LLM if enabled
        llm_config = None
        if getattr(args, 'enable_llm', False):
            llm_config = configure_llm_from_args(args)
            if llm_config and llm_config.enabled:
                print(f"✨ AI-enhanced recommendations enabled ({llm_config.provider})")
        
        # Read job description
        with open(args.jd, 'r', encoding='utf-8') as f:
            jd_text = f.read()
        
        # Initialize scorer
        scorer = ATSResumeScorer(
            weights=weights, 
            skills_db_path=args.skills_db,
            llm_config=llm_config
        )
        
        # Score resume
        recommendation_level = getattr(args, 'level', 'normal')
        print(f"🔍 Analyzing resume: {args.resume}")
        print(f"📋 Against job description: {args.jd}")
        print(f"🎯 Recommendation level: {recommendation_level}")
        print("-" * 60)
        
        result = scorer.score_resume(args.resume, jd_text, recommendation_level)
        
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
            print_formatted_result(result, recommendation_level)
            
    except Exception as e:
        logger.error(f"Error scoring resume: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def score_batch_resumes(args):
    """Score multiple resumes with enhanced features"""
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
    
    # Configure LLM if enabled
    llm_config = None
    if getattr(args, 'enable_llm', False):
        llm_config = configure_llm_from_args(args)
        if llm_config and llm_config.enabled:
            print(f"✨ AI-enhanced recommendations enabled")
    
    # Load custom weights if provided
    weights = None
    if args.weights:
        weights = load_custom_weights(args.weights)
        print(f"✓ Using custom weights from: {args.weights}")
    
    # Process resumes
    recommendation_level = getattr(args, 'level', 'concise')  # Use concise for batch by default
    print(f"🚀 Starting batch processing (recommendation level: {recommendation_level})...")
    start_time = time.time()
    
    if args.parallel:
        results = process_resumes_parallel(resume_files, jd_text, weights, llm_config, recommendation_level, args)
    else:
        results = process_resumes_sequential(resume_files, jd_text, weights, llm_config, recommendation_level, args)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Sort by score (highest first)
    successful_results = [r for r in results if 'score' in r]
    failed_results = [r for r in results if 'error' in r]
    successful_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Output results
    print(f"\n✅ Batch processing completed in {processing_time:.2f} seconds")
    print(f"📊 Successfully processed {len(successful_results)} resumes")
    if failed_results:
        print(f"❌ Failed to process {len(failed_results)} resumes")
    
    if args.output:
        output_path = Path(args.output)
        if output_path.suffix == '.csv':
            save_batch_results_csv(successful_results + failed_results, args.output)
        else:
            save_batch_results_json(successful_results + failed_results, args.output)
        print(f"📄 Batch results saved to: {args.output}")
    else:
        print_batch_results(successful_results + failed_results)

def configure_llm_from_args(args) -> LLMConfig:
    """Configure LLM from command line arguments"""
    api_key = getattr(args, 'llm_api_key', None) or os.getenv("ATS_LLM_API_KEY")
    provider = getattr(args, 'llm_provider', 'openai')
    
    # For local models, API key is not required
    if provider == "local":
        api_key = api_key or "local_model"
        endpoint = getattr(args, 'llm_endpoint', None) or os.getenv("ATS_LLM_ENDPOINT")
        if not endpoint:
            print("Warning: Local model requires --llm-endpoint or ATS_LLM_ENDPOINT")
            return LLMConfig(enabled=False)
    elif not api_key:
        print("Warning: LLM enabled but no API key provided. Use --llm-api-key or set ATS_LLM_API_KEY")
        return LLMConfig(enabled=False)
    
    return LLMConfig(
        enabled=True,
        provider=provider,
        model=getattr(args, 'llm_model', 'gpt-3.5-turbo'),
        api_key=api_key,
        endpoint=getattr(args, 'llm_endpoint', None) or os.getenv("ATS_LLM_ENDPOINT"),
        max_tokens=getattr(args, 'llm_max_tokens', 500),
        temperature=getattr(args, 'llm_temperature', 0.7)
    )

def process_resumes_sequential(resume_files, jd_text, weights, llm_config, recommendation_level, args):
    """Process resumes one by one"""
    results = []
    scorer = ATSResumeScorer(
        weights=weights, 
        skills_db_path=args.skills_db,
        llm_config=llm_config
    )
    
    for i, resume_file in enumerate(resume_files, 1):
        print(f"📄 Processing {i}/{len(resume_files)}: {resume_file.name}")
        try:
            result = scorer.score_resume(str(resume_file), jd_text, recommendation_level)
            results.append({
                'filename': resume_file.name,
                'score': result['overall_score'],
                'grade': result['grade'],
                'ats_status': result['ats_compatibility']['status'],
                'llm_enhanced': result.get('llm_enhanced', False),
                'recommendation_level': recommendation_level,
                'result': result
            })
        except Exception as e:
            logger.error(f"Error processing {resume_file.name}: {e}")
            results.append({
                'filename': resume_file.name,
                'error': str(e)
            })
    
    return results

def process_resumes_parallel(resume_files, jd_text, weights, llm_config, recommendation_level, args):
    """Process resumes in parallel using thread pool"""
    results = []
    max_workers = min(args.workers, len(resume_files))
    
    def score_resume_worker(resume_file):
        """Worker function for parallel processing"""
        scorer = ATSResumeScorer(
            weights=weights, 
            skills_db_path=args.skills_db,
            llm_config=llm_config
        )
        try:
            result = scorer.score_resume(str(resume_file), jd_text, recommendation_level)
            return {
                'filename': resume_file.name,
                'score': result['overall_score'],
                'grade': result['grade'],
                'ats_status': result['ats_compatibility']['status'],
                'llm_enhanced': result.get('llm_enhanced', False),
                'recommendation_level': recommendation_level,
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
                llm_indicator = "✨" if result.get('llm_enhanced') else "📊"
                print(f"{llm_indicator} {completed}/{len(resume_files)}: {result['filename']} - Score: {result['score']:.1f}")
            else:
                print(f"❌ {completed}/{len(resume_files)}: {result['filename']} - Error")
    
    return results

def print_formatted_result(result: Dict[str, Any], level: str = "normal"):
    """Print result in a formatted way with level-specific details"""
    print("=" * 70)
    print(f"🎯 ATS RESUME SCORE: {result['overall_score']:.1f}/100 (Grade: {result['grade']})")
    print(f"🤖 ATS Compatibility: {result['ats_compatibility']['status']}")
    if result.get('llm_enhanced'):
        print("✨ AI-Enhanced Recommendations")
    print(f"📊 Recommendation Level: {result.get('recommendation_level', 'normal').title()}")
    print("=" * 70)
    
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
    
    # Display recommendations based on level
    print(f"\n💡 RECOMMENDATIONS ({level.upper()} Level):")
    rec_count = len(result["recommendations"])
    
    if level == "concise":
        display_count = min(3, rec_count)
        for i, rec in enumerate(result["recommendations"][:display_count], 1):
            print(f"  {i}. {rec}")
    
    elif level == "normal":
        display_count = min(5, rec_count)
        for i, rec in enumerate(result["recommendations"][:display_count], 1):
            print(f"  {i}. {rec}")
        
        # Show action steps if available
        if "detailed_recommendations" in result:
            print(f"\n📝 ACTION STEPS:")
            for i, detailed_rec in enumerate(result["detailed_recommendations"][:3], 1):
                if detailed_rec.get("action_steps"):
                    print(f"  {i}. {detailed_rec['message'][:50]}...")
                    for step in detailed_rec["action_steps"][:2]:
                        print(f"     • {step}")
    
    else:  # detailed
        for i, rec in enumerate(result["recommendations"][:rec_count], 1):
            print(f"  {i}. {rec}")
        
        if "detailed_recommendations" in result:
            print(f"\n📋 DETAILED ACTION PLANS:")
            for i, detailed_rec in enumerate(result["detailed_recommendations"][:5], 1):
                print(f"\n{i}. {detailed_rec['message']}")
                print(f"   📊 Category: {detailed_rec['category']} | Priority: {detailed_rec['priority']}")
                
                if detailed_rec.get("detailed_explanation"):
                    print(f"   📝 Explanation: {detailed_rec['detailed_explanation']}")
                
                if detailed_rec.get("action_steps"):
                    print("   🎯 Action Steps:")
                    for step in detailed_rec["action_steps"]:
                        print(f"      • {step}")
                
                if detailed_rec.get("examples"):
                    print("   💭 Examples:")
                    for example in detailed_rec["examples"]:
                        print(f"      • {example}")
    
    if 'improvement_potential' in result:
        improvement = result['improvement_potential']
        print(f"\n📈 IMPROVEMENT POTENTIAL:")
        print(f"  Current Score:    {improvement['current_score']:.1f}/100")
        print(f"  Potential Score:  {improvement['max_possible_score']:.1f}/100")
        print(f"  Possible Gain:    +{improvement['total_potential_gain']:.1f} points")

def print_batch_results(results: List[Dict[str, Any]]):
    """Print batch results summary with LLM indicators"""
    print("\n" + "=" * 80)
    print("📊 BATCH RESUME SCORING RESULTS")
    print("=" * 80)
    
    # Summary statistics
    successful_results = [r for r in results if 'error' not in r]
    error_count = len(results) - len(successful_results)
    llm_enhanced_count = len([r for r in successful_results if r.get('llm_enhanced', False)])
    
    if successful_results:
        scores = [r['score'] for r in successful_results]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        print(f"\n📈 SUMMARY STATISTICS:")
        print(f"  Total Resumes:    {len(results)}")
        print(f"  Successful:       {len(successful_results)}")
        print(f"  Errors:           {error_count}")
        print(f"  AI-Enhanced:      {llm_enhanced_count}")
        print(f"  Average Score:    {avg_score:.1f}/100")
        print(f"  Highest Score:    {max_score:.1f}/100")
        print(f"  Lowest Score:     {min_score:.1f}/100")
    
    print(f"\n📋 DETAILED RESULTS:")
    print(f"{'Rank':<6} {'Filename':<35} {'Score':<8} {'Grade':<6} {'ATS Status':<12} {'AI':<3} {'Top Issue'}")
    print("-" * 100)
    
    for i, result in enumerate(results, 1):
        if 'error' in result:
            print(f"{i:<6} {result['filename']:<35} {'ERROR':<8} {'-':<6} {'-':<12} {'-':<3} {result['error'][:30]}")
        else:
            # Get top recommendation
            top_rec = result['result']['recommendations'][0][:35] if result['result']['recommendations'] else 'None'
            ai_indicator = "✨" if result.get('llm_enhanced') else "-"
            print(f"{i:<6} {result['filename']:<35} {result['score']:<8.1f} {result['grade']:<6} {result['ats_status']:<12} {ai_indicator:<3} {top_rec}")

def save_batch_results_csv(results: List[Dict[str, Any]], output_path: str):
    """Save batch results to CSV with enhanced fields"""
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'rank', 'filename', 'score', 'grade', 'ats_status', 'llm_enhanced', 'recommendation_level',
            'keyword_match', 'title_match', 'education_match', 'experience_match',
            'format_compliance', 'action_verbs_grammar', 'readability',
            'top_recommendation', 'required_skills_match_pct', 'improvement_potential', 'error'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for i, result in enumerate(results, 1):
            if 'error' not in result:
                detailed = result['result']['detailed_breakdown']
                job_match = result['result']['job_match_analysis']
                top_rec = result['result']['recommendations'][0] if result['result']['recommendations'] else ''
                improvement = result['result'].get('improvement_potential', {})
                
                writer.writerow({
                    'rank': i,
                    'filename': result['filename'],
                    'score': result['score'],
                    'grade': result['grade'],
                    'ats_status': result['ats_status'],
                    'llm_enhanced': result.get('llm_enhanced', False),
                    'recommendation_level': result.get('recommendation_level', 'normal'),
                    'keyword_match': detailed['keyword_match'],
                    'title_match': detailed['title_match'],
                    'education_match': detailed['education_match'],
                    'experience_match': detailed['experience_match'],
                    'format_compliance': detailed['format_compliance'],
                    'action_verbs_grammar': detailed['action_verbs_grammar'],
                    'readability': detailed['readability'],
                    'top_recommendation': top_rec,
                    'required_skills_match_pct': job_match['required_match_percentage'],
                    'improvement_potential': improvement.get('total_potential_gain', 0),
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

def compare_resumes(args):
    """Compare multiple resumes against the same job description"""
    print(f"🔍 Comparing {len(args.resumes)} resumes against job description")
    
    # Read job description
    with open(args.jd, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    # Configure LLM if enabled
    llm_config = None
    if getattr(args, 'enable_llm', False):
        llm_config = configure_llm_from_args(args)
        if llm_config and llm_config.enabled:
            print(f"✨ AI-enhanced recommendations enabled")
    
    # Load custom weights if provided
    weights = None
    if args.weights:
        weights = load_custom_weights(args.weights)
        print(f"✓ Using custom weights from: {args.weights}")
    
    # Score all resumes
    scorer = ATSResumeScorer(weights=weights, llm_config=llm_config)
    results = []
    recommendation_level = getattr(args, 'level', 'normal')
    
    for i, resume_path in enumerate(args.resumes, 1):
        resume_file = Path(resume_path)
        if not resume_file.exists():
            print(f"⚠️  Warning: Resume file not found: {resume_path}")
            continue
            
        print(f"📄 Processing {i}/{len(args.resumes)}: {resume_file.name}")
        try:
            result = scorer.score_resume(str(resume_file), jd_text, recommendation_level)
            results.append({
                'filename': resume_file.name,
                'filepath': str(resume_file),
                'score': result['overall_score'],
                'grade': result['grade'],
                'llm_enhanced': result.get('llm_enhanced', False),
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
    
    # Configure LLM if enabled
    llm_config = None
    if getattr(args, 'enable_llm', False):
        llm_config = configure_llm_from_args(args)
        if llm_config and llm_config.enabled:
            print(f"✨ AI-enhanced analysis enabled")
    
    # Load custom weights if provided
    weights = None
    if args.weights:
        weights = load_custom_weights(args.weights)
    
    # Score resume with detailed level
    scorer = ATSResumeScorer(weights=weights, llm_config=llm_config)
    result = scorer.score_resume(args.resume, jd_text, "detailed")
    
    # Generate detailed analysis
    analysis = generate_detailed_analysis(result, args.resume, jd_text)
    
    # Display analysis
    print_detailed_analysis(analysis)
    
    # Save if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"📄 Detailed analysis saved to: {args.output}")

def main():
    """Enhanced advanced CLI main function"""
    parser = argparse.ArgumentParser(
        description="Enhanced Advanced ATS Resume Scoring Tool with AI Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Score single resume with AI recommendations
  python cli_advanced.py single --resume resume.pdf --jd job.txt --level detailed --enable-llm
  
  # Score multiple resumes with concise recommendations
  python cli_advanced.py batch --resume-dir ./resumes --jd job.txt --level concise --parallel
  
  # Compare resumes with normal level
  python cli_advanced.py compare --resumes *.pdf --jd job.txt --level normal
  
  # Detailed analysis with custom LLM settings
  python cli_advanced.py analyze --resume resume.pdf --jd job.txt --enable-llm --llm-model gpt-4
  
Environment Variables:
  ATS_LLM_ENABLED=true          # Enable LLM integration
  ATS_LLM_API_KEY=your-key      # API key for LLM provider
  ATS_LLM_PROVIDER=openai       # LLM provider (openai, anthropic, local)
  ATS_LLM_MODEL=gpt-3.5-turbo   # Model name
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Common arguments for all subcommands
    def add_common_args(subparser):
        subparser.add_argument('--weights', '-w', help='Custom weights JSON file')
        subparser.add_argument('--skills-db', help='Custom skills database JSON file')
        subparser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        subparser.add_argument('--level', '-l', choices=['concise', 'normal', 'detailed'], 
                             default='normal', help='Recommendation detail level')
        
        # LLM arguments
        llm_group = subparser.add_argument_group('LLM Settings')
        llm_group.add_argument('--enable-llm', action='store_true', help='Enable AI-enhanced recommendations')
        llm_group.add_argument('--llm-provider', choices=['openai', 'anthropic', 'gemini', 'local'], 
                             default='openai', help='LLM provider')
        llm_group.add_argument('--llm-model', default='gpt-3.5-turbo', help='LLM model name')
        llm_group.add_argument('--llm-api-key', help='API key (or set ATS_LLM_API_KEY)')
        llm_group.add_argument('--llm-endpoint', help='Custom endpoint for local models')
        llm_group.add_argument('--llm-max-tokens', type=int, default=500, help='Max tokens')
        llm_group.add_argument('--llm-temperature', type=float, default=0.7, help='Temperature')
    
    # Single resume scoring
    single_parser = subparsers.add_parser('single', help='Score a single resume')
    single_parser.add_argument('--resume', '-r', required=True, help='Path to resume file')
    single_parser.add_argument('--jd', '-j', required=True, help='Path to job description file')
    single_parser.add_argument('--output', '-o', help='Output file path')
    single_parser.add_argument('--format', '-f', choices=['json', 'text'], default='text', help='Output format')
    add_common_args(single_parser)
    
    # Batch resume scoring
    batch_parser = subparsers.add_parser('batch', help='Score multiple resumes')
    batch_parser.add_argument('--resume-dir', '-d', required=True, help='Directory containing resume files')
    batch_parser.add_argument('--jd', '-j', required=True, help='Path to job description file')
    batch_parser.add_argument('--output', '-o', help='Output file path (.json or .csv)')
    batch_parser.add_argument('--parallel', '-p', action='store_true', help='Enable parallel processing')
    batch_parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    add_common_args(batch_parser)
    
    # Compare resumes command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple resumes')
    compare_parser.add_argument('--resumes', '-r', nargs='+', required=True, help='Resume file paths')
    compare_parser.add_argument('--jd', '-j', required=True, help='Path to job description file')
    compare_parser.add_argument('--output', '-o', help='Output comparison report')
    add_common_args(compare_parser)
    
    # Analyze command for detailed analysis
    analyze_parser = subparsers.add_parser('analyze', help='Detailed analysis of resume vs job description')
    analyze_parser.add_argument('--resume', '-r', required=True, help='Path to resume file')
    analyze_parser.add_argument('--jd', '-j', required=True, help='Path to job description file')
    analyze_parser.add_argument('--output', '-o', help='Output detailed analysis report')
    add_common_args(analyze_parser)
    
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

# Keep existing utility functions
def print_comparison_results(results):
    """Print comparison results in a ranked format"""
    print("\n" + "🏆" * 20 + " RESUME COMPARISON RESULTS " + "🏆" * 20)
    
    successful_results = [r for r in results if 'error' not in r]
    
    if not successful_results:
        print("❌ No resumes were successfully processed")
        return
    
    llm_enhanced_count = len([r for r in successful_results if r.get('llm_enhanced', False)])
    
    print(f"\n📊 RANKING ({len(successful_results)} resumes, {llm_enhanced_count} AI-enhanced):")
    print(f"{'Rank':<6} {'Resume':<40} {'Score':<8} {'Grade':<6} {'Status':<12} {'AI'}")
    print("-" * 75)
    
    for i, result in enumerate(successful_results, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}."
        filename = result['filename']
        if len(filename) > 35:
            filename = filename[:32] + "..."
        
        status = "✅ Strong" if result['score'] >= 80 else "⚠️  Fair" if result['score'] >= 60 else "❌ Weak"
        ai_indicator = "✨" if result.get('llm_enhanced') else "-"
        
        print(f"{medal:<6} {filename:<40} {result['score']:<8.1f} {result['grade']:<6} {status:<12} {ai_indicator}")
    
    # Show top performer details
    if successful_results:
        top_performer = successful_results[0]
        print(f"\n🏆 TOP PERFORMER: {top_performer['filename']}")
        print(f"   Score: {top_performer['score']:.1f}/100")
        print(f"   AI Enhanced: {'Yes' if top_performer.get('llm_enhanced') else 'No'}")
        print(f"   Strengths: {', '.join(get_top_strengths(top_performer['result']))}")

def generate_comparison_report(results, jd_text):
    """Generate a comprehensive comparison report"""
    successful_results = [r for r in results if 'error' not in r]
    
    if not successful_results:
        return {"error": "No resumes successfully processed"}
    
    # Calculate statistics
    scores = [r['score'] for r in successful_results]
    llm_enhanced_count = len([r for r in successful_results if r.get('llm_enhanced', False)])
    
    return {
        "comparison_summary": {
            "total_resumes": len(results),
            "successfully_processed": len(successful_results),
            "ai_enhanced_count": llm_enhanced_count,
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
                "ai_enhanced": r.get('llm_enhanced', False),
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
        "ai_enhanced": result.get('llm_enhanced', False),
        "recommendation_level": result.get('recommendation_level', 'detailed'),
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
        "detailed_recommendations": result.get('detailed_recommendations', []),
        "job_match_deep_dive": result['job_match_analysis'],
        "resume_statistics": result['resume_summary']
    }

def print_detailed_analysis(analysis):
    """Print detailed analysis in a formatted way"""
    print("\n" + "🔬" * 20 + " DETAILED ANALYSIS REPORT " + "🔬" * 20)
    
    print(f"\n📄 RESUME: {Path(analysis['resume_file']).name}")
    print(f"📅 ANALYZED: {analysis['analysis_timestamp']}")
    if analysis.get('ai_enhanced'):
        print("✨ AI-ENHANCED ANALYSIS")
    print(f"📊 RECOMMENDATION LEVEL: {analysis.get('recommendation_level', 'detailed').title()}")
    
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
    
    # Show detailed recommendations if available
    if analysis.get('detailed_recommendations'):
        print(f"\n📋 DETAILED ACTION PLANS:")
        for i, detailed_rec in enumerate(analysis['detailed_recommendations'][:3], 1):
            print(f"\n{i}. {detailed_rec['message']}")
            print(f"   📊 Priority: {detailed_rec.get('priority', 'Medium')} | Impact: {detailed_rec.get('impact', 'TBD')}")
            
            if detailed_rec.get('detailed_explanation'):
                print(f"   📝 Explanation: {detailed_rec['detailed_explanation']}")
            
            if detailed_rec.get('action_steps'):
                print("   🎯 Action Steps:")
                for step in detailed_rec["action_steps"][:4]:
                    print(f"      • {step}")
            
            if detailed_rec.get('examples'):
                print("   💭 Examples:")
                for example in detailed_rec["examples"][:3]:
                    print(f"      • {example}")

# Keep existing utility functions with enhancements
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

if __name__ == "__main__":
    main()