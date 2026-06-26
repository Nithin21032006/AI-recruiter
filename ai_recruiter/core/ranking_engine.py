import os
from typing import List, Dict, Any, Optional
from models.job_description import JobDescription
from models.candidate import Candidate
from models.ranking_result import RankingResult, ScoreBreakdown, BiasAudit
from core.embedding_engine import EmbeddingEngine
from datetime import datetime

class RankingEngine:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.embedding_engine = EmbeddingEngine()
        
        # Core weights mapping, configurable via env variables or custom dictionary
        env_weights = {
            "semantic_similarity": float(os.environ.get("SEMANTIC_SIMILARITY_WEIGHT", 0.40)),
            "experience_match": float(os.environ.get("EXPERIENCE_MATCH_WEIGHT", 0.20)),
            "skill_match": float(os.environ.get("SKILL_MATCH_WEIGHT", 0.15)),
            "behavior_score": float(os.environ.get("BEHAVIOR_SCORE_WEIGHT", 0.10)),
            "education_score": float(os.environ.get("EDUCATION_MATCH_WEIGHT", 0.10)),
            "growth_score": float(os.environ.get("GROWTH_SCORE_WEIGHT", 0.05))
        }
        
        # Use passed weights or fallback to environment weights
        input_weights = weights or env_weights
        
        # Align naming keys (e.g. skill_match vs skill_score)
        self.weights = {}
        key_mappings = {
            "semantic_similarity": ["semantic_similarity", "semantic_score"],
            "experience_match": ["experience_match", "experience_score"],
            "skill_match": ["skill_match", "skill_score"],
            "behavior_score": ["behavior_score", "behavior_match"],
            "education_score": ["education_score", "education_match", "education"],
            "growth_score": ["growth_score", "growth_potential"]
        }
        
        for std_key, aliases in key_mappings.items():
            val = None
            for alias in aliases:
                if alias in input_weights:
                    val = input_weights[alias]
                    break
            if val is not None:
                self.weights[std_key] = float(val)
            else:
                # Fallback to default/env values
                self.weights[std_key] = env_weights[std_key]
                
        # Normalize weights to sum to 1.0
        total_w = sum(self.weights.values())
        if total_w > 0:
            self.weights = {k: v / total_w for k, v in self.weights.items()}

    def is_honeypot(self, c: Candidate) -> bool:
        current_date = datetime(2026, 6, 23)
        profile = c.profile or c
        career = c.career_history or c.experience
        skills = c.skills or []
        signals = c.redrob_signals or {}
        
        # 1. Dates contradiction in career history
        for job in career:
            start_str = job.start_date
            end_str = job.end_date
            duration = job.duration_months or 0.0
            
            if not start_str:
                continue
            try:
                s_yr, s_mo = map(int, start_str.split("-")[:2])
                start_dt = datetime(s_yr, s_mo, 1)
                
                if end_str and end_str.lower() != 'present':
                    e_yr, e_mo = map(int, end_str.split("-")[:2])
                    end_dt = datetime(e_yr, e_mo, 1)
                else:
                    end_dt = current_date
                    
                elapsed_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1
                if duration > elapsed_months + 1:
                    return True
            except Exception:
                pass
                
        # 2. Skill duration anomalies
        profile_years = getattr(profile, 'years_of_experience', 0.0) or 0.0
        total_career_months = sum(job.duration_months or 0.0 for job in career)
        
        for s in skills:
            prof = (s.proficiency or '').lower()
            dur = s.duration_months or 0.0
            if dur == 0.0 and getattr(s, 'years', 0.0):
                dur = getattr(s, 'years', 0.0) * 12.0
            if (prof == 'expert' or prof == 'advanced') and dur == 0:
                return True
            if profile_years > 0 and dur > (profile_years * 12 + 48):
                return True
            if total_career_months > 0 and dur > (total_career_months + 24):
                return True
                
        # 3. Sum of career durations exceed profile experience
        career_years = total_career_months / 12.0
        if profile_years > 0.0:
            if career_years > profile_years + 2.0:
                return True
            if profile_years > 3.0 and career_years < profile_years * 0.4:
                return True
            
        # 4. Expected salary range min > max
        sal = signals.get("expected_salary_range_inr_lpa", {}) or {}
        if sal.get("min", 0.0) > sal.get("max", 0.0):
            return True
            
        # 5. Signup date is after last active date
        signup_str = signals.get("signup_date")
        active_str = signals.get("last_active_date")
        if signup_str and active_str:
            try:
                s_dt = datetime.strptime(signup_str.split("T")[0], "%Y-%m-%d")
                a_dt = datetime.strptime(active_str.split("T")[0], "%Y-%m-%d")
                if s_dt > a_dt:
                    return True
            except Exception:
                pass
                
        # 6. Rates out of bounds
        resp_rate = signals.get("recruiter_response_rate", 0.5)
        if resp_rate < 0.0 or resp_rate > 1.0:
            return True
            
        int_rate = signals.get("interview_completion_rate", 0.5)
        if int_rate < 0.0 or int_rate > 1.0:
            return True
            
        offer_rate = signals.get("offer_acceptance_rate", 0.5)
        if offer_rate != -1.0 and (offer_rate < 0.0 or offer_rate > 1.0):
            return True
            
        return False

    def is_unrelated_role(self, title: str) -> bool:
        unrelated_keywords = [
            "marketing", "graphic designer", "operations manager", "human resources",
            "recruiter", "support", "customer support", "accountant", "sales",
            "content writer", "social media", "product manager", "project manager",
            "scrum master", "business analyst", "finance", "legal", "admin", "executive assistant"
        ]
        title_lower = (title or '').lower()
        return any(kw in title_lower for kw in unrelated_keywords)

    def get_title_score(self, title: str, headline: str) -> float:
        ai_ml_keywords = ["ai", "ml", "machine learning", "nlp", "natural language", "deep learning", "computer vision", "data scientist", "search", "retrieval", "ranking", "recommendation"]
        swe_keywords = ["software engineer", "backend engineer", "fullstack engineer", "full stack", "developer", "data engineer"]
        
        text = f"{title or ''} {headline or ''}".lower()
        if self.is_unrelated_role(title) or self.is_unrelated_role(headline):
            return -100.0
            
        if any(kw in text for kw in ai_ml_keywords):
            return 1.0
        if any(kw in text for kw in swe_keywords):
            return 0.7
        return 0.2

    def has_only_consulting_history(self, career: List[Any]) -> bool:
        consulting_firms = [
            "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
            "tech mahindra", "mindtree", "hcl", "mphasis", "l&t", "ltts", "hexaware", "tata consultancy"
        ]
        if not career:
            return False
        return all(any(firm in (getattr(job, 'company', '') or '').lower() for firm in consulting_firms) for job in career)

    def has_only_academic_history(self, career: List[Any]) -> bool:
        academic_keywords = ["university", "college", "institute", "research assistant", "teaching assistant", "phd student", "postdoc", "phd candidate", "professor"]
        if not career:
            return False
        
        for job in career:
            desc = (getattr(job, 'description', '') or '').lower()
            title = (getattr(job, 'title', '') or '').lower()
            company = (getattr(job, 'company', '') or '').lower()
            
            is_academic = any(kw in company or kw in title or kw in desc for kw in academic_keywords)
            has_production = any(kw in desc for kw in ["deploy", "production", "real user", "scale", "system", "product company"])
            if not (is_academic and not has_production):
                return False
        return True

    def calculate_skill_match(self, candidate: Candidate, required_skills: List[str]) -> float:
        if not required_skills:
            return 1.0
        candidate_skills = set(s.name.lower() for s in candidate.skills)
        matched = candidate_skills.intersection(set(s.lower() for s in required_skills))
        return len(matched) / len(required_skills)

    def calculate_experience_fit(self, candidate: Candidate, job: JobDescription) -> float:
        required_years = job.years_required
        candidate_years = candidate.get_total_experience_years()
        if candidate_years >= required_years:
            return 1.0
        return candidate_years / required_years if required_years > 0 else 1.0

    def calculate_semantic_similarity(self, candidate: Candidate, job: JobDescription) -> float:
        cand_emb = self.embedding_engine.embed_candidate(candidate)
        job_emb = self.embedding_engine.embed_job_description(job)
        return self.embedding_engine.semantic_similarity(cand_emb, job_emb)

    def calculate_education_match(self, candidate: Candidate, job: JobDescription) -> float:
        degrees_hierarchy = {"phd": 4, "doctorate": 4, "master": 3, "m.tech": 3, "m.s": 3, "m.e": 3, "bachelor": 2, "b.tech": 2, "b.e": 2, "b.s": 2, "associate": 1}
        candidate_degrees = [getattr(edu, 'degree', '').lower() for edu in candidate.education if getattr(edu, 'degree', None)]
        job_edu = (job.education or "").lower()
        
        if not job_edu:
            return 1.0
            
        highest_cand = 0
        for deg in candidate_degrees:
            for key, val in degrees_hierarchy.items():
                if key in deg:
                    highest_cand = max(highest_cand, val)
                    break
                    
        highest_job = 0
        for key, val in degrees_hierarchy.items():
            if key in job_edu:
                highest_job = val
                break
                
        if highest_cand >= highest_job and highest_job > 0:
            return 1.0
        elif highest_cand > 0:
            return 0.7
        return 0.5

    def score_candidate_for_hackathon(self, candidate: Candidate, job: JobDescription) -> RankingResult:
        # Calculate individual scores (out of 100)
        semantic_score = self.calculate_semantic_similarity(candidate, job) * 100.0
        experience_score = self.calculate_experience_fit(candidate, job) * 100.0
        skill_score = self.calculate_skill_match(candidate, job.required_skills) * 100.0
        education_score = self.calculate_education_match(candidate, job) * 100.0
        
        # 1. Enhanced Behavior Score (normalized to 100)
        signals = candidate.redrob_signals or {}
        comp_score = signals.get("profile_completeness_score", 70.0) # out of 100
        resp_rate = signals.get("recruiter_response_rate", 0.7) * 100.0 # out of 100
        int_rate = signals.get("interview_completion_rate", 0.7) * 100.0 # out of 100
        
        resume_text_lower = ((candidate.summary or "") + " " + (candidate.raw_resume or "")).lower()
        
        # GitHub & repository metrics
        github_act = max(0.0, float(signals.get("github_activity_score", 0.0)))
        github_points = min(15.0, github_act * 0.15)
        if "github" in resume_text_lower or "commit" in resume_text_lower:
            github_points = max(github_points, 8.0)
            
        # Hackathons
        hackathon_points = 5.0 if "hackathon" in resume_text_lower else 0.0
        
        # Certifications
        cert_points = min(10.0, len(candidate.certifications) * 2.5)
        
        # Learning consistency
        learning_points = 6.0
        if len(candidate.certifications) > 0:
            learning_points += 2.0
        if len(candidate.education) > 1:
            learning_points += 2.0
            
        # Portfolio quality
        portfolio_points = 3.0
        if signals.get("linkedin_connected", False):
            portfolio_points += 2.0
            
        # Leadership & Project Complexity indicators
        lead_points = 0.0
        if any(w in resume_text_lower for w in ["lead", "manager", "mentor", "head", "founder"]):
            lead_points += 5.0
            
        behavior_score = (
            (comp_score * 0.20) +       # max 20
            (resp_rate * 0.15) +        # max 15
            (int_rate * 0.15) +         # max 15
            github_points +             # max 15
            hackathon_points +          # max 5
            cert_points +               # max 10
            learning_points +           # max 10
            portfolio_points +          # max 5
            lead_points                 # max 5
        )
        behavior_score = min(100.0, max(0.0, behavior_score))
        
        # 2. Growth score
        growth = 70.0
        endorsements = signals.get("endorsements_received", 0)
        growth += min(15.0, endorsements * 0.5)
        growth += min(10.0, len(candidate.certifications) * 5.0)
        connections = signals.get("connection_count", 0)
        growth += min(5.0, connections * 0.01)
        growth_score = min(100.0, max(0.0, growth))
        
        # 3. Enhanced Confidence Score (based on Semantic similarity, Experience, Behaviour, Data completeness, and consistency)
        semantic_factor = semantic_score * 0.25
        experience_factor = experience_score * 0.25
        behavior_factor = behavior_score * 0.20
        completeness_factor = comp_score * 0.20
        
        # Consistency is higher if semantic_score and experience_score are aligned (close to each other)
        consistency_diff = abs(semantic_score - experience_score)
        consistency_factor = max(0.0, 10.0 - (consistency_diff * 0.1))
        
        confidence_score = (
            semantic_factor +
            experience_factor +
            behavior_factor +
            completeness_factor +
            consistency_factor
        )
        # Trust signals addition/deductions
        if signals.get("verified_email", False):
            confidence_score += 2.0
        if signals.get("verified_phone", False):
            confidence_score += 2.0
        if signals.get("recruiter_response_rate", 1.0) < 0.2:
            confidence_score -= 8.0
            
        confidence_score = min(100.0, max(0.0, confidence_score))
        
        # Weighted overall score calculation
        w_sem = self.weights.get("semantic_similarity", 0.40)
        w_exp = self.weights.get("experience_match", 0.20)
        w_skills = self.weights.get("skill_match", 0.15)
        w_beh = self.weights.get("behavior_score", 0.10)
        w_edu = self.weights.get("education_score", 0.10)
        w_growth = self.weights.get("growth_score", 0.05)
        
        overall_score = (
            (semantic_score * w_sem) +
            (experience_score * w_exp) +
            (skill_score * w_skills) +
            (behavior_score * w_beh) +
            (education_score * w_edu) +
            (growth_score * w_growth)
        )
        overall_score = min(100.0, max(1.0, overall_score))
        
        reasoning = self._generate_reasoning(candidate, overall_score, semantic_score, experience_score)
        
        # Breakdown values scaled 0 to 1 for backwards compatibility in test cases
        breakdown = ScoreBreakdown(
            semantic_similarity=semantic_score / 100.0,
            skill_match=skill_score / 100.0,
            experience_match=experience_score / 100.0,
            education_match=education_score / 100.0,
            behavior_score=behavior_score / 100.0,
            growth_score=growth_score / 100.0,
            confidence_score=confidence_score / 100.0
        )
        
        return RankingResult(
            candidate_id=candidate.id,
            candidate_name=candidate.name or "Anonymized",
            overall_score=overall_score,
            score=overall_score,
            breakdown=breakdown,
            reasoning=reasoning,
            semantic_score=semantic_score,
            experience_score=experience_score,
            skill_score=skill_score,
            behavior_score=behavior_score,
            education_score=education_score,
            growth_score=growth_score,
            confidence_score=confidence_score
        )


    def rank_candidates(self, candidates: List[Candidate], job: JobDescription, weights: Optional[Dict[str, float]] = None) -> List[RankingResult]:
        old_weights = None
        if weights:
            old_weights = self.weights
            self.weights = {}
            key_mappings = {
                "semantic_similarity": ["semantic_similarity", "semantic_score"],
                "experience_match": ["experience_match", "experience_score"],
                "skill_match": ["skill_match", "skill_score"],
                "behavior_score": ["behavior_score", "behavior_match"],
                "education_score": ["education_score", "education_match", "education"],
                "growth_score": ["growth_score", "growth_potential"]
            }
            for std_key, aliases in key_mappings.items():
                val = None
                for alias in aliases:
                    if alias in weights:
                        val = weights[alias]
                        break
                if val is not None:
                    self.weights[std_key] = float(val)
                else:
                    self.weights[std_key] = 0.0
            
            # Normalize
            total_w = sum(self.weights.values())
            if total_w > 0:
                self.weights = {k: v / total_w for k, v in self.weights.items()}

        results = []
        for candidate in candidates:
            res = self.score_candidate_for_hackathon(candidate, job)
            results.append(res)
            
        if old_weights is not None:
            self.weights = old_weights
            
        results.sort(key=lambda x: (-x.overall_score, x.candidate_id))
        
        for rank, res in enumerate(results, 1):
            res.rank = rank
            
        # Save pre-computed candidate embeddings to disk
        self.embedding_engine.save_candidate_embeddings()
        return results



    def _generate_reasoning(self, c: Candidate, overall_score: float, semantic_score: float, experience_score: float) -> str:
        profile = c.profile or c
        title = getattr(profile, 'current_title', '') or ''
        company = getattr(profile, 'current_company', '') or ''
        years = c.get_total_experience_years()
        location = c.location or ''
        notice = (c.redrob_signals or {}).get("notice_period_days", 0)
        
        parts = []
        if title:
            parts.append(f"{years:.1f} years experience as a {title} at {company}")
        else:
            parts.append(f"Candidate has {years:.1f} years of experience")
            
        skills = c.get_skill_names()
        matching_skills = [s for s in skills if s.lower() in [
            "embeddings", "sentence-transformers", "pinecone", "weaviate", "qdrant", "milvus", "python", "ndcg", "mrr", "map", "rag"
        ]]
        
        if matching_skills:
            parts.append(f"with key skills like {', '.join(matching_skills[:2])}")
        elif skills:
            parts.append(f"skilled in {', '.join(skills[:2])}")
            
        is_pune_noida = 'noida' in location.lower() or 'pune' in location.lower()
        loc_part = f"based in {location}" if is_pune_noida else (
            f"willing to relocate from {location}" if (c.redrob_signals or {}).get("willing_to_relocate", False) else f"located in {location}"
        )
        notice_part = f"notice period is {notice} days" if notice > 0 else 'immediately available'
        parts.append(f"({loc_part}; {notice_part}).")
        
        reason = " ".join(parts)
        if overall_score > 85.0:
            reason += " Strong fit matching the 'product company over research' profile with solid platform activity."
        elif overall_score > 70.0:
            reason += " Good alignment on core technical requirements but with minor concerns on notice period or company background."
        else:
            reason += " Adjacent skills but has gaps in required ML/AI experience or is from pure consulting background."
        return reason
