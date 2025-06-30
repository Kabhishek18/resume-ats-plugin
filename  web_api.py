# web_api.py (Fixed with proper imports)
"""
FastAPI web interface for the ATS Resume Scorer
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import tempfile
import os
from typing import Optional
import uvicorn
import logging
from pathlib import Path

# Import from our package
from ats_resume_scorer.main import ATSResumeScorer
from ats_resume_scorer.scoring.scoring_engine import ScoringWeights

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ATS Resume Scorer API",
    description="API for scoring resumes against job descriptions using ATS standards",
    version="1.0.0",
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

def get_scorer():
    """Dependency to get scorer instance"""
    global scorer
    if scorer is None:
        scorer = ATSResumeScorer()
    return scorer

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
    """Root endpoint with simple web interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ATS Resume Scorer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .form-group { margin: 20px 0; }
            input, textarea, button { width: 100%; padding: 10px; margin: 5px 0; }
            button { background: #007bff; color: white; border: none; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ATS Resume Scorer</h1>
            <p>Upload your resume and job description to get an ATS compatibility score.</p>
            
            <form id="scoreForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label>Resume File:</label>
                    <input type="file" id="resume" name="resume" accept=".pdf,.docx,.txt" required>
                </div>
                
                <div class="form-group">
                    <label>Job Description:</label>
                    <textarea id="jobDescription" name="jobDescription" rows="10" 
                              placeholder="Paste the job description here..." required></textarea>
                </div>
                
                <button type="submit">Score Resume</button>
            </form>
            
            <div id="result" class="result" style="display:none;"></div>
        </div>

        <script>
            document.getElementById('scoreForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData();
                formData.append('resume_file', document.getElementById('resume').files[0]);
                formData.append('job_description', document.getElementById('jobDescription').value);
                
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = '<p>Scoring in progress...</p>';
                resultDiv.style.display = 'block';
                
                try {
                    const response = await fetch('/score-resume/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        const result = data.result;
                        resultDiv.innerHTML = `
                            <h3>ATS Score: ${result.overall_score}/100 (Grade: ${result.grade})</h3>
                            <p><strong>ATS Compatibility:</strong> ${result.ats_compatibility.status}</p>
                            
                            <h4>Detailed Breakdown:</h4>
                            <ul>
                                <li>Keyword Match: ${result.detailed_breakdown.keyword_match}/100</li>
                                <li>Title Match: ${result.detailed_breakdown.title_match}/100</li>
                                <li>Education Match: ${result.detailed_breakdown.education_match}/100</li>
                                <li>Experience Match: ${result.detailed_breakdown.experience_match}/100</li>
                                <li>Format Compliance: ${result.detailed_breakdown.format_compliance}/100</li>
                                <li>Action Verbs & Grammar: ${result.detailed_breakdown.action_verbs_grammar}/100</li>
                                <li>Readability: ${result.detailed_breakdown.readability}/100</li>
                            </ul>
                            
                            <h4>Top Recommendations:</h4>
                            <ul>
                                ${result.recommendations.slice(0, 5).map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        `;
                    } else {
                        resultDiv.innerHTML = `<p style="color: red;">Error: ${data.detail}</p>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/score-resume/")
async def score_resume(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    keyword_weight: Optional[float] = Form(0.30),
    title_weight: Optional[float] = Form(0.10),
    education_weight: Optional[float] = Form(0.10),
    experience_weight: Optional[float] = Form(0.15),
    format_weight: Optional[float] = Form(0.15),
    grammar_weight: Optional[float] = Form(0.10),
    readability_weight: Optional[float] = Form(0.10),
    scorer: ATSResumeScorer = Depends(get_scorer)
):
    """
    Score a resume against a job description
    
    - **resume_file**: Resume file (PDF, DOCX, or TXT)
    - **job_description**: Job description text
    - **weights**: Optional custom scoring weights (must sum to 1.0)
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
            scorer = ATSResumeScorer(weights=weights)
        
        # Score resume
        result = scorer.score_resume(tmp_file_path, job_description)
        
        return JSONResponse(content={
            "status": "success",
            "filename": resume_file.filename,
            "file_size": resume_file.size,
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test scorer functionality
        scorer = get_scorer()
        return {
            "status": "healthy", 
            "service": "ATS Resume Scorer API",
            "version": "1.0.0",
            "scorer_initialized": scorer is not None
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "service": "ATS Resume Scorer API",
        "version": "1.0.0",
        "description": "Score resumes against job descriptions using ATS standards",
        "endpoints": {
            "/": "GET - Web interface",
            "/score-resume/": "POST - Score a resume against job description",
            "/health": "GET - Health check",
            "/api/info": "GET - API information",
            "/docs": "GET - API documentation (Swagger)",
            "/redoc": "GET - API documentation (ReDoc)"
        },
        "supported_formats": [".pdf", ".docx", ".txt"],
        "max_file_size": "10MB",
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

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server"""
    uvicorn.run(
        "web_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ATS Resume Scorer Web API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"Starting ATS Resume Scorer API on http://{args.host}:{args.port}")
    print(f"API Documentation: http://{args.host}:{args.port}/docs")
    print(f"Web Interface: http://{args.host}:{args.port}/")
    
    run_server(host=args.host, port=args.port, reload=args.reload)