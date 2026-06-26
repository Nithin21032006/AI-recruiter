import sys
from pathlib import Path

# Add ai_recruiter package directory to Python path
ai_recruiter_dir = Path("c:/Users/nithu/OneDrive/Desktop/AI_Recruiter") / "ai_recruiter"
sys.path.insert(0, str(ai_recruiter_dir))

from models.job_description import JobDescription
from models.candidate import Candidate, Skill, Experience
from core.candidate_profiler import CandidateProfiler
from core.ranking_engine import RankingEngine

job = JobDescription(
    id="jd_001",
    title="Senior Python Developer",
    company="TechCorp",
    description="Looking for experienced Python developer",
    years_required=5,
    required_skills=["Python", "Django"],
    raw_text="Test"
)

candidate = Candidate(
    id="cand_001",
    name="John Doe",
    email="john@example.com",
    skills=[Skill(name="Python", proficiency="Expert", years=7)],
    experience=[
        Experience(
            title="Senior Dev",
            company="Company",
            start_date="2019-01",
            end_date="present",
            duration_years=5,
            description="Senior Dev"
        )
    ]
)

ranking_engine = RankingEngine()
profiler = CandidateProfiler()

c_profile = profiler.profile(candidate)
candidate.profile = c_profile

is_hp = ranking_engine.is_honeypot(candidate)
print(f"Is Honeypot: {is_hp}")

current_role = c_profile.experience_analysis.get('current_role', '')
print(f"Current Role: {current_role}")

title_score = ranking_engine.get_title_score(
    current_role,
    candidate.summary or ""
)
print(f"Title Score: {title_score}")

has_consulting = ranking_engine.has_only_consulting_history(candidate.experience)
print(f"Has Consulting: {has_consulting}")

has_academic = ranking_engine.has_only_academic_history(candidate.experience)
print(f"Has Academic: {has_academic}")
