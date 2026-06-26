from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ScoreBreakdown(BaseModel):
    semantic_similarity: float = 0.0
    skill_match: float = 0.0
    experience_match: float = 0.0
    education_match: float = 0.0
    
    # Extra fields for the new scoring details
    behavior_score: float = 0.0
    growth_score: float = 0.0
    confidence_score: float = 0.0

class BiasAudit(BaseModel):
    gender_coded: Dict[str, int] = Field(default_factory=dict)
    age_bias: int = 0
    prestige_school: int = 0
    detected_biases: List[str] = Field(default_factory=list)
    mitigations_applied: List[str] = Field(default_factory=list)

class RankingResult(BaseModel):
    candidate_id: str
    candidate_name: str
    rank: int = 0
    overall_score: float
    score: float = 0.0
    breakdown: ScoreBreakdown
    bias_audit: BiasAudit = Field(default_factory=BiasAudit)
    match_breakdown: Dict[str, float] = Field(default_factory=dict)
    reasoning: str = ""
    key_strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    bias_flags: List[str] = Field(default_factory=list)
    
    # Explainability & Re-ranking details
    why_selected: str = ""
    weaknesses: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    relevant_projects: List[str] = Field(default_factory=list)
    career_highlights: List[str] = Field(default_factory=list)
    hiring_recommendation: str = ""

    # Hybrid ranking score fields (0-100 scaling)
    semantic_score: float = 0.0
    experience_score: float = 0.0
    skill_score: float = 0.0
    behavior_score: float = 0.0
    education_score: float = 0.0
    growth_score: float = 0.0
    confidence_score: float = 0.0

class RankingBatch(BaseModel):
    job_id: str
    results: List[RankingResult] = Field(default_factory=list)
    total_candidates: int = 0
    timestamp: str = ""
    fairness_score: float = 1.0
    bias_warnings: List[str] = Field(default_factory=list)
