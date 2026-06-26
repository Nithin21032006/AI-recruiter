from pydantic import BaseModel, Field
from typing import List, Optional

class SalaryRange(BaseModel):
    min: float = 0.0
    max: float = 0.0
    currency: str = "INR"

class JobDescription(BaseModel):
    id: str
    title: str
    company: str
    description: str
    years_required: float = 0.0
    experience_level: Optional[str] = ""
    location: Optional[str] = ""
    job_type: Optional[str] = ""
    education: Optional[str] = ""
    required_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    salary_range: Optional[SalaryRange] = None
    posted_date: Optional[str] = None
    deadline: Optional[str] = None
    raw_text: str = ""

    def get_all_skills(self) -> List[str]:
        return list(set(self.required_skills + self.nice_to_have_skills))
