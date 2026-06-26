from typing import List, Dict, Any
from models.job_description import JobDescription
from models.candidate import Candidate, SkillGapItem

class SkillGapAnalyzer:
    def __init__(self):
        # Database of standard tech skills with estimated learning times and typical hiring impact
        self.skill_database = {
            "python": {"learning_time": "1 Month", "hiring_impact": "High"},
            "django": {"learning_time": "2 Months", "hiring_impact": "High"},
            "fastapi": {"learning_time": "1 Month", "hiring_impact": "High"},
            "flask": {"learning_time": "1 Month", "hiring_impact": "Medium"},
            "embeddings": {"learning_time": "2 Months", "hiring_impact": "High"},
            "retrieval": {"learning_time": "2 Months", "hiring_impact": "High"},
            "vector databases": {"learning_time": "2 Months", "hiring_impact": "High"},
            "pinecone": {"learning_time": "2 Weeks", "hiring_impact": "High"},
            "weaviate": {"learning_time": "2 Weeks", "hiring_impact": "High"},
            "qdrant": {"learning_time": "2 Weeks", "hiring_impact": "High"},
            "milvus": {"learning_time": "3 Weeks", "hiring_impact": "High"},
            "search": {"learning_time": "3 Months", "hiring_impact": "High"},
            "ranking": {"learning_time": "3 Months", "hiring_impact": "High"},
            "evaluation frameworks": {"learning_time": "2 Months", "hiring_impact": "High"},
            "docker": {"learning_time": "2 Months", "hiring_impact": "Medium"},
            "kubernetes": {"learning_time": "3 Months", "hiring_impact": "High"},
            "aws": {"learning_time": "3 Months", "hiring_impact": "Medium"},
            "gcp": {"learning_time": "3 Months", "hiring_impact": "Medium"},
            "azure": {"learning_time": "3 Months", "hiring_impact": "Medium"},
            "pytorch": {"learning_time": "3 Months", "hiring_impact": "High"},
            "tensorflow": {"learning_time": "3 Months", "hiring_impact": "High"},
            "git": {"learning_time": "1 Week", "hiring_impact": "Medium"},
            "airflow": {"learning_time": "1 Month", "hiring_impact": "Medium"},
            "mlflow": {"learning_time": "1 Month", "hiring_impact": "Medium"}
        }

    def analyze_gaps(self, candidate: Candidate, job: JobDescription) -> List[SkillGapItem]:
        cand_skills = set(s.name.lower() for s in candidate.skills)
        gaps = []

        # Analyze required skills (High Priority)
        for rs in job.required_skills:
            if rs.lower() not in cand_skills:
                info = self._get_skill_info(rs)
                gaps.append(SkillGapItem(
                    name=rs,
                    importance="High Priority",
                    learning_time=info["learning_time"],
                    hiring_impact=info["hiring_impact"]
                ))

        # Analyze nice to have skills (Nice to Have)
        for ps in job.nice_to_have_skills:
            if ps.lower() not in cand_skills:
                info = self._get_skill_info(ps)
                gaps.append(SkillGapItem(
                    name=ps,
                    importance="Nice to Have",
                    learning_time=info["learning_time"],
                    hiring_impact="Medium" if info["hiring_impact"] == "High" else "Low"
                ))

        return gaps

    def _get_skill_info(self, skill_name: str) -> Dict[str, str]:
        name_lower = skill_name.lower()
        for k, v in self.skill_database.items():
            if k in name_lower or name_lower in k:
                return v
        return {"learning_time": "1 Month", "hiring_impact": "Medium"}
