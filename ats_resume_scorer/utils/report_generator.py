# ats_resume_scorer/utils/report_generator.py
"""
Enhanced Report Generator with LLM Integration and Multiple Recommendation Levels
"""

from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
import json
import os

from ..parsers.resume_parser import ResumeData
from ..parsers.jd_parser import JobDescription


RecommendationLevel = Literal["concise", "normal", "detailed"]


@dataclass
class RecommendationItem:
    """Individual recommendation with priority, category, and level-specific content"""

    message: str
    category: str
    priority: int  # 1=high, 2=medium, 3=low
    impact: str  # What improvement this could bring
    detailed_explanation: Optional[str] = None  # For detailed level
    action_steps: Optional[List[str]] = None  # Specific action items
    examples: Optional[List[str]] = None  # Examples for implementation


@dataclass
class LLMConfig:
    """Configuration for LLM integration"""
    
    enabled: bool = False
    provider: str = "openai"  # "openai", "anthropic", "local"
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    max_tokens: int = 500
    temperature: float = 0.7


class LLMRecommendationEngine:
    """LLM-powered recommendation engine for enhanced suggestions"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        
        if config.enabled:
            self._initialize_llm_client()
    
    def _initialize_llm_client(self):
        """Initialize LLM client based on provider"""
        try:
            if self.config.provider == "openai":
                import openai
                self.client = openai.OpenAI(api_key=self.config.api_key)
            elif self.config.provider == "anthropic":
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.config.api_key)
            elif self.config.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.config.api_key)
                self.client = genai.GenerativeModel(self.config.model)
            elif self.config.provider == "local":
                # For local models like Ollama
                import requests
                self.client = requests.Session()
                # Validate endpoint is provided
                if not self.config.endpoint:
                    print("Warning: Local model provider requires ATS_LLM_ENDPOINT to be set")
                    self.config.enabled = False
        except ImportError as e:
            print(f"Warning: LLM provider {self.config.provider} not available: {e}")
            self.config.enabled = False
    
    def enhance_recommendations(
        self, 
        basic_recommendations: List[RecommendationItem],
        resume_data: ResumeData,
        job_description: JobDescription,
        level: RecommendationLevel = "normal"
    ) -> List[RecommendationItem]:
        """Enhance recommendations using LLM"""
        
        if not self.config.enabled or not self.client:
            return basic_recommendations
        
        enhanced_recommendations = []
        
        for rec in basic_recommendations:
            try:
                enhanced_rec = self._enhance_single_recommendation(
                    rec, resume_data, job_description, level
                )
                enhanced_recommendations.append(enhanced_rec)
            except Exception as e:
                print(f"Warning: Failed to enhance recommendation: {e}")
                enhanced_recommendations.append(rec)
        
        return enhanced_recommendations
    
    def _enhance_single_recommendation(
        self,
        recommendation: RecommendationItem,
        resume_data: ResumeData,
        job_description: JobDescription,
        level: RecommendationLevel
    ) -> RecommendationItem:
        """Enhance a single recommendation using LLM"""
        
        prompt = self._build_enhancement_prompt(
            recommendation, resume_data, job_description, level
        )
        
        if self.config.provider == "openai":
            response = self._call_openai(prompt)
        elif self.config.provider == "anthropic":
            response = self._call_anthropic(prompt)
        elif self.config.provider == "gemini":
            response = self._call_gemini(prompt)
        elif self.config.provider == "local":
            response = self._call_local_model(prompt)
        else:
            return recommendation
        
        return self._parse_llm_response(recommendation, response, level)
    
    def _build_enhancement_prompt(
        self,
        recommendation: RecommendationItem,
        resume_data: ResumeData,
        job_description: JobDescription,
        level: RecommendationLevel
    ) -> str:
        """Build prompt for LLM enhancement"""
        
        context = f"""
        Resume Summary:
        - Skills: {', '.join(resume_data.skills[:10])}
        - Experience: {len(resume_data.experience)} positions
        - Education: {len(resume_data.education)} entries
        
        Job Requirements:
        - Title: {job_description.title}
        - Required Skills: {', '.join(job_description.required_skills[:10])}
        - Experience: {job_description.experience_requirements}
        
        Current Recommendation:
        Category: {recommendation.category}
        Message: {recommendation.message}
        Priority: {recommendation.priority}
        Impact: {recommendation.impact}
        """
        
        if level == "concise":
            prompt = f"""
            {context}
            
            Please provide a concise, actionable enhancement to this resume recommendation.
            Keep it under 50 words and focus on the most important action.
            
            Respond with ONLY valid JSON in this exact format:
            {{"enhanced_message": "your enhanced message here"}}
            
            Do not include any other text, explanations, or formatting.
            """
        
        elif level == "normal":
            prompt = f"""
            {context}
            
            Please enhance this resume recommendation with:
            1. A clearer, more actionable message
            2. Specific steps the candidate can take
            3. Why this improvement matters
            
            Respond with ONLY valid JSON in this exact format:
            {{
                "enhanced_message": "improved recommendation message",
                "action_steps": ["step 1", "step 2", "step 3"],
                "explanation": "why this matters"
            }}
            
            Do not include any other text, explanations, or formatting.
            """
        
        else:  # detailed
            prompt = f"""
            {context}
            
            Please provide a comprehensive enhancement to this resume recommendation including:
            1. A detailed explanation of the issue
            2. Step-by-step action plan
            3. Specific examples or templates
            4. Expected impact and timeline
            5. Common mistakes to avoid
            
            Respond with ONLY valid JSON in this exact format:
            {{
                "enhanced_message": "detailed recommendation message",
                "detailed_explanation": "comprehensive explanation",
                "action_steps": ["step 1", "step 2", "step 3", "step 4"],
                "examples": ["example 1", "example 2"],
                "timeline": "expected timeline",
                "common_mistakes": ["mistake 1", "mistake 2"]
            }}
            
            Do not include any other text, explanations, or formatting. Ensure all strings are properly escaped.
            """
        
        return prompt
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
        return response.choices[0].message.content
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            # Configure generation parameters
            generation_config = {
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
                "top_p": 0.95,
                "top_k": 64
            }
            
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Handle potential safety issues
            if response.candidates and response.candidates[0].content:
                return response.candidates[0].content.parts[0].text
            else:
                # If content was blocked or empty, return a fallback
                return '{"enhanced_message": "Unable to generate enhanced recommendation due to content policy."}'
                
        except Exception as e:
            print(f"Gemini API error: {e}")
            return '{"enhanced_message": "Error generating enhanced recommendation."}'
    
    def _call_local_model(self, prompt: str) -> str:
        """Call local model (e.g., Ollama)"""
        if not self.config.endpoint:
            raise ValueError("Endpoint required for local model")
        
        try:
            # Ollama API format
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            }
            
            response = self.client.post(
                self.config.endpoint,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                print(f"Local model error: {response.status_code} - {response.text}")
                return '{"enhanced_message": "Error calling local model."}'
                
        except Exception as e:
            print(f"Local model connection error: {e}")
            return '{"enhanced_message": "Failed to connect to local model."}'
    
    def _parse_llm_response(
        self,
        original_rec: RecommendationItem,
        llm_response: str,
        level: RecommendationLevel
    ) -> RecommendationItem:
        """Parse LLM response and create enhanced recommendation"""
        
        try:
            # Clean the response first - remove control characters and fix formatting
            cleaned_response = self._clean_llm_response(llm_response)
            
            # Extract JSON from response
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = cleaned_response[start_idx:end_idx]
                parsed_response = json.loads(json_str)
            else:
                # If no valid JSON found, try to extract key information from text
                parsed_response = self._extract_info_from_text(cleaned_response, level)
            
            # Create enhanced recommendation
            enhanced_rec = RecommendationItem(
                message=parsed_response.get("enhanced_message", original_rec.message),
                category=original_rec.category,
                priority=original_rec.priority,
                impact=original_rec.impact,
                detailed_explanation=parsed_response.get("detailed_explanation"),
                action_steps=parsed_response.get("action_steps"),
                examples=parsed_response.get("examples")
            )
            
            return enhanced_rec
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse LLM response: {e}")
            # Return enhanced version using text extraction as fallback
            return self._create_fallback_recommendation(original_rec, llm_response, level)
    
    def _clean_llm_response(self, response: str) -> str:
        """Clean LLM response by removing control characters and fixing formatting"""
        import re
        
        # Remove control characters (keeping newlines and tabs)
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', response)
        
        # Remove markdown formatting if present
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)
        
        # Fix common JSON issues in Llama responses
        cleaned = re.sub(r'(?<!\\)"([^"]*)"([^,}\]:\s])', r'"\1",\2', cleaned)  # Missing commas
        cleaned = re.sub(r'},\s*}', '}}', cleaned)  # Extra commas before closing
        cleaned = re.sub(r'{\s*,', '{', cleaned)  # Leading commas
        cleaned = re.sub(r',\s*}', '}', cleaned)  # Trailing commas
        cleaned = re.sub(r',\s*]', ']', cleaned)  # Trailing commas in arrays
        
        # Fix unescaped quotes in strings
        cleaned = re.sub(r'(?<!\\)"([^"]*[^\\])"([^,}\]:\s])', r'"\1"\2', cleaned)
        
        # Handle multiline strings - replace internal newlines with spaces
        lines = cleaned.split('\n')
        in_string = False
        result_lines = []
        current_line = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Count unescaped quotes to determine if we're inside a string
            quote_count = len(re.findall(r'(?<!\\)"', line))
            
            if quote_count % 2 == 1:
                in_string = not in_string
                
            if in_string and current_line:
                current_line += " " + line
            else:
                if current_line:
                    result_lines.append(current_line)
                current_line = line
        
        if current_line:
            result_lines.append(current_line)
            
        return ' '.join(result_lines)
    
    def _extract_info_from_text(self, text: str, level: RecommendationLevel) -> dict:
        """Extract recommendation info from plain text when JSON parsing fails"""
        
        # Extract enhanced message (first substantial sentence or paragraph)
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 30]
        enhanced_message = sentences[0] + '.' if sentences else text[:300]
        
        # Clean up the enhanced message
        enhanced_message = enhanced_message.replace('\n', ' ').strip()
        if len(enhanced_message) > 200:
            enhanced_message = enhanced_message[:200] + "..."
        
        # Extract action steps (look for numbered lists, bullet points, or step patterns)
        action_steps = []
        import re
        
        # Look for step patterns
        step_patterns = [
            r'Step\s*\d+[:\-]\s*([^.\n]+)',
            r'^\d+\.\s*([^.\n]+)',
            r'[•\-\*]\s*([^.\n]+)',
            r'Action\s*\d+[:\-]\s*([^.\n]+)'
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            if matches:
                action_steps.extend([match.strip() for match in matches[:5]])
                break
        
        # If no structured steps found, look for sentences with action words
        if not action_steps:
            action_words = ['add', 'include', 'update', 'create', 'develop', 'implement', 'improve']
            for sentence in sentences[:5]:
                if any(word in sentence.lower() for word in action_words):
                    action_steps.append(sentence.strip())
        
        # Extract examples (look for example patterns)
        examples = []
        example_patterns = [
            r'(?:example|for instance|such as)[:\s]*([^.\n]{20,})',
            r'\'([^\']{20,})\'',
            r'"([^"]{20,})"',
            r'template[:\s]*([^.\n]{20,})'
        ]
        
        for pattern in example_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                examples.extend([ex.strip() for ex in matches[:3]])
                if len(examples) >= 3:
                    break
        
        return {
            "enhanced_message": enhanced_message,
            "action_steps": action_steps[:5] if action_steps else None,
            "examples": examples[:3] if examples else None,
            "detailed_explanation": text[:400] + "..." if len(text) > 400 else text
        }
    
    def _create_fallback_recommendation(
        self, 
        original_rec: RecommendationItem, 
        llm_text: str, 
        level: RecommendationLevel
    ) -> RecommendationItem:
        """Create enhanced recommendation using text extraction when JSON parsing fails"""
        
        extracted = self._extract_info_from_text(llm_text, level)
        
        return RecommendationItem(
            message=extracted.get("enhanced_message", original_rec.message),
            category=original_rec.category,
            priority=original_rec.priority,
            impact=original_rec.impact,
            detailed_explanation=extracted.get("detailed_explanation"),
            action_steps=extracted.get("action_steps"),
            examples=extracted.get("examples")
        )


class ReportGenerator:
    """Enhanced report generator with multiple recommendation levels and LLM integration"""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize report generator with optional LLM configuration"""
        self.llm_config = llm_config or LLMConfig()
        self.llm_engine = LLMRecommendationEngine(self.llm_config) if llm_config else None

    def generate_comprehensive_report(
        self,
        resume_data: ResumeData,
        job_description: JobDescription,
        scoring_results: Dict[str, Any],
        recommendation_level: RecommendationLevel = "normal"
    ) -> Dict[str, Any]:
        """Generate complete ATS scoring report with enhanced recommendations"""

        # Calculate grade
        grade = self._calculate_grade(scoring_results["total_score"])

        # Generate basic recommendations
        basic_recommendations = self._generate_recommendations(
            resume_data, job_description, scoring_results
        )

        # Enhance recommendations with LLM if available
        if self.llm_engine and self.llm_config.enabled:
            try:
                enhanced_recommendations = self.llm_engine.enhance_recommendations(
                    basic_recommendations, resume_data, job_description, recommendation_level
                )
            except Exception as e:
                print(f"Warning: LLM enhancement failed: {e}")
                enhanced_recommendations = basic_recommendations
        else:
            enhanced_recommendations = basic_recommendations

        # Format recommendations based on level
        formatted_recommendations = self._format_recommendations_by_level(
            enhanced_recommendations, recommendation_level
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
            "recommendations": formatted_recommendations["simple_list"],
            "detailed_recommendations": formatted_recommendations["detailed_list"],
            "recommendation_level": recommendation_level,
            "llm_enhanced": self.llm_config.enabled,
            "scoring_weights": scoring_results["weights_used"],
            "improvement_potential": self._calculate_improvement_potential(scoring_results),
            "ats_compatibility": self._assess_ats_compatibility(scoring_results["total_score"]),
        }

    def _format_recommendations_by_level(
        self, 
        recommendations: List[RecommendationItem], 
        level: RecommendationLevel
    ) -> Dict[str, Any]:
        """Format recommendations based on the specified level"""
        
        if level == "concise":
            return self._format_concise_recommendations(recommendations)
        elif level == "normal":
            return self._format_normal_recommendations(recommendations)
        else:  # detailed
            return self._format_detailed_recommendations(recommendations)

    def _format_concise_recommendations(
        self, recommendations: List[RecommendationItem]
    ) -> Dict[str, Any]:
        """Format recommendations in concise format"""
        
        # Get top 5 high-priority recommendations
        high_priority = [r for r in recommendations if r.priority == 1][:5]
        
        simple_list = [rec.message for rec in high_priority]
        
        detailed_list = [
            {
                "message": rec.message,
                "category": rec.category,
                "priority": "High",
            }
            for rec in high_priority
        ]
        
        return {
            "simple_list": simple_list,
            "detailed_list": detailed_list,
            "total_recommendations": len(high_priority)
        }

    def _format_normal_recommendations(
        self, recommendations: List[RecommendationItem]
    ) -> Dict[str, Any]:
        """Format recommendations in normal detail level"""
        
        # Get top 8 recommendations
        top_recommendations = recommendations[:8]
        
        simple_list = [rec.message for rec in top_recommendations]
        
        detailed_list = [
            {
                "message": rec.message,
                "category": rec.category,
                "priority": self._priority_to_text(rec.priority),
                "impact": rec.impact,
                "action_steps": rec.action_steps[:3] if rec.action_steps else []
            }
            for rec in top_recommendations
        ]
        
        return {
            "simple_list": simple_list,
            "detailed_list": detailed_list,
            "total_recommendations": len(top_recommendations)
        }

    def _format_detailed_recommendations(
        self, recommendations: List[RecommendationItem]
    ) -> Dict[str, Any]:
        """Format recommendations in detailed format"""
        
        # Include all recommendations with full details
        simple_list = [rec.message for rec in recommendations]
        
        detailed_list = [
            {
                "message": rec.message,
                "category": rec.category,
                "priority": self._priority_to_text(rec.priority),
                "impact": rec.impact,
                "detailed_explanation": rec.detailed_explanation,
                "action_steps": rec.action_steps or [],
                "examples": rec.examples or []
            }
            for rec in recommendations
        ]
        
        return {
            "simple_list": simple_list,
            "detailed_list": detailed_list,
            "total_recommendations": len(recommendations)
        }

    def _priority_to_text(self, priority: int) -> str:
        """Convert priority number to text"""
        return {1: "High", 2: "Medium", 3: "Low"}.get(priority, "Medium")

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
                        action_steps=[
                            f"Add '{skill}' to your skills section" for skill in missing_skills[:3]
                        ] + [
                            "Include these skills in your experience descriptions",
                            "Consider taking online courses to gain these skills"
                        ],
                        examples=[
                            f"Skills: Python, JavaScript, {missing_skills[0]}, {missing_skills[1] if len(missing_skills) > 1 else 'SQL'}",
                            f"Experience: Developed applications using {missing_skills[0] if missing_skills else 'relevant technology'}"
                        ]
                    )
                )

        # Format compliance recommendations
        if scores["format_compliance"] < 80:
            format_issues = self._identify_format_issues(resume_data)
            recommendations.extend(format_issues)

        # Action verbs recommendations
        if scores["action_verbs_grammar"] < 70:
            recommendations.append(
                RecommendationItem(
                    message="Use more action verbs to describe your achievements (e.g., 'developed', 'implemented', 'led')",
                    category="Language",
                    priority=2,
                    impact="Improves ATS parsing and makes resume more compelling",
                    action_steps=[
                        "Replace passive voice with active voice",
                        "Start bullet points with strong action verbs",
                        "Use past tense for previous roles, present tense for current role",
                        "Quantify achievements with numbers and percentages"
                    ],
                    examples=[
                        "Instead of: 'Was responsible for managing team' → 'Led team of 5 developers'",
                        "Instead of: 'Helped with project' → 'Delivered project 2 weeks ahead of schedule'",
                        "Instead of: 'Worked on application' → 'Developed web application serving 10,000+ users'"
                    ]
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
                    action_steps=[
                        "Review target job title and identify key terms",
                        "Adjust your most recent title to include relevant keywords",
                        "Use industry-standard job titles when possible",
                        "Consider adding alternate titles in parentheses"
                    ],
                    examples=[
                        f"Current: Software Developer → Target: {job_description.title}",
                        "Software Engineer (Full-Stack Developer)",
                        "Data Analyst (Business Intelligence Specialist)"
                    ]
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
                    action_steps=[
                        "Use consistent bullet points throughout",
                        "Maintain uniform font sizes and styles",
                        "Add clear section headers",
                        "Use white space effectively",
                        "Keep line length under 80 characters"
                    ],
                    examples=[
                        "Use standard sections: Contact → Summary → Skills → Experience → Education",
                        "Consistent formatting: • Bullet point style",
                        "Clear headers: PROFESSIONAL EXPERIENCE (all caps, bold)"
                    ]
                )
            )

        # Sort by priority and return recommendations
        recommendations.sort(key=lambda x: x.priority)
        return recommendations

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
                    action_steps=[
                        "Use format: firstname.lastname@domain.com",
                        "Avoid unprofessional email addresses",
                        "Place email prominently at the top of resume"
                    ],
                    examples=[
                        "john.smith@gmail.com",
                        "j.smith@outlook.com", 
                        "johnsmith2024@yahoo.com"
                    ]
                )
            )

        if not resume_data.contact_info.phones:
            issues.append(
                RecommendationItem(
                    message="Include a phone number",
                    category="Contact",
                    priority=1,
                    impact="Provides alternative contact method for recruiters",
                    action_steps=[
                        "Use format: +1 (555) 123-4567",
                        "Include country code for international applications",
                        "Ensure voicemail is professional"
                    ],
                    examples=[
                        "+1 (555) 123-4567",
                        "(555) 123-4567",
                        "555.123.4567"
                    ]
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
                    action_steps=[
                        "List positions in reverse chronological order",
                        "Include job title, company, dates, and location",
                        "Add 3-5 bullet points per position",
                        "Focus on achievements, not just responsibilities"
                    ],
                    examples=[
                        "Software Engineer | Tech Corp | Jan 2020 - Dec 2023 | San Francisco, CA",
                        "• Developed 5 web applications serving 50,000+ users",
                        "• Led team of 3 developers in agile environment"
                    ]
                )
            )

        if not resume_data.skills:
            issues.append(
                RecommendationItem(
                    message="Add a dedicated skills section",
                    category="Content",
                    priority=1,
                    impact="Helps ATS systems identify your technical capabilities",
                    action_steps=[
                        "Group skills by category (Technical, Languages, Tools)",
                        "List most relevant skills first",
                        "Use industry-standard skill names",
                        "Include both hard and soft skills"
                    ],
                    examples=[
                        "Technical Skills: Python, JavaScript, SQL, React, AWS",
                        "Tools: Git, Docker, Jenkins, Jira, Visual Studio Code",
                        "Languages: English (Native), Spanish (Conversational)"
                    ]
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
                    action_steps=[
                        "Add specific numbers to demonstrate impact",
                        "Include percentages for improvements",
                        "Mention team sizes you managed",
                        "Specify budget amounts or revenue generated"
                    ],
                    examples=[
                        "Improved application performance by 40%",
                        "Managed team of 8 developers",
                        "Increased sales by $2.5M annually",
                        "Reduced processing time from 2 hours to 15 minutes"
                    ]
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
                    action_steps=[
                        "Add 3-5 bullet points per position",
                        "Focus on achievements, not just duties",
                        "Include technologies and methodologies used",
                        "Describe the impact of your work"
                    ],
                    examples=[
                        "• Developed RESTful APIs using Python and Django",
                        "• Collaborated with UX team to improve user experience",
                        "• Implemented automated testing reducing bugs by 60%"
                    ]
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
                    action_steps=[
                        "List degree, institution, and graduation year",
                        "Include relevant coursework if recent graduate",
                        "Add certifications and professional development",
                        "Include GPA if 3.5 or higher"
                    ],
                    examples=[
                        "Bachelor of Science in Computer Science",
                        "University of Technology | 2020",
                        "Relevant Coursework: Data Structures, Algorithms, Database Systems"
                    ]
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

    def generate_summary_report(
        self, 
        comprehensive_report: Dict[str, Any],
        level: RecommendationLevel = "normal"
    ) -> str:
        """Generate a human-readable summary report"""
        score = comprehensive_report["overall_score"]
        grade = comprehensive_report["grade"]
        rec_level = comprehensive_report.get("recommendation_level", "normal")
        llm_enhanced = comprehensive_report.get("llm_enhanced", False)

        summary = f"""
ATS RESUME SCORE REPORT
=======================

Overall Score: {score}/100 (Grade: {grade})
ATS Compatibility: {comprehensive_report['ats_compatibility']['status']}
Recommendation Level: {rec_level.title()}
{"✨ AI-Enhanced Recommendations" if llm_enhanced else "📋 Standard Recommendations"}

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
  
RECOMMENDATIONS ({rec_level.upper()} LEVEL):
"""

        recommendations = comprehensive_report["recommendations"]
        rec_count = min(5 if level == "concise" else 8 if level == "normal" else len(recommendations), len(recommendations))
        
        for i, rec in enumerate(recommendations[:rec_count], 1):
            summary += f"  {i}. {rec}\n"

        if level == "detailed" and "detailed_recommendations" in comprehensive_report:
            summary += f"\nDETAILED ACTION PLANS:\n"
            for i, detailed_rec in enumerate(comprehensive_report["detailed_recommendations"][:3], 1):
                summary += f"\n{i}. {detailed_rec['message']}\n"
                if detailed_rec.get("action_steps"):
                    summary += "   Action Steps:\n"
                    for step in detailed_rec["action_steps"][:3]:
                        summary += f"   • {step}\n"

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
        level = report.get("recommendation_level", "normal")
        summary = self.generate_summary_report(report, level)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(summary)