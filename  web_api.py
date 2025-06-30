
# web_api.py (Optional web API module)
"""
Optional FastAPI web interface for the ATS Resume Scorer
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from typing import Optional
import uvicorn

from ats_resume_scorer.main import ATSResumeScorer, ScoringWeights

app = FastAPI(
    title="ATS Resume Scorer API",
    description="API for scoring resumes against job descriptions using ATS standards",
    version="1.0.0"
)

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
    readability_weight: Optional[float] = Form(0.10)
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
            detail=f"Weights must sum to 1.0, got {total_weight}"
        )
    
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    file_extension = os.path.splitext(resume_file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        content = await resume_file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Create custom weights
        weights = ScoringWeights(
            keyword_match=keyword_weight,
            title_match=title_weight,
            education_match=education_weight,
            experience_match=experience_weight,
            format_compliance=format_weight,
            action_verbs_grammar=grammar_weight,
            readability=readability_weight
        )
        
        # Initialize scorer and score resume
        scorer = ATSResumeScorer(weights=weights)
        result = scorer.score_resume(tmp_file_path, job_description)
        
        return JSONResponse(content={
            "status": "success",
            "filename": resume_file.filename,
            "result": result
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ATS Resume Scorer API"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ATS Resume Scorer API",
        "version": "1.0.0",
        "endpoints": {
            "/score-resume/": "POST - Score a resume against job description",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
