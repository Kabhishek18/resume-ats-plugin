"""
Multi-resume comparison functionality for Resume ATS Plugin.
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np
from collections import Counter

from .core import ResumeATS, analyze_resume


class ResumeComparer:
    """Class to compare multiple resumes against job descriptions or each other."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the resume comparer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.ats = ResumeATS(config)
    
    def compare_multiple_resumes(self, resume_paths: List[str], 
                                job_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Compare multiple resumes, optionally against a job description.
        
        Args:
            resume_paths: List of paths to resume files
            job_description: Optional job description to compare against
            
        Returns:
            Comparison results
        """
        if len(resume_paths) < 2:
            raise ValueError("Need at least 2 resumes to compare")
        
        # Analyze each resume
        analyses = {}
        for resume_path in resume_paths:
            resume_name = os.path.basename(resume_path)
            analyses[resume_name] = analyze_resume(resume_path, job_description, self.config)
        
        # Get comparison metrics
        comparison = self._compare_metrics(analyses)
        
        # Get common and unique skills/keywords
        if job_description:
            keyword_analysis = self._analyze_keywords(analyses)
            comparison["keyword_analysis"] = keyword_analysis
        
        # Get section analysis
        section_analysis = self._analyze_sections(analyses)
        comparison["section_analysis"] = section_analysis
        
        # Create summary
        summary = self._create_comparison_summary(comparison)
        comparison["summary"] = summary
        
        return comparison
    
    def compare_resume_to_multiple_jobs(self, resume_path: str, 
                                       job_descriptions: Dict[str, str]) -> Dict[str, Any]:
        """
        Compare a single resume against multiple job descriptions.
        
        Args:
            resume_path: Path to the resume file
            job_descriptions: Dictionary mapping job names to descriptions
            
        Returns:
            Comparison results
        """
        if len(job_descriptions) < 2:
            raise ValueError("Need at least 2 job descriptions to compare")
        
        # Analyze resume against each job
        analyses = {}
        for job_name, job_desc in job_descriptions.items():
            analyses[job_name] = analyze_resume(resume_path, job_desc, self.config)
        
        # Get comparison metrics
        comparison = self._compare_metrics(analyses)
        
        # Get keyword analysis
        keyword_analysis = self._analyze_keywords(analyses)
        comparison["keyword_analysis"] = keyword_analysis
        
        # Create summary
        summary = self._create_job_comparison_summary(comparison, resume_path)
        comparison["summary"] = summary
        
        return comparison
    
    def _compare_metrics(self, analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare key metrics between analyses.
        
        Args:
            analyses: Dictionary mapping resume names to analysis results
            
        Returns:
            Metrics comparison
        """
        metrics = {}
        
        # Extract metrics to compare
        for name, analysis in analyses.items():
            if "stats" in analysis:
                stats = analysis["stats"]
                metrics[name] = {
                    "overall_ats_score": stats.get("overall_ats_score", 0),
                    "keyword_match_score": stats.get("keyword_match_score", 0),
                    "format_score": stats.get("format_score", 0),
                    "readability_score": stats.get("readability_score", 0),
                    "word_count": stats.get("word_count", 0),
                }
        
        # Determine rankings
        rankings = {}
        for metric in ["overall_ats_score", "keyword_match_score", "format_score", "readability_score"]:
            # Sort by metric, descending
            sorted_items = sorted(metrics.items(), key=lambda x: x[1].get(metric, 0), reverse=True)
            rankings[metric] = [name for name, _ in sorted_items]
        
        # Create visualization data
        visualization_data = {
            "resume_names": list(metrics.keys()),
            "metrics": metrics
        }
        
        return {
            "metrics": metrics,
            "rankings": rankings,
            "visualization_data": visualization_data
        }
    
    def _analyze_keywords(self, analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze keywords across multiple analyses.
        
        Args:
            analyses: Dictionary mapping resume names to analysis results
            
        Returns:
            Keyword analysis
        """
        # Extract keywords from each analysis
        keywords = {}
        for name, analysis in analyses.items():
            if "stats" in analysis:
                stats = analysis["stats"]
                keywords[name] = {
                    "matches": stats.get("keyword_matches", []),
                    "missing": stats.get("missing_keywords", [])
                }
        
        # Find common and unique matched keywords
        all_matches = [set(kw["matches"]) for kw in keywords.values()]
        common_matches = set.intersection(*all_matches) if all_matches else set()
        
        unique_matches = {}
        for name, kw in keywords.items():
            other_matches = set()
            for other_name, other_kw in keywords.items():
                if other_name != name:
                    other_matches.update(other_kw["matches"])
            unique_matches[name] = list(set(kw["matches"]) - other_matches)
        
        # Find common missing keywords
        all_missing = [set(kw["missing"]) for kw in keywords.values()]
        common_missing = set.intersection(*all_missing) if all_missing else set()
        
        # Unique missing (missing in only one resume)
        unique_missing = {}
        for name, kw in keywords.items():
            other_missing = set()
            for other_name, other_kw in keywords.items():
                if other_name != name:
                    other_missing.update(other_kw["missing"])
            unique_missing[name] = list(set(kw["missing"]) - other_missing)
        
        return {
            "keyword_details": keywords,
            "common_matches": list(common_matches),
            "unique_matches": unique_matches,
            "common_missing": list(common_missing),
            "unique_missing": unique_missing
        }
    
    def _analyze_sections(self, analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sections across multiple analyses.
        
        Args:
            analyses: Dictionary mapping resume names to analysis results
            
        Returns:
            Section analysis
        """
        # Extract sections from each analysis
        sections = {}
        for name, analysis in analyses.items():
            sections[name] = analysis.get("sections_detected", [])
        
        # All possible sections
        all_sections = set()
        for section_list in sections.values():
            all_sections.update(section_list)
        
        # Create section presence matrix
        section_matrix = {}
        for name, section_list in sections.items():
            section_matrix[name] = {section: section in section_list for section in all_sections}
        
        # Find common and unique sections
        common_sections = []
        for section in all_sections:
            if all(section_matrix[name][section] for name in section_matrix):
                common_sections.append(section)
        
        unique_sections = {}
        for name, matrix in section_matrix.items():
            unique = []
            for section, present in matrix.items():
                if present and all(not section_matrix[other][section] for other in section_matrix if other != name):
                    unique.append(section)
            unique_sections[name] = unique
        
        return {
            "section_matrix": section_matrix,
            "common_sections": common_sections,
            "unique_sections": unique_sections
        }
    
    def _create_comparison_summary(self, comparison: Dict[str, Any]) -> str:
        """
        Create a summary of the comparison.
        
        Args:
            comparison: Comparison data
            
        Returns:
            Summary text
        """
        metrics = comparison["metrics"]
        rankings = comparison["rankings"]
        
        summary_lines = ["# Resume Comparison Summary"]
        
        # Overall ranking
        summary_lines.append("\n## Overall ATS Score Ranking")
        for i, name in enumerate(rankings["overall_ats_score"]):
            score = metrics[name]["overall_ats_score"]
            summary_lines.append(f"{i+1}. {name}: {score}%")
        
        # Keyword comparison if available
        if "keyword_analysis" in comparison:
            keyword_analysis = comparison["keyword_analysis"]
            
            summary_lines.append("\n## Keyword Analysis")
            
            if keyword_analysis["common_matches"]:
                summary_lines.append("\n### Keywords in All Resumes")
                for keyword in sorted(keyword_analysis["common_matches"]):
                    summary_lines.append(f"- {keyword}")
            
            if any(keyword_analysis["unique_matches"].values()):
                summary_lines.append("\n### Unique Keywords by Resume")
                for name, unique in keyword_analysis["unique_matches"].items():
                    if unique:
                        summary_lines.append(f"\n**{name}**")
                        for keyword in sorted(unique):
                            summary_lines.append(f"- {keyword}")
        
        # Section comparison
        if "section_analysis" in comparison:
            section_analysis = comparison["section_analysis"]
            
            summary_lines.append("\n## Section Analysis")
            
            if section_analysis["common_sections"]:
                summary_lines.append("\n### Sections in All Resumes")
                for section in sorted(section_analysis["common_sections"]):
                    summary_lines.append(f"- {section}")
            
            if any(section_analysis["unique_sections"].values()):
                summary_lines.append("\n### Unique Sections by Resume")
                for name, unique in section_analysis["unique_sections"].items():
                    if unique:
                        summary_lines.append(f"\n**{name}**")
                        for section in sorted(unique):
                            summary_lines.append(f"- {section}")
        
        # Recommendations
        summary_lines.append("\n## Recommendations")
        
        # Best format recommendations
        best_format = rankings["format_score"][0]
        summary_lines.append(f"\n- **Best Formatting**: {best_format} has the best formatting score and can be used as a reference.")
        
        # Keyword recommendations
        if "keyword_analysis" in comparison and "common_missing" in comparison["keyword_analysis"]:
            common_missing = comparison["keyword_analysis"]["common_missing"]
            if common_missing:
                summary_lines.append("\n- **Missing Keywords**: All resumes are missing these important keywords:")
                for keyword in sorted(common_missing[:5]):
                    summary_lines.append(f"  - {keyword}")
                if len(common_missing) > 5:
                    summary_lines.append(f"  - ... and {len(common_missing) - 5} more")
        
        return "\n".join(summary_lines)
    
    def _create_job_comparison_summary(self, comparison: Dict[str, Any], resume_path: str) -> str:
        """
        Create a summary of comparing one resume to multiple jobs.
        
        Args:
            comparison: Comparison data
            resume_path: Path to the resume file
            
        Returns:
            Summary text
        """
        metrics = comparison["metrics"]
        rankings = comparison["rankings"]
        resume_name = os.path.basename(resume_path)
        
        summary_lines = [f"# Job Fit Analysis for {resume_name}"]
        
        # Job ranking
        summary_lines.append("\n## Job Match Ranking")
        for i, job_name in enumerate(rankings["overall_ats_score"]):
            score = metrics[job_name]["overall_ats_score"]
            summary_lines.append(f"{i+1}. {job_name}: {score}%")
        
        # Best match analysis
        best_match = rankings["overall_ats_score"][0]
        best_score = metrics[best_match]["overall_ats_score"]
        summary_lines.append(f"\n## Best Match: {best_match} ({best_score}%)")
        
        # Keyword analysis
        if "keyword_analysis" in comparison:
            keyword_analysis = comparison["keyword_analysis"]
            
            best_matches = keyword_analysis["keyword_details"][best_match]["matches"]
            best_missing = keyword_analysis["keyword_details"][best_match]["missing"]
            
            summary_lines.append("\n### Matched Keywords")
            for keyword in sorted(best_matches[:10]):
                summary_lines.append(f"- {keyword}")
            if len(best_matches) > 10:
                summary_lines.append(f"- ... and {len(best_matches) - 10} more")
            
            summary_lines.append("\n### Missing Keywords")
            for keyword in sorted(best_missing[:10]):
                summary_lines.append(f"- {keyword}")
            if len(best_missing) > 10:
                summary_lines.append(f"- ... and {len(best_missing) - 10} more")
        
        # Recommendations
        summary_lines.append("\n## Recommendations")
        
        # Job-specific recommendations
        summary_lines.append(f"\n### For {best_match}")
        
        # Keyword recommendations
        if "keyword_analysis" in comparison:
            best_missing = keyword_analysis["keyword_details"][best_match]["missing"]
            if best_missing:
                summary_lines.append("\n- **Missing Keywords**: Add these keywords to your resume:")
                for keyword in sorted(best_missing[:5]):
                    summary_lines.append(f"  - {keyword}")
                if len(best_missing) > 5:
                    summary_lines.append(f"  - ... and {len(best_missing) - 5} more")
        
        # If there's a significant gap with the best match
        if len(rankings["overall_ats_score"]) > 1:
            second_best = rankings["overall_ats_score"][1]
            second_score = metrics[second_best]["overall_ats_score"]
            
            if best_score - second_score > 15:  # Significant gap
                summary_lines.append(f"\n### For {second_best}")
                summary_lines.append(f"\nYour resume is significantly better matched to {best_match} than {second_best}. If you're interested in {second_best}, consider:")
                
                if "keyword_analysis" in comparison:
                    second_missing = keyword_analysis["keyword_details"][second_best]["missing"]
                    if second_missing:
                        summary_lines.append("\n- **Missing Keywords**: Add these keywords for this position:")
                        for keyword in sorted(second_missing[:5]):
                            summary_lines.append(f"  - {keyword}")
                        if len(second_missing) > 5:
                            summary_lines.append(f"  - ... and {len(second_missing) - 5} more")
        
        return "\n".join(summary_lines)
    
    def generate_comparison_charts(self, comparison: Dict[str, Any]) -> Dict[str, BytesIO]:
        """
        Generate visualization charts for the comparison.
        
        Args:
            comparison: Comparison data from compare_multiple_resumes or compare_resume_to_multiple_jobs
            
        Returns:
            Dictionary mapping chart names to BytesIO objects containing chart images
        """
        if "visualization_data" not in comparison:
            return {}
        
        viz_data = comparison["visualization_data"]
        resume_names = viz_data["resume_names"]
        metrics = viz_data["metrics"]
        
        charts = {}
        
        # Radar chart for overall comparison
        charts["radar_chart"] = self._create_radar_chart(resume_names, metrics)
        
        # Bar chart for overall ATS score
        charts["ats_score_chart"] = self._create_score_bar_chart(resume_names, metrics, "overall_ats_score", "Overall ATS Score")
        
        # Bar chart for keyword match if available
        if all("keyword_match_score" in metrics[name] for name in resume_names):
            charts["keyword_match_chart"] = self._create_score_bar_chart(resume_names, metrics, "keyword_match_score", "Keyword Match Score")
        
        # Bar chart for format score
        charts["format_score_chart"] = self._create_score_bar_chart(resume_names, metrics, "format_score", "Format Score")
        
        # Word count comparison
        charts["word_count_chart"] = self._create_score_bar_chart(resume_names, metrics, "word_count", "Word Count")
        
        # Keyword comparison if available
        if "keyword_analysis" in comparison:
            keyword_analysis = comparison["keyword_analysis"]
            keyword_details = keyword_analysis["keyword_details"]
            
            # Compare matched and missing keywords
            charts["keyword_comparison_chart"] = self._create_keyword_comparison_chart(resume_names, keyword_details)
        
        # Section comparison if available
        if "section_analysis" in comparison:
            section_analysis = comparison["section_analysis"]
            section_matrix = section_analysis["section_matrix"]
            
            # Create section presence heatmap
            charts["section_heatmap"] = self._create_section_heatmap(section_matrix)
        
        return charts
    
    def _create_radar_chart(self, resume_names: List[str], metrics: Dict[str, Dict[str, float]]) -> BytesIO:
        """
        Create a radar chart comparing resumes across metrics.
        
        Args:
            resume_names: List of resume names
            metrics: Dictionary mapping resume names to metric values
            
        Returns:
            BytesIO object containing the chart image
        """
        # Metrics to include in the radar chart
        radar_metrics = ["keyword_match_score", "format_score", "readability_score"]
        
        # Ensure all metrics exist for all resumes, using 0 as default
        metric_values = []
        for name in resume_names:
            values = []
            for metric in radar_metrics:
                val = metrics[name].get(metric, 0)
                # Normalize to 0-1 scale
                if metric != "readability_score":  # format and keyword are already 0-1
                    val = val / 100 if val > 1 else val
                values.append(val)
            metric_values.append(values)
        
        # Create the radar chart
        plt.figure(figsize=(8, 6))
        
        # Specify the number of metrics (axes)
        num_metrics = len(radar_metrics)
        
        # Calculate angles for the metrics
        angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
        
        # Close the polygon by adding the first angle again
        angles += angles[:1]
        
        # Create beautiful labels
        metric_labels = ["Keyword Match", "Format", "Readability"]
        
        # Make the plot
        ax = plt.subplot(111, polar=True)
        
        # Plot each resume
        for i, name in enumerate(resume_names):
            # Close the polygon by repeating the first value
            values = metric_values[i] + [metric_values[i][0]]
            
            # Plot the values
            ax.plot(angles, values, linewidth=2, linestyle='solid', label=name)
            ax.fill(angles, values, alpha=0.1)
        
        # Set the angle labels
        plt.xticks(angles[:-1], metric_labels)
        
        # Add legend
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        
        # Add title
        plt.title("Resume Comparison Across Metrics", size=15, y=1.1)
        
        # Save to BytesIO
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        
        buf.seek(0)
        return buf
    
    def _create_score_bar_chart(self, resume_names: List[str], metrics: Dict[str, Dict[str, float]], 
                               metric_key: str, title: str) -> BytesIO:
        """
        Create a bar chart comparing resumes on a specific metric.
        
        Args:
            resume_names: List of resume names
            metrics: Dictionary mapping resume names to metric values
            metric_key: Key of the metric to chart
            title: Chart title
            
        Returns:
            BytesIO object containing the chart image
        """
        # Extract metric values
        values = []
        for name in resume_names:
            values.append(metrics[name].get(metric_key, 0))
        
        # Create chart
        plt.figure(figsize=(8, 5))
        
        # Sort by value
        sorted_data = sorted(zip(resume_names, values), key=lambda x: x[1], reverse=True)
        sorted_names = [x[0] for x in sorted_data]
        sorted_values = [x[1] for x in sorted_data]
        
        # Create horizontal bar chart
        y_pos = np.arange(len(sorted_names))
        
        # Add color gradient: green for high values, red for low
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(sorted_values)))
        
        # Plot
        plt.barh(y_pos, sorted_values, color=colors)
        
        # Add names as y-labels
        plt.yticks(y_pos, sorted_names)
        
        # Add value labels
        for i, v in enumerate(sorted_values):
            plt.text(v + 1, i, f"{v:.1f}", va='center')
        
        # Set title and labels
        plt.title(title)
        plt.xlabel("Score" if "score" in metric_key.lower() else "Value")
        
        # Set x-axis limits
        if "score" in metric_key.lower() and not metric_key == "word_count":
            max_val = max(100, max(sorted_values) * 1.1)
            plt.xlim(0, max_val)
        else:
            plt.xlim(0, max(sorted_values) * 1.1)
        
        # Save to BytesIO
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        buf.seek(0)
        return buf
    
    def _create_keyword_comparison_chart(self, resume_names: List[str], 
                                        keyword_details: Dict[str, Dict[str, List[str]]]) -> BytesIO:
        """
        Create a stacked bar chart comparing matched and missing keywords.
        
        Args:
            resume_names: List of resume names
            keyword_details: Dictionary mapping resume names to keyword match details
            
        Returns:
            BytesIO object containing the chart image
        """
        # Extract keyword counts
        matched_counts = []
        missing_counts = []
        
        for name in resume_names:
            if name in keyword_details:
                matched_counts.append(len(keyword_details[name].get("matches", [])))
                missing_counts.append(len(keyword_details[name].get("missing", [])))
            else:
                matched_counts.append(0)
                missing_counts.append(0)
        
        # Create chart
        plt.figure(figsize=(10, 6))
        
        # Set up the plot
        x = np.arange(len(resume_names))
        width = 0.35
        
        # Create bars
        plt.bar(x, matched_counts, width, label='Matched Keywords', color='green')
        plt.bar(x, missing_counts, width, bottom=matched_counts, label='Missing Keywords', color='red')
        
        # Add labels and title
        plt.xlabel('Resume')
        plt.ylabel('Number of Keywords')
        plt.title('Keyword Match Comparison')
        plt.xticks(x, resume_names, rotation=45, ha='right')
        plt.legend()
        
        # Add counts as text
        for i in range(len(resume_names)):
            # Only add text if there's enough room
            if matched_counts[i] > 0:
                plt.text(i, matched_counts[i]/2, str(matched_counts[i]), ha='center', va='center', color='white', fontweight='bold')
            if missing_counts[i] > 0:
                plt.text(i, matched_counts[i] + missing_counts[i]/2, str(missing_counts[i]), ha='center', va='center', color='white', fontweight='bold')
        
        # Save to BytesIO
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        buf.seek(0)
        return buf
    
    def _create_section_heatmap(self, section_matrix: Dict[str, Dict[str, bool]]) -> BytesIO:
        """
        Create a heatmap showing which sections are present in each resume.
        
        Args:
            section_matrix: Matrix of section presence by resume
            
        Returns:
            BytesIO object containing the chart image
        """
        # Extract resume names and section names
        resume_names = list(section_matrix.keys())
        all_sections = set()
        for sections in section_matrix.values():
            all_sections.update(sections.keys())
        section_names = sorted(all_sections)
        
        # Create data matrix
        data = np.zeros((len(resume_names), len(section_names)))
        
        for i, resume in enumerate(resume_names):
            for j, section in enumerate(section_names):
                data[i, j] = 1 if section_matrix[resume].get(section, False) else 0
        
        # Create heatmap
        plt.figure(figsize=(max(8, len(section_names) * 0.5), max(6, len(resume_names) * 0.5)))
        
        # Plot heatmap
        plt.imshow(data, cmap='YlGn', aspect='auto')
        
        # Add labels
        plt.yticks(range(len(resume_names)), resume_names)
        plt.xticks(range(len(section_names)), section_names, rotation=45, ha='right')
        
        # Add colorbar
        cbar = plt.colorbar(ticks=[0, 1])
        cbar.set_ticklabels(['Absent', 'Present'])
        
        # Add title
        plt.title('Section Presence by Resume')
        
        # Add grid
        plt.grid(False)
        
        # Add text annotations
        for i in range(len(resume_names)):
            for j in range(len(section_names)):
                text = "✓" if data[i, j] else "✗"
                color = "black" if data[i, j] else "red"
                plt.text(j, i, text, ha="center", va="center", color=color)
        
        # Save to BytesIO
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        
        buf.seek(0)
        return buf


# Convenience functions
def compare_resumes(resume_paths: List[str], job_description: Optional[str] = None, 
                  config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Compare multiple resumes, optionally against a job description.
    
    Args:
        resume_paths: List of paths to resume files
        job_description: Optional job description to compare against
        config: Optional configuration dictionary
        
    Returns:
        Comparison results
    """
    comparer = ResumeComparer(config)
    return comparer.compare_multiple_resumes(resume_paths, job_description)


def compare_resume_to_jobs(resume_path: str, job_descriptions: Dict[str, str], 
                          config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Compare a single resume against multiple job descriptions.
    
    Args:
        resume_path: Path to the resume file
        job_descriptions: Dictionary mapping job names to descriptions
        config: Optional configuration dictionary
        
    Returns:
        Comparison results
    """
    comparer = ResumeComparer(config)
    return comparer.compare_resume_to_multiple_jobs(resume_path, job_descriptions)
