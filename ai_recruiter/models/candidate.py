from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Skill(BaseModel):
    name: str
    proficiency: Optional[str] = ""
    years: Optional[float] = 0.0
    duration_months: Optional[float] = 0.0
    endorsements: Optional[int] = 0

class Experience(BaseModel):
    title: Optional[str] = ""
    company: Optional[str] = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_years: Optional[float] = None
    duration_months: Optional[float] = 0.0
    description: Optional[str] = ""
    skills_used: List[str] = Field(default_factory=list)
    is_current: Optional[bool] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None

class Education(BaseModel):
    degree: Optional[str] = ""
    field: Optional[str] = ""
    field_of_study: Optional[str] = ""
    university: Optional[str] = ""
    institution: Optional[str] = ""
    graduation_year: Optional[int] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade: Optional[str] = None
    tier: Optional[str] = None

class Profile(BaseModel):
    anonymized_name: Optional[str] = ""
    headline: Optional[str] = ""
    summary: Optional[str] = ""
    location: Optional[str] = ""
    country: Optional[str] = ""
    years_of_experience: float = 0.0
    current_title: Optional[str] = ""
    current_company: Optional[str] = ""
    current_company_size: Optional[str] = ""
    current_industry: Optional[str] = ""

class Candidate(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[Skill] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[Dict[str, Any]] = Field(default_factory=list)
    languages: List[Dict[str, Any]] = Field(default_factory=list)
    raw_resume: Optional[str] = ""
    
    # JSON structure aliases
    profile: Optional[Profile] = None
    career_history: List[Experience] = Field(default_factory=list)
    redrob_signals: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        if "candidate_id" in data and "id" not in data:
            data["id"] = data["candidate_id"]
        super().__init__(**data)
        if self.profile:
            if not self.name:
                self.name = self.profile.anonymized_name
            if not self.location:
                self.location = self.profile.location
            if not self.summary:
                self.summary = self.profile.summary
        if self.career_history and not self.experience:
            self.experience = self.career_history
        for exp in self.experience:
            if exp.duration_years is None and exp.duration_months is not None:
                exp.duration_years = exp.duration_months / 12.0
            elif exp.duration_months is None and exp.duration_years is not None:
                exp.duration_months = exp.duration_years * 12.0

    def get_total_experience_years(self) -> float:
        if self.profile and self.profile.years_of_experience > 0:
            return self.profile.years_of_experience
        total = 0.0
        for exp in self.experience:
            if exp.duration_years:
                total += exp.duration_years
            elif exp.duration_months:
                total += exp.duration_months / 12.0
        return total

    def get_skill_names(self) -> List[str]:
        return [s.name for s in self.skills]

    def get_skill_proficiency(self, skill_name: str) -> Optional[str]:
        skill_name_lower = skill_name.lower()
        for s in self.skills:
            if s.name.lower() == skill_name_lower:
                return s.proficiency
        return None

    def get_skill_years(self, skill_name: str) -> float:
        skill_name_lower = skill_name.lower()
        for s in self.skills:
            if s.name.lower() == skill_name_lower:
                if s.years:
                    return s.years
                if s.duration_months:
                    return s.duration_months / 12.0
        return 0.0

class CandidateProfile(BaseModel):
    candidate_id: str
    name: Optional[str] = ""
    skills_analysis: Dict[str, Any] = Field(default_factory=dict)
    experience_analysis: Dict[str, Any] = Field(default_factory=dict)
    soft_skills: List[str] = Field(default_factory=list)
    profile_completeness: Dict[str, Any] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    certifications: List[Dict[str, Any]] = Field(default_factory=list)
    education_count: int = 0
    
    # New profiling scores
    leadership_score: float = 0.0
    learning_score: float = 0.0
    project_complexity_score: float = 0.0
    career_growth_score: float = 0.0
    communication_score: float = 0.0
    open_source_score: float = 0.0
    consistency_score: float = 0.0
    normalized_score: float = 0.0

    def __getitem__(self, item):
        return getattr(self, item)

    def __contains__(self, item):
        return hasattr(self, item) or item in self.model_fields


class SkillGapItem(BaseModel):
    name: str
    importance: str
    learning_time: str
    hiring_impact: str


