# web_api.py
"""
Enhanced FastAPI web interface for the ATS Resume Scorer with LLM integration
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import tempfile
import os
from typing import Optional, List
import uvicorn
import logging
from pathlib import Path
from pydantic import BaseModel

# Import from our package
from ats_resume_scorer.main import ATSResumeScorer
from ats_resume_scorer.scoring.scoring_engine import ScoringWeights
from ats_resume_scorer.utils.report_generator import LLMConfig, RecommendationLevel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enhanced ATS Resume Scorer API",
    description="AI-powered API for scoring resumes against job descriptions using ATS standards",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scorer instance
scorer = None

# Pydantic models for request/response
class LLMConfigModel(BaseModel):
    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 500
    temperature: float = 0.7

class ScoringRequest(BaseModel):
    job_description: str
    recommendation_level: RecommendationLevel = "normal"
    llm_config: Optional[LLMConfigModel] = None
    custom_weights: Optional[dict] = None

class BatchScoringRequest(BaseModel):
    job_description: str
    recommendation_level: RecommendationLevel = "concise"
    llm_config: Optional[LLMConfigModel] = None
    custom_weights: Optional[dict] = None
    max_workers: int = 4

def get_scorer():
    """Dependency to get scorer instance"""
    global scorer
    if scorer is None:
        scorer = ATSResumeScorer()
    return scorer

def create_scorer_with_config(
    llm_config: Optional[LLMConfigModel] = None,
    custom_weights: Optional[dict] = None,
    skills_db_path: Optional[str] = None
) -> ATSResumeScorer:
    """Create scorer with custom configuration"""
    
    # Parse weights
    weights = None
    if custom_weights:
        try:
            weights = ScoringWeights(**custom_weights)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid weights: {str(e)}")
    
    # Parse LLM config
    parsed_llm_config = None
    if llm_config and llm_config.enabled:
        api_key = os.getenv("ATS_LLM_API_KEY")
        if not api_key:
            logger.warning("LLM enabled but no API key found")
        else:
            parsed_llm_config = LLMConfig(
                enabled=True,
                provider=llm_config.provider,
                model=llm_config.model,
                api_key=api_key,
                max_tokens=llm_config.max_tokens,
                temperature=llm_config.temperature
            )
    
    return ATSResumeScorer(
        weights=weights,
        skills_db_path=skills_db_path,
        llm_config=parsed_llm_config
    )

@app.on_event("startup")
async def startup_event():
    """Initialize scorer on startup"""
    global scorer
    try:
        scorer = ATSResumeScorer()
        logger.info("ATS Resume Scorer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize scorer: {e}")
        raise

@app.get("/", response_class=HTMLResponse)
async def root():
    """Enhanced web interface with LLM integration"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced ATS Resume Scorer</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 900px; margin: 0 auto; padding: 20px;
                background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                margin-top: 20px; margin-bottom: 20px;
            }
            h1 { 
                color: #333; text-align: center; margin-bottom: 10px;
                font-size: 2.5em; font-weight: 300;
            }
            .subtitle { 
                text-align: center; color: #666; margin-bottom: 30px;
                font-size: 1.1em;
            }
            .form-group { margin: 25px 0; }
            label { 
                display: block; margin-bottom: 8px; font-weight: 600; 
                color: #555; font-size: 0.95em;
            }
            input, textarea, select, button { 
                width: 100%; padding: 12px; margin: 5px 0; border-radius: 8px;
                border: 2px solid #e1e8ed; font-size: 14px; transition: all 0.3s ease;
            }
            input:focus, textarea:focus, select:focus {
                outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            button { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; border: none; cursor: pointer; font-weight: 600;
                text-transform: uppercase; letter-spacing: 0.5px; padding: 15px;
            }
            button:hover { 
                transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            button:disabled {
                background: #ccc; cursor: not-allowed; transform: none; box-shadow: none;
            }
            .result { 
                background: #f8fafe; padding: 25px; margin: 25px 0; border-radius: 12px;
                border-left: 5px solid #667eea; box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }
            .score-display {
                text-align: center; margin: 20px 0;
            }
            .score-number {
                font-size: 3em; font-weight: bold; color: #667eea;
            }
            .score-grade {
                font-size: 1.5em; color: #764ba2; font-weight: 600;
            }
            .breakdown-grid {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px; margin: 20px 0;
            }
            .breakdown-item {
                background: white; padding: 15px; border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            .breakdown-score {
                font-size: 1.3em; font-weight: bold; color: #333;
            }
            .recommendations {
                background: white; padding: 20px; border-radius: 8px;
                margin: 15px 0; border-left: 4px solid #ffa726;
            }
            .recommendation-item {
                margin: 10px 0; padding: 10px; background: #fff3e0; border-radius: 6px;
            }
            .toggle-section {
                margin: 20px 0; padding: 15px; background: #f5f7fa; border-radius: 8px;
            }
            .checkbox-group {
                display: flex; align-items: center; margin: 10px 0;
            }
            .checkbox-group input[type="checkbox"] {
                width: auto; margin-right: 10px;
            }
            .level-buttons {
                display: flex; gap: 10px; margin: 10px 0;
            }
            .level-btn {
                flex: 1; padding: 8px; border: 2px solid #e1e8ed; background: white;
                color: #666; border-radius: 6px; cursor: pointer; transition: all 0.3s;
            }
            .level-btn.active {
                border-color: #667eea; background: #667eea; color: white;
            }
            .loading {
                text-align: center; color: #667eea; font-weight: 600;
            }
            .error {
                color: #e74c3c; background: #fdf2f2; padding: 15px; border-radius: 8px;
            }
            @media (max-width: 768px) {
                .container { margin: 10px; padding: 15px; }
                h1 { font-size: 2em; }
                .breakdown-grid { grid-template-columns: 1fr; }
                .level-buttons { flex-direction: column; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Enhanced ATS Resume Scorer</h1>
            <p class="subtitle">AI-powered resume optimization with detailed recommendations</p>
            
            <form id="scoreForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label>📄 Resume File:</label>
                    <input type="file" id="resume" name="resume" accept=".pdf,.docx,.txt" required>
                    <small style="color: #666;">Supported formats: PDF, DOCX, TXT (max 10MB)</small>
                </div>
                
                <div class="form-group">
                    <label>📋 Job Description:</label>
                    <textarea id="jobDescription" name="jobDescription" rows="8" 
                              placeholder="Paste the complete job description here..." required></textarea>
                </div>
                
                <div class="form-group">
                    <label>🎯 Recommendation Level:</label>
                    <div class="level-buttons">
                        <button type="button" class="level-btn" data-level="concise">Concise</button>
                        <button type="button" class="level-btn active" data-level="normal">Normal</button>
                        <button type="button" class="level-btn" data-level="detailed">Detailed</button>
                    </div>
                    <input type="hidden" id="recommendationLevel" value="normal">
                </div>
                
                <div class="toggle-section">
                    <div class="checkbox-group">
                        <input type="checkbox" id="enableLLM">
                        <label for="enableLLM">✨ Enable AI-Enhanced Recommendations</label>
                    </div>
                    <small style="color: #666;">Requires API key configuration on server</small>
                    
                    <div id="llmOptions" style="display: none; margin-top: 15px;">
                        <div class="form-group">
                            <label>🤖 AI Provider:</label>
                            <select id="llmProvider">
                                <option value="openai">OpenAI (GPT)</option>
                                <option value="anthropic">Anthropic (Claude)</option>
                                <option value="gemini">Google (Gemini)</option>
                                <option value="local">Local Model</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>🧠 Model:</label>
                            <input type="text" id="llmModel" value="gpt-3.5-turbo" placeholder="Model name">
                        </div>
                    </div>
                </div>
                
                <button type="submit" id="submitBtn">🔍 Analyze Resume</button>
            </form>
            
            <div id="result" class="result" style="display:none;"></div>
        </div>

        <script>
            // Level button handling
            document.querySelectorAll('.level-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.level-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    document.getElementById('recommendationLevel').value = this.dataset.level;
                });
            });
            
            // LLM options toggle
            document.getElementById('enableLLM').addEventListener('change', function() {
                document.getElementById('llmOptions').style.display = this.checked ? 'block' : 'none';
            });
            
            // Form submission
            document.getElementById('scoreForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const submitBtn = document.getElementById('submitBtn');
                const resultDiv = document.getElementById('result');
                
                // Disable form and show loading
                submitBtn.disabled = true;
                submitBtn.textContent = '🔄 Analyzing...';
                resultDiv.innerHTML = '<div class="loading">🧠 AI is analyzing your resume... This may take a moment.</div>';
                resultDiv.style.display = 'block';
                
                const formData = new FormData();
                formData.append('resume_file', document.getElementById('resume').files[0]);
                formData.append('job_description', document.getElementById('jobDescription').value);
                formData.append('recommendation_level', document.getElementById('recommendationLevel').value);
                
                // Add LLM config if enabled
                if (document.getElementById('enableLLM').checked) {
                    formData.append('enable_llm', 'true');
                    formData.append('llm_provider', document.getElementById('llmProvider').value);
                    formData.append('llm_model', document.getElementById('llmModel').value);
                }
                
                try {
                    const response = await fetch('/score-resume/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        displayResults(data.result);
                    } else {
                        resultDiv.innerHTML = `<div class="error">❌ Error: ${data.detail}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                } finally {
                    // Re-enable form
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🔍 Analyze Resume';
                }
            });
            
            function displayResults(result) {
                const level = result.recommendation_level || 'normal';
                const llmEnhanced = result.llm_enhanced || false;
                
                let html = `
                    <div class="score-display">
                        <div class="score-number">${result.overall_score.toFixed(1)}/100</div>
                        <div class="score-grade">Grade: ${result.grade}</div>
                        <div style="margin: 10px 0; color: #666;">
                            ATS Compatibility: <strong>${result.ats_compatibility.status}</strong>
                            ${llmEnhanced ? '<br>✨ <strong>AI-Enhanced Analysis</strong>' : ''}
                        </div>
                    </div>
                    
                    <h3>📊 Detailed Breakdown</h3>
                    <div class="breakdown-grid">
                `;
                
                for (const [category, score] of Object.entries(result.detailed_breakdown)) {
                    const categoryName = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    const color = score >= 80 ? '#4caf50' : score >= 60 ? '#ff9800' : '#f44336';
                    const icon = score >= 80 ? '🟢' : score >= 60 ? '🟡' : '🔴';
                    
                    html += `
                        <div class="breakdown-item">
                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                <span style="margin-right: 8px;">${icon}</span>
                                <strong>${categoryName}</strong>
                            </div>
                            <div class="breakdown-score" style="color: ${color};">${score.toFixed(1)}/100</div>
                        </div>
                    `;
                }
                
                html += `</div>`;
                
                // Job match analysis
                const match = result.job_match_analysis;
                html += `
                    <h3>🎯 Job Match Analysis</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div class="breakdown-item">
                            <strong>Required Skills</strong><br>
                            ${match.required_skills_matched}/${match.required_skills_total} 
                            (${match.required_match_percentage.toFixed(1)}%)
                        </div>
                        <div class="breakdown-item">
                            <strong>Preferred Skills</strong><br>
                            ${match.preferred_skills_matched}/${match.preferred_skills_total} 
                            (${match.preferred_match_percentage.toFixed(1)}%)
                        </div>
                    </div>
                `;
                
                // Missing skills
                if (match.missing_required_skills.length > 0) {
                    html += `
                        <div style="margin: 15px 0; padding: 15px; background: #fff3e0; border-radius: 8px;">
                            <strong>❌ Missing Required Skills:</strong><br>
                            ${match.missing_required_skills.slice(0, 10).join(', ')}
                            ${match.missing_required_skills.length > 10 ? ` (and ${match.missing_required_skills.length - 10} more)` : ''}
                        </div>
                    `;
                }
                
                // Recommendations
                html += `<h3>💡 Recommendations (${level.toUpperCase()} Level)</h3>`;
                const recCount = level === 'concise' ? 3 : level === 'normal' ? 5 : result.recommendations.length;
                
                if (level === 'detailed' && result.detailed_recommendations) {
                    // Show detailed recommendations
                    result.detailed_recommendations.slice(0, recCount).forEach((rec, i) => {
                        html += `
                            <div class="recommendation-item">
                                <strong>${i + 1}. ${rec.message}</strong><br>
                                <small>Category: ${rec.category} | Priority: ${rec.priority}</small>
                                ${rec.detailed_explanation ? `<br><em>${rec.detailed_explanation}</em>` : ''}
                                ${rec.action_steps && rec.action_steps.length > 0 ? 
                                    `<br><strong>Action Steps:</strong><ul>${rec.action_steps.slice(0, 3).map(step => `<li>${step}</li>`).join('')}</ul>` : ''}
                                ${rec.examples && rec.examples.length > 0 ? 
                                    `<br><strong>Examples:</strong><ul>${rec.examples.slice(0, 2).map(ex => `<li>${ex}</li>`).join('')}</ul>` : ''}
                            </div>
                        `;
                    });
                } else {
                    // Show normal recommendations
                    result.recommendations.slice(0, recCount).forEach((rec, i) => {
                        html += `<div class="recommendation-item">${i + 1}. ${rec}</div>`;
                    });
                }
                
                // Improvement potential
                if (result.improvement_potential) {
                    const improvement = result.improvement_potential;
                    html += `
                        <h3>📈 Improvement Potential</h3>
                        <div class="breakdown-item">
                            <strong>Current Score:</strong> ${improvement.current_score.toFixed(1)}/100<br>
                            <strong>Potential Score:</strong> ${improvement.max_possible_score.toFixed(1)}/100<br>
                            <strong>Possible Gain:</strong> +${improvement.total_potential_gain.toFixed(1)} points
                        </div>
                    `;
                }
                
                document.getElementById('result').innerHTML = html;
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/score-resume/")
async def score_resume(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    recommendation_level: RecommendationLevel = Form("normal"),
    enable_llm: Optional[str] = Form(None),
    llm_provider: Optional[str] = Form("openai"),
    llm_model: Optional[str] = Form("gpt-3.5-turbo"),
    llm_max_tokens: Optional[int] = Form(500),
    llm_temperature: Optional[float] = Form(0.7),
    keyword_weight: Optional[float] = Form(0.30),
    title_weight: Optional[float] = Form(0.10),
    education_weight: Optional[float] = Form(0.10),
    experience_weight: Optional[float] = Form(0.15),
    format_weight: Optional[float] = Form(0.15),
    grammar_weight: Optional[float] = Form(0.10),
    readability_weight: Optional[float] = Form(0.10),
):
    """
    Enhanced resume scoring endpoint with LLM integration
    """
    
    # Validate weights
    total_weight = (keyword_weight + title_weight + education_weight + 
                   experience_weight + format_weight + grammar_weight + readability_weight)
    
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=400, 
            detail=f"Weights must sum to 1.0, got {total_weight:.3f}"
        )
    
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    file_extension = os.path.splitext(resume_file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (10MB limit)
    if resume_file.size and resume_file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum size is 10MB."
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        try:
            content = await resume_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    try:
        # Create custom weights if different from defaults
        weights = None
        if not all([
            keyword_weight == 0.30,
            title_weight == 0.10,
            education_weight == 0.10,
            experience_weight == 0.15,
            format_weight == 0.15,
            grammar_weight == 0.10,
            readability_weight == 0.10
        ]):
            weights = ScoringWeights(
                keyword_match=keyword_weight,
                title_match=title_weight,
                education_match=education_weight,
                experience_match=experience_weight,
                format_compliance=format_weight,
                action_verbs_grammar=grammar_weight,
                readability=readability_weight
            )
        
        # Configure LLM if enabled
        llm_config = None
        if enable_llm and enable_llm.lower() == "true":
            api_key = os.getenv("ATS_LLM_API_KEY")
            if api_key:
                llm_config = LLMConfig(
                    enabled=True,
                    provider=llm_provider,
                    model=llm_model,
                    api_key=api_key,
                    max_tokens=llm_max_tokens,
                    temperature=llm_temperature
                )
                logger.info(f"LLM enabled: {llm_provider}/{llm_model}")
            else:
                logger.warning("LLM requested but no API key configured")
        
        # Create scorer with configuration
        scorer = create_scorer_with_config(
            llm_config=LLMConfigModel(
                enabled=llm_config.enabled if llm_config else False,
                provider=llm_config.provider if llm_config else "openai",
                model=llm_config.model if llm_config else "gpt-3.5-turbo",
                max_tokens=llm_config.max_tokens if llm_config else 500,
                temperature=llm_config.temperature if llm_config else 0.7
            ) if llm_config else None,
            custom_weights={
                "keyword_match": keyword_weight,
                "title_match": title_weight,
                "education_match": education_weight,
                "experience_match": experience_weight,
                "format_compliance": format_weight,
                "action_verbs_grammar": grammar_weight,
                "readability": readability_weight
            } if weights else None
        )
        
        # Score resume
        result = scorer.score_resume(tmp_file_path, job_description, recommendation_level)
        
        return JSONResponse(content={
            "status": "success",
            "filename": resume_file.filename,
            "file_size": resume_file.size,
            "recommendation_level": recommendation_level,
            "llm_enhanced": result.get('llm_enhanced', False),
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error processing resume {resume_file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except:
                pass  # Ignore cleanup errors

@app.post("/batch-score/")
async def batch_score_resumes(
    resume_files: List[UploadFile] = File(...),
    request: BatchScoringRequest = Depends()
):
    """
    Score multiple resumes in batch
    """
    if len(resume_files) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 files allowed in batch processing"
        )
    
    # Validate all files first
    temp_files = []
    try:
        for resume_file in resume_files:
            # Validate file type
            allowed_extensions = {'.pdf', '.docx', '.txt'}
            file_extension = os.path.splitext(resume_file.filename)[1].lower()
            
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type in {resume_file.filename}: {file_extension}"
                )
            
            # Validate file size
            if resume_file.size and resume_file.size > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size too large: {resume_file.filename}. Maximum size is 10MB."
                )
            
            # Save temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                content = await resume_file.read()
                tmp_file.write(content)
                temp_files.append({
                    'path': tmp_file.name,
                    'original_name': resume_file.filename,
                    'size': resume_file.size
                })
        
        # Create scorer with configuration
        scorer = create_scorer_with_config(
            llm_config=request.llm_config,
            custom_weights=request.custom_weights
        )
        
        # Process files
        file_paths = [f['path'] for f in temp_files]
        results = scorer.batch_score_resumes(
            file_paths,
            request.job_description,
            request.recommendation_level,
            request.max_workers
        )
        
        # Format results with original filenames
        formatted_results = []
        for i, result in enumerate(results):
            original_file = temp_files[i]
            if result['success']:
                formatted_results.append({
                    "filename": original_file['original_name'],
                    "file_size": original_file['size'],
                    "success": True,
                    "score": result['result']['overall_score'],
                    "grade": result['result']['grade'],
                    "ats_status": result['result']['ats_compatibility']['status'],
                    "llm_enhanced": result['result'].get('llm_enhanced', False),
                    "top_recommendations": result['result']['recommendations'][:3],
                    "result": result['result']
                })
            else:
                formatted_results.append({
                    "filename": original_file['original_name'],
                    "file_size": original_file['size'],
                    "success": False,
                    "error": result['error']
                })
        
        # Sort by score (highest first)
        successful_results = [r for r in formatted_results if r['success']]
        failed_results = [r for r in formatted_results if not r['success']]
        successful_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return JSONResponse(content={
            "status": "success",
            "total_files": len(resume_files),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "recommendation_level": request.recommendation_level,
            "llm_enhanced": request.llm_config.enabled if request.llm_config else False,
            "results": successful_results + failed_results
        })
        
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in batch processing: {str(e)}")
    
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file['path']):
                    os.unlink(temp_file['path'])
            except:
                pass

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Test scorer functionality
        scorer = get_scorer()
        
        # Check LLM availability
        llm_available = bool(os.getenv("ATS_LLM_API_KEY"))
        
        return {
            "status": "healthy", 
            "service": "Enhanced ATS Resume Scorer API",
            "version": "2.0.0",
            "scorer_initialized": scorer is not None,
            "llm_integration": {
                "api_key_configured": llm_available,
                "supported_providers": ["openai", "anthropic", "local"],
                "default_provider": os.getenv("ATS_LLM_PROVIDER", "openai")
            },
            "features": {
                "recommendation_levels": ["concise", "normal", "detailed"],
                "batch_processing": True,
                "custom_weights": True,
                "supported_formats": [".pdf", ".docx", ".txt"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/info")
async def api_info():
    """Enhanced API information endpoint"""
    return {
        "service": "Enhanced ATS Resume Scorer API",
        "version": "2.0.0",
        "description": "AI-powered resume scoring with detailed recommendations",
        "features": {
            "ai_enhanced_recommendations": True,
            "multiple_detail_levels": ["concise", "normal", "detailed"],
            "batch_processing": True,
            "custom_scoring_weights": True,
            "llm_providers": ["openai", "anthropic", "gemini", "local"]
        },
        "endpoints": {
            "/": "GET - Enhanced web interface with AI features",
            "/score-resume/": "POST - Score single resume with AI recommendations",
            "/batch-score/": "POST - Score multiple resumes in batch",
            "/health": "GET - Health check with feature status",
            "/api/info": "GET - API information",
            "/api/default-weights": "GET - Default scoring weights",
            "/api/llm-status": "GET - LLM integration status",
            "/docs": "GET - API documentation (Swagger)",
            "/redoc": "GET - API documentation (ReDoc)"
        },
        "supported_formats": [".pdf", ".docx", ".txt"],
        "max_file_size": "10MB",
        "batch_limit": 20,
        "scoring_categories": [
            "keyword_match",
            "title_match", 
            "education_match",
            "experience_match",
            "format_compliance",
            "action_verbs_grammar",
            "readability"
        ]
    }

@app.get("/api/default-weights")
async def get_default_weights():
    """Get default scoring weights"""
    weights = ScoringWeights()
    return {
        "keyword_match": weights.keyword_match,
        "title_match": weights.title_match,
        "education_match": weights.education_match,
        "experience_match": weights.experience_match,
        "format_compliance": weights.format_compliance,
        "action_verbs_grammar": weights.action_verbs_grammar,
        "readability": weights.readability
    }

@app.get("/api/llm-status")
async def get_llm_status():
    """Get LLM integration status"""
    api_key_configured = bool(os.getenv("ATS_LLM_API_KEY"))
    
    return {
        "enabled": api_key_configured,
        "api_key_configured": api_key_configured,
        "default_provider": os.getenv("ATS_LLM_PROVIDER", "openai"),
        "default_model": os.getenv("ATS_LLM_MODEL", "gpt-3.5-turbo"),
        "supported_providers": {
            "openai": {
                "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                "description": "OpenAI GPT models"
            },
            "anthropic": {
                "models": ["claude-3-sonnet", "claude-3-opus", "claude-3-haiku"],
                "description": "Anthropic Claude models"
            },
            "gemini": {
                "models": ["gemini-pro", "gemini-pro-vision", "gemini-1.5-pro"],
                "description": "Google Gemini models"
            },
            "local": {
                "models": ["custom"],
                "description": "Local or self-hosted models (requires endpoint)"
            }
        },
        "recommendation_levels": {
            "concise": "Brief, actionable recommendations (3-5 items)",
            "normal": "Detailed recommendations with action steps (5-8 items)",
            "detailed": "Comprehensive analysis with examples and explanations (8+ items)"
        }
    }

@app.post("/api/configure-llm")
async def configure_llm(config: LLMConfigModel):
    """
    Configure LLM settings (requires restart to take effect)
    """
    if config.enabled and not os.getenv("ATS_LLM_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="API key required for LLM integration. Set ATS_LLM_API_KEY environment variable."
        )
    
    # In a production environment, you might want to store this in a database
    # For now, we just validate the configuration
    
    return {
        "status": "configuration_validated",
        "message": "LLM configuration is valid. Restart the service to apply changes.",
        "config": {
            "enabled": config.enabled,
            "provider": config.provider,
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }
    }

@app.get("/api/sample-job-descriptions")
async def get_sample_job_descriptions():
    """Get sample job descriptions for testing"""
    return {
        "software_engineer": {
            "title": "Senior Software Engineer - Python",
            "description": """We are seeking a skilled Senior Software Engineer to join our growing team.

Required Skills:
- 5+ years Python development experience
- Experience with Django or Flask frameworks
- SQL database management (PostgreSQL/MySQL)
- RESTful API development
- Git version control
- Agile/Scrum methodology

Preferred Skills:
- AWS cloud services (EC2, S3, RDS)
- Docker containerization
- React.js frontend development
- Test-driven development
- CI/CD pipeline experience

Requirements:
- Bachelor's degree in Computer Science or related field
- 5+ years of software development experience
- Strong problem-solving and communication skills
- Experience leading development teams

Responsibilities:
- Design and develop scalable web applications
- Lead technical discussions and code reviews
- Mentor junior developers
- Collaborate with product and design teams
- Ensure code quality and best practices"""
        },
        "data_scientist": {
            "title": "Data Scientist - Machine Learning",
            "description": """Join our data science team to build innovative ML solutions.

Required Skills:
- 3+ years data science experience
- Python programming (pandas, numpy, scikit-learn)
- Machine learning algorithms and statistics
- SQL and database management
- Data visualization tools

Preferred Skills:
- TensorFlow or PyTorch
- Big data tools (Spark, Hadoop)
- Cloud platforms (AWS, GCP)
- A/B testing experience

Requirements:
- Master's degree in Data Science, Statistics, or related field
- Strong analytical and problem-solving skills
- Experience with production ML systems"""
        },
        "marketing_manager": {
            "title": "Digital Marketing Manager",
            "description": """Lead our digital marketing initiatives and drive growth.

Required Skills:
- 4+ years digital marketing experience
- Google Analytics and Google Ads
- Social media marketing
- Email marketing platforms
- Content marketing strategy

Preferred Skills:
- SEO and SEM optimization
- Marketing automation tools
- A/B testing and conversion optimization
- Project management

Requirements:
- Bachelor's degree in Marketing or related field
- Proven track record of driving growth
- Strong communication and leadership skills"""
        }
    }

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the enhanced FastAPI server"""
    uvicorn.run(
        "web_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced ATS Resume Scorer Web API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--enable-llm", action="store_true", help="Enable LLM integration")
    
    args = parser.parse_args()
    
    if args.enable_llm and not os.getenv("ATS_LLM_API_KEY"):
        print("⚠️  Warning: LLM enabled but ATS_LLM_API_KEY not set")
        print("Set the environment variable with your API key to use AI features")
    
    print(f"🚀 Starting Enhanced ATS Resume Scorer API on http://{args.host}:{args.port}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🌐 Web Interface: http://{args.host}:{args.port}/")
    
    if os.getenv("ATS_LLM_API_KEY"):
        provider = os.getenv("ATS_LLM_PROVIDER", "openai")
        model = os.getenv("ATS_LLM_MODEL", "gpt-3.5-turbo")
        print(f"✨ AI Features: Enabled ({provider}/{model})")
    else:
        print("📊 AI Features: Disabled (set ATS_LLM_API_KEY to enable)")
    
    run_server(host=args.host, port=args.port, reload=args.reload)