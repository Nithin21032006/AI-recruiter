from models.candidate import Candidate, CandidateProfile
from typing import Dict, Any, List

class CandidateProfiler:
    def profile(self, candidate: Candidate) -> CandidateProfile:
        total_years = candidate.get_total_experience_years()
        skills = candidate.get_skill_names()
        
        # Soft skills detection
        soft_skills = []
        resume_text = (candidate.summary or "") + " " + (candidate.raw_resume or "")
        for exp in candidate.experience:
            resume_text += " " + (exp.description or "")
        resume_text_lower = resume_text.lower()
        
        soft_skill_keywords = {
            "leadership": ["lead", "manage", "mentor", "guide", "leadership"],
            "communication": ["write", "present", "talk", "communication", "report"],
            "problem_solving": ["solve", "optimize", "fix", "troubleshoot", "problem-solving"],
            "collaboration": ["collaborate", "team", "partner", "share", "cooperate"],
            "project_management": ["manage", "project", "schedule", "deliver", "milestone"]
        }
        for skill, kw_list in soft_skill_keywords.items():
            if any(kw in resume_text_lower for kw in kw_list):
                soft_skills.append(skill)
                
        # Profile completeness
        completeness = 0
        if candidate.name: completeness += 20
        if candidate.email: completeness += 10
        if candidate.skills: completeness += 30
        if candidate.experience: completeness += 30
        if candidate.education: completeness += 10
        
        # Strengths
        strengths = []
        if total_years > 5.0:
            strengths.append(f"Experienced professional with {total_years:.1f} years of tenure.")
        if len(skills) > 10:
            strengths.append(f"Broad skill portfolio with {len(skills)} unique skills.")
        if soft_skills:
            strengths.append(f"Demonstrates soft skills in: {', '.join(soft_skills)}.")

        # --- Calculate custom scoring dimensions ---
        # 1. Leadership Score
        leadership = 50.0
        lead_words = ["lead", "manager", "mentor", "vp", "director", "head", "founder", "architect", "team lead"]
        for word in lead_words:
            if word in resume_text_lower:
                leadership += 5.0
        for exp in candidate.experience:
            title_lower = (exp.title or "").lower()
            if any(w in title_lower for w in ["lead", "manager", "director", "head", "founder"]):
                leadership += 10.0
        leadership_score = min(100.0, max(0.0, leadership))

        # 2. Learning Score
        learning = 60.0
        learning += min(15.0, len(candidate.skills) * 0.5)
        learning += min(15.0, len(candidate.certifications) * 5.0)
        learning += min(10.0, len(candidate.education) * 3.0)
        learning_score = min(100.0, max(0.0, learning))

        # 3. Project Complexity Score
        complexity = 50.0
        complexity_words = ["architecture", "infrastructure", "distributed", "kubernetes", "scale", "performance", "optimization", "million", "billion", "pipeline", "platform", "redesign"]
        for word in complexity_words:
            if word in resume_text_lower:
                complexity += 4.0
        expert_count = sum(1 for s in candidate.skills if (s.proficiency or "").lower() in ["expert", "advanced"])
        complexity += min(15.0, expert_count * 2.0)
        project_complexity_score = min(100.0, max(0.0, complexity))

        # 4. Career Growth Score
        growth = 50.0
        signals = candidate.redrob_signals or {}
        endorsements = signals.get("endorsements_received", 0)
        growth += min(15.0, endorsements * 0.5)
        if len(candidate.experience) > 1:
            early_title = (candidate.experience[-1].title or "").lower()
            recent_title = (candidate.experience[0].title or "").lower()
            if "senior" in recent_title and "senior" not in early_title:
                growth += 15.0
            elif "lead" in recent_title and "lead" not in early_title:
                growth += 15.0
        career_growth_score = min(100.0, max(0.0, growth))

        # 5. Communication Score
        comm = 60.0
        if candidate.summary and len(candidate.summary) > 100:
            comm += 15.0
        comm_words = ["communication", "present", "write", "client", "stakeholder", "presentation", "report", "facilitate"]
        for word in comm_words:
            if word in resume_text_lower:
                comm += 3.0
        communication_score = min(100.0, max(0.0, comm))

        # 6. Open Source Score
        github_score = signals.get("github_activity_score", 0.0)
        os_score = 30.0
        if github_score > 0:
            os_score += min(50.0, github_score * 0.5)
        if "open source" in resume_text_lower or "open-source" in resume_text_lower:
            os_score += 15.0
        if "github" in resume_text_lower:
            os_score += 5.0
        open_source_score = min(100.0, max(0.0, os_score))

        # 7. Consistency Score
        consistency = 50.0
        completeness_signal = signals.get("profile_completeness_score", 70.0)
        consistency += completeness_signal * 0.3
        if len(candidate.experience) > 0:
            avg_tenure = total_years / len(candidate.experience)
            if avg_tenure >= 2.0:
                consistency += 15.0
            elif avg_tenure >= 1.0:
                consistency += 10.0
        consistency_score = min(100.0, max(0.0, consistency))

        # Calculate normalized profile score
        normalized_score = (
            leadership_score + learning_score + project_complexity_score + 
            career_growth_score + communication_score + open_source_score + 
            consistency_score
        ) / 7.0
            
        return CandidateProfile(
            candidate_id=candidate.id,
            name=candidate.name or "Anonymized",
            skills_analysis=self.analyze_skills(candidate),
            experience_analysis=self.analyze_experience(candidate),
            soft_skills=soft_skills,
            profile_completeness=self.calculate_profile_completeness(candidate),
            strengths=strengths,
            certifications=candidate.certifications,
            education_count=len(candidate.education),
            leadership_score=leadership_score,
            learning_score=learning_score,
            project_complexity_score=project_complexity_score,
            career_growth_score=career_growth_score,
            communication_score=communication_score,
            open_source_score=open_source_score,
            consistency_score=consistency_score,
            normalized_score=normalized_score
        )

    def analyze_skills(self, candidate: Candidate) -> Dict[str, Any]:
        skills = candidate.get_skill_names()
        prof_dist = {}
        expert_skills = []
        advanced_skills = []
        for s in candidate.skills:
            prof = (s.proficiency or "intermediate").lower()
            prof_dist[prof] = prof_dist.get(prof, 0) + 1
            if prof == "expert":
                expert_skills.append(s.name)
            elif prof == "advanced":
                advanced_skills.append(s.name)
        return {
            "total_skills": len(skills),
            "skills": skills,
            "proficiency_distribution": prof_dist,
            "expert_skills": expert_skills,
            "advanced_skills": advanced_skills
        }

    def analyze_experience(self, candidate: Candidate) -> Dict[str, Any]:
        total_years = candidate.get_total_experience_years()
        return {
            "total_years": total_years,
            "total_positions": len(candidate.experience),
            "average_tenure": total_years / max(1, len(candidate.experience)),
            "experience_progression": "Growing" if len(candidate.experience) > 1 else "Stable",
            "current_role": candidate.experience[0].title if candidate.experience else "",
            "current_company": candidate.experience[0].company if candidate.experience else ""
        }

    def assess_soft_skills(self, candidate: Candidate) -> List[str]:
        soft_skills = []
        resume_text = (candidate.summary or "") + " " + (candidate.raw_resume or "")
        for exp in candidate.experience:
            resume_text += " " + (exp.description or "")
        resume_text_lower = resume_text.lower()
        soft_skill_keywords = {
            "leadership": ["lead", "manage", "mentor", "guide", "leadership"],
            "communication": ["write", "present", "talk", "communication", "report"],
            "problem_solving": ["solve", "optimize", "fix", "troubleshoot", "problem-solving"],
            "collaboration": ["collaborate", "team", "partner", "share", "cooperate"],
            "project_management": ["manage", "project", "schedule", "deliver", "milestone"]
        }
        for skill, kw_list in soft_skill_keywords.items():
            if any(kw in resume_text_lower for kw in kw_list):
                soft_skills.append(skill)
        return soft_skills

    def calculate_profile_completeness(self, candidate: Candidate) -> Dict[str, Any]:
        completeness = 0
        if candidate.name: completeness += 20
        if candidate.email: completeness += 10
        if candidate.skills: completeness += 30
        if candidate.experience: completeness += 30
        if candidate.education: completeness += 10
        return {
            "percentage": completeness,
            "level": "Excellent" if completeness > 80 else "Good" if completeness > 50 else "Fair"
        }

    def identify_strengths(self, candidate: Candidate) -> List[str]:
        total_years = candidate.get_total_experience_years()
        skills = candidate.get_skill_names()
        strengths = []
        if total_years > 5.0:
            strengths.append(f"Experienced professional with {total_years:.1f} years of tenure.")
        if len(skills) > 10:
            strengths.append(f"Broad skill portfolio with {len(skills)} unique skills.")
        return strengths
