from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from models.job_description import JobDescription
from models.candidate import Candidate
from pipeline import RecruitmentPipeline

app = FastAPI(title="Redrob AI Talent Intelligence API")

@app.get("/health")
def health():
    return {"status": "healthy"}

class MatchRequest(BaseModel):
    job_description: JobDescription
    candidates: List[Candidate]
    weights: Optional[Dict[str, float]] = None
    check_bias: Optional[bool] = True

@app.post("/api/v1/match")
def match(req: MatchRequest):
    pipeline = RecruitmentPipeline(weights=req.weights)
    batch = pipeline.match_candidates(
        req.job_description,
        req.candidates,
        check_bias=req.check_bias
    )
    return batch

@app.post("/api/v1/jobs/analyze")
def analyze_job(job: JobDescription):
    pipeline = RecruitmentPipeline()
    return pipeline.job_analyzer.analyze(job)

@app.post("/api/v1/candidates/profile")
def profile_candidate(candidate: Candidate):
    pipeline = RecruitmentPipeline()
    return pipeline.candidate_profiler.profile(candidate)

@app.get("/api/v1/metrics")
def get_metrics():
    pipeline = RecruitmentPipeline()
    return pipeline.get_pipeline_metrics()

# --- New Endpoints ---

class CompareRequest(BaseModel):
    candidate_a: Candidate
    candidate_b: Candidate
    job_description: JobDescription

@app.post("/api/v1/candidates/compare")
def compare_candidates(req: CompareRequest):
    pipeline = RecruitmentPipeline()
    # Compute ranking results for both to get overall_score, behaviour_score, growth_score etc.
    r1 = pipeline.ranking_engine.score_candidate_for_hackathon(req.candidate_a, req.job_description)
    r2 = pipeline.ranking_engine.score_candidate_for_hackathon(req.candidate_b, req.job_description)
    return pipeline.comparison_engine.compare_candidates(
        req.candidate_a, r1,
        req.candidate_b, r2,
        req.job_description
    )

class ExplainRequest(BaseModel):
    candidate: Candidate
    job_description: JobDescription

@app.post("/api/v1/candidates/explain")
def explain_candidate(req: ExplainRequest):
    pipeline = RecruitmentPipeline()
    r = pipeline.ranking_engine.score_candidate_for_hackathon(req.candidate, req.job_description)
    pipeline.explanation_engine.explain_candidate(req.candidate, r, req.job_description)
    
    # Run skill gap analysis too
    gaps = pipeline.skill_gap_analyzer.analyze_gaps(req.candidate, req.job_description)
    return {
        "ranking_result": r,
        "skill_gaps": gaps
    }

class QuestionsRequest(BaseModel):
    candidate: Candidate
    job_description: JobDescription
    count: Optional[int] = 5

@app.post("/api/v1/candidates/questions")
def generate_questions(req: QuestionsRequest):
    pipeline = RecruitmentPipeline()
    return pipeline.question_generator.generate_questions(
        req.candidate,
        req.job_description,
        count=req.count or 5
    )
