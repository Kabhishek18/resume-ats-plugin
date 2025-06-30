# ats_resume_scorer/utils/report_generator.py
"""
Report Generator - Creates comprehensive scoring reports with recommendations
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from ..parsers.resume_parser import ResumeData
from ..parsers.jd_parser import JobDescription


@dataclass
class RecommendationItem:
    """Individual recommendation with priority and category"""

    message: str
    category: str
    priority: int  # 1=high, 2=medium, 3=low
    impact: str  # What improvement this could bring


class ReportGenerator:
    """Generates comprehensive ATS scoring reports"""

    def __init__(self):
        """Initialize report generator"""
        pass

    def generate_comprehensive_report(
        self,
        resume_data: ResumeData,
        job_description: JobDescription,
        scoring_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate complete ATS scoring report"""

        # Calculate grade
        grade = self._calculate_grade(scoring_results["total_score"])

        # Generate recommendations
        recommendations = self._generate_recommendations(
            resume_data, job_description, scoring_results
        )

        # Analyze job match
        job_match_analysis = self._analyze_job_match(resume_data, job_description)

        # Create resume summary
        resume_summary = self._create_resume_summary(resume_data)

        return {
            "overall_score": scoring_results["total_score"],
            "grade": grade,
            "detailed_breakdown": scoring_results["detailed_scores"],
            "resume_summary": resume_summary,
            "job_match_analysis": job_match_analysis,
            "recommendations": [rec.message for rec in recommendations],
            "detailed_recommendations": [
                {
                    "message": rec.message,
                    "category": rec.category,
                    "priority": rec.priority,
                    "impact": rec.impact,
                }
                for rec in recommendations
            ],
            "scoring_weights": scoring_results["weights_used"],
            "improvement_potential": self._calculate_improvement_potential(
                scoring_results
            ),
            "ats_compatibility": self._assess_ats_compatibility(
                scoring_results["total_score"]
            ),
        }

    def _calculate_grade(self, score: float) -> str:
        """Convert numerical score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _create_resume_summary(self, resume_data: ResumeData) -> Dict[str, Any]:
        """Create summary of resume contents"""
        return {
            "has_contact_info": bool(
                resume_data.contact_info.emails and resume_data.contact_info.phones
            ),
            "has_summary": bool(resume_data.summary),
            "skills_count": len(resume_data.skills),
            "education_count": len(resume_data.education),
            "experience_count": len(resume_data.experience),
            "certifications_count": len(resume_data.certifications),
            "total_word_count": len(resume_data.raw_text.split()),
            "has_linkedin": bool(resume_data.contact_info.linkedin),
            "has_github": bool(resume_data.contact_info.github),
        }

    def _analyze_job_match(
        self, resume_data: ResumeData, job_description: JobDescription
    ) -> Dict[str, Any]:
        """Analyze how well resume matches job requirements"""
        resume_skills = set([skill.lower() for skill in resume_data.skills])
        required_skills = set(
            [skill.lower() for skill in job_description.required_skills]
        )
        preferred_skills = set(
            [skill.lower() for skill in job_description.preferred_skills]
        )

        # Calculate matches
        required_matches = resume_skills.intersection(required_skills)
        preferred_matches = resume_skills.intersection(preferred_skills)

        # Find missing skills
        missing_required = required_skills - resume_skills
        missing_preferred = preferred_skills - resume_skills

        # Calculate match percentages
        required_match_percent = (
            (len(required_matches) / len(required_skills) * 100)
            if required_skills
            else 100
        )
        preferred_match_percent = (
            (len(preferred_matches) / len(preferred_skills) * 100)
            if preferred_skills
            else 0
        )

        return {
            "required_skills_matched": len(required_matches),
            "required_skills_total": len(required_skills),
            "required_match_percentage": round(required_match_percent, 1),
            "preferred_skills_matched": len(preferred_matches),
            "preferred_skills_total": len(preferred_skills),
            "preferred_match_percentage": round(preferred_match_percent, 1),
            "matched_required_skills": list(required_matches),
            "matched_preferred_skills": list(preferred_matches),
            "missing_required_skills": list(missing_required),
            "missing_preferred_skills": list(missing_preferred),
        }

    def _generate_recommendations(
        self,
        resume_data: ResumeData,
        job_description: JobDescription,
        scoring_results: Dict[str, Any],
    ) -> List[RecommendationItem]:
        """Generate actionable recommendations based on scoring results"""

        recommendations = []
        scores = scoring_results["detailed_scores"]

        # Keyword/Skills recommendations
        if scores["keyword_match"] < 70:
            missing_skills = self._get_missing_skills(resume_data, job_description)
            if missing_skills:
                recommendations.append(
                    RecommendationItem(
                        message=f"Add these critical missing skills: {', '.join(missing_skills[:5])}",
                        category="Skills",
                        priority=1,
                        impact="Could increase keyword match score by 15-25 points",
                    )
                )

        # Format compliance recommendations
        if scores["format_compliance"] < 80:
            format_issues = self._identify_format_issues(resume_data)
            for issue in format_issues:
                recommendations.append(issue)

        # Action verbs recommendations
        if scores["action_verbs_grammar"] < 70:
            recommendations.append(
                RecommendationItem(
                    message="Use more action verbs to describe your achievements (e.g., 'developed', 'implemented', 'led')",
                    category="Language",
                    priority=2,
                    impact="Improves ATS parsing and makes resume more compelling",
                )
            )

        # Experience recommendations
        if scores["experience_match"] < 80:
            exp_recommendations = self._get_experience_recommendations(
                resume_data, job_description
            )
            recommendations.extend(exp_recommendations)

        # Education recommendations
        if scores["education_match"] < 80:
            edu_recommendations = self._get_education_recommendations(
                resume_data, job_description
            )
            recommendations.extend(edu_recommendations)

        # Title match recommendations
        if scores["title_match"] < 60:
            recommendations.append(
                RecommendationItem(
                    message="Consider adjusting your job titles to better match the target role",
                    category="Experience",
                    priority=2,
                    impact="Better title alignment can improve recruiter attention",
                )
            )

        # Readability recommendations
        if scores["readability"] < 70:
            recommendations.append(
                RecommendationItem(
                    message="Improve resume structure with clear sections and consistent formatting",
                    category="Format",
                    priority=2,
                    impact="Better readability improves both ATS and human review",
                )
            )

        # Sort by priority and return top recommendations
        recommendations.sort(key=lambda x: x.priority)
        return recommendations[:10]  # Return top 10 recommendations

    def _get_missing_skills(
        self, resume_data: ResumeData, job_description: JobDescription
    ) -> List[str]:
        """Identify missing required skills"""
        resume_skills = set([skill.lower() for skill in resume_data.skills])
        required_skills = set(
            [skill.lower() for skill in job_description.required_skills]
        )
        missing = required_skills - resume_skills
        return list(missing)

    def _identify_format_issues(
        self, resume_data: ResumeData
    ) -> List[RecommendationItem]:
        """Identify specific formatting issues"""
        issues = []

        # Check contact info
        if not resume_data.contact_info.emails:
            issues.append(
                RecommendationItem(
                    message="Add a professional email address",
                    category="Contact",
                    priority=1,
                    impact="Essential for ATS systems and recruiters to contact you",
                )
            )

        if not resume_data.contact_info.phones:
            issues.append(
                RecommendationItem(
                    message="Include a phone number",
                    category="Contact",
                    priority=1,
                    impact="Provides alternative contact method for recruiters",
                )
            )

        # Check sections
        if not resume_data.experience:
            issues.append(
                RecommendationItem(
                    message="Add work experience section",
                    category="Content",
                    priority=1,
                    impact="Experience section is critical for ATS parsing",
                )
            )

        if not resume_data.skills:
            issues.append(
                RecommendationItem(
                    message="Add a dedicated skills section",
                    category="Content",
                    priority=1,
                    impact="Helps ATS systems identify your technical capabilities",
                )
            )

        # Check for bullet points
        if not any(
            "•" in exp.description[0] if exp.description else False
            for exp in resume_data.experience
        ):
            issues.append(
                RecommendationItem(
                    message="Use bullet points to list achievements in work experience",
                    category="Format",
                    priority=2,
                    impact="Bullet points improve ATS parsing and readability",
                )
            )

        return issues

    def _get_experience_recommendations(
        self, resume_data: ResumeData, job_description: JobDescription
    ) -> List[RecommendationItem]:
        """Generate experience-related recommendations"""
        recommendations = []

        # Check if quantified achievements are present
        has_numbers = any(
            any(char.isdigit() for char in " ".join(exp.description))
            for exp in resume_data.experience
        )

        if not has_numbers:
            recommendations.append(
                RecommendationItem(
                    message="Quantify your achievements with numbers, percentages, or metrics",
                    category="Experience",
                    priority=1,
                    impact="Quantified achievements are more compelling and ATS-friendly",
                )
            )

        # Check experience descriptions length
        short_descriptions = [
            exp
            for exp in resume_data.experience
            if len(" ".join(exp.description)) < 100
        ]

        if short_descriptions:
            recommendations.append(
                RecommendationItem(
                    message="Expand experience descriptions with more specific achievements",
                    category="Experience",
                    priority=2,
                    impact="Detailed descriptions provide more keyword opportunities",
                )
            )

        return recommendations

    def _get_education_recommendations(
        self, resume_data: ResumeData, job_description: JobDescription
    ) -> List[RecommendationItem]:
        """Generate education-related recommendations"""
        recommendations = []

        if not resume_data.education and job_description.education_requirements:
            recommendations.append(
                RecommendationItem(
                    message="Add education section with relevant degrees or certifications",
                    category="Education",
                    priority=1,
                    impact="Education section may be required for many positions",
                )
            )

        return recommendations

    def _calculate_improvement_potential(
        self, scoring_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate potential score improvements"""
        scores = scoring_results["detailed_scores"]
        weights = scoring_results["weights_used"]

        # Find areas with biggest improvement potential
        improvement_opportunities = []

        for category, score in scores.items():
            if score < 90:  # Room for improvement
                weight = weights[category]
                potential_gain = (90 - score) * weight  # Assume we can get to 90%
                improvement_opportunities.append(
                    {
                        "category": category,
                        "current_score": score,
                        "potential_gain": round(potential_gain, 2),
                        "weight": weight,
                    }
                )

        # Sort by potential gain
        improvement_opportunities.sort(key=lambda x: x["potential_gain"], reverse=True)

        total_potential = sum(
            opp["potential_gain"] for opp in improvement_opportunities
        )
        max_possible_score = scoring_results["total_score"] + total_potential

        return {
            "current_score": scoring_results["total_score"],
            "max_possible_score": round(min(max_possible_score, 100), 2),
            "total_potential_gain": round(total_potential, 2),
            "top_improvement_areas": improvement_opportunities[:3],
        }

    def _assess_ats_compatibility(self, score: float) -> Dict[str, Any]:
        """Assess overall ATS compatibility"""
        if score >= 85:
            status = "Excellent"
            description = "Your resume is highly optimized for ATS systems"
            likelihood = "Very High"
        elif score >= 75:
            status = "Good"
            description = "Your resume should perform well with most ATS systems"
            likelihood = "High"
        elif score >= 65:
            status = "Fair"
            description = (
                "Your resume may pass ATS filters but has room for improvement"
            )
            likelihood = "Moderate"
        elif score >= 50:
            status = "Poor"
            description = "Your resume may struggle with ATS systems"
            likelihood = "Low"
        else:
            status = "Very Poor"
            description = "Your resume is unlikely to pass ATS filters"
            likelihood = "Very Low"

        return {
            "status": status,
            "description": description,
            "pass_likelihood": likelihood,
            "score": score,
        }

    def generate_summary_report(self, comprehensive_report: Dict[str, Any]) -> str:
        """Generate a human-readable summary report"""
        score = comprehensive_report["overall_score"]
        grade = comprehensive_report["grade"]

        summary = f"""
ATS RESUME SCORE REPORT
=======================

Overall Score: {score}/100 (Grade: {grade})
ATS Compatibility: {comprehensive_report['ats_compatibility']['status']}

SCORE BREAKDOWN:
"""

        for category, score in comprehensive_report["detailed_breakdown"].items():
            category_name = category.replace("_", " ").title()
            summary += f"  {category_name:<25}: {score:>5.1f}/100\n"

        summary += f"""
RESUME SUMMARY:
  Skills Listed: {comprehensive_report['resume_summary']['skills_count']}
  Experience Entries: {comprehensive_report['resume_summary']['experience_count']}
  Education Entries: {comprehensive_report['resume_summary']['education_count']}
  
JOB MATCH ANALYSIS:
  Required Skills Match: {comprehensive_report['job_match_analysis']['required_match_percentage']:.1f}%
  Preferred Skills Match: {comprehensive_report['job_match_analysis']['preferred_match_percentage']:.1f}%
  
TOP RECOMMENDATIONS:
"""

        for i, rec in enumerate(comprehensive_report["recommendations"][:5], 1):
            summary += f"  {i}. {rec}\n"

        summary += f"""
IMPROVEMENT POTENTIAL:
  Current Score: {comprehensive_report['improvement_potential']['current_score']}/100
  Maximum Possible: {comprehensive_report['improvement_potential']['max_possible_score']}/100
  Potential Gain: +{comprehensive_report['improvement_potential']['total_potential_gain']} points
"""

        return summary

    def export_to_json(self, report: Dict[str, Any], filename: str) -> None:
        """Export report to JSON file"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def export_to_text(self, report: Dict[str, Any], filename: str) -> None:
        """Export summary report to text file"""
        summary = self.generate_summary_report(report)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(summary)
