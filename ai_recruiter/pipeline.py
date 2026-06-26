from core.job_analyzer import JobAnalyzer
from core.candidate_profiler import CandidateProfiler
from core.embedding_engine import EmbeddingEngine
from core.ranking_engine import RankingEngine
from core.bias_detector import BiasDetector
from core.re_ranking_engine import ReRankingEngine
from core.explanation_engine import ExplanationEngine
from core.skill_gap_analyzer import SkillGapAnalyzer
from core.comparison_engine import ComparisonEngine
from core.question_generator import QuestionGenerator

from models.job_description import JobDescription
from models.candidate import Candidate
from models.ranking_result import RankingBatch, RankingResult
from typing import List, Dict, Any, Optional
from datetime import datetime

class RecruitmentPipeline:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.job_analyzer = JobAnalyzer()
        self.candidate_profiler = CandidateProfiler()
        self.embedding_engine = EmbeddingEngine()
        self.ranking_engine = RankingEngine(weights=weights)
        self.bias_detector = BiasDetector()
        
        # New upgraded core modules
        self.re_ranking_engine = ReRankingEngine()
        self.explanation_engine = ExplanationEngine()
        self.skill_gap_analyzer = SkillGapAnalyzer()
        self.comparison_engine = ComparisonEngine()
        self.question_generator = QuestionGenerator()

    def match_candidates(
        self,
        job_description: JobDescription,
        candidates: List[Candidate],
        weights: Optional[Dict[str, float]] = None,
        check_bias: bool = True
    ) -> RankingBatch:
        """
        Orchestrates the candidate ranking pipeline:
        1. Run job analysis
        2. Filter out traps/exclusions (honeypots, unrelated roles, consulting/academic-only)
        3. Run hybrid ranking engine (incorporating semantic, experience, skills, behavior, education, growth)
        4. LLM Re-ranking of the top 50 candidates
        5. Explainability & Skill Gap Analysis for shortlisted candidates
        6. Apply bias mitigations & calculate fairness score
        """
        # 1. Job Description analysis & understanding
        job_analysis = self.job_analyzer.analyze(job_description)
        # Apply updated fields back to job_description if they were extracted from LLM/fallback
        if "must_have_skills" in job_analysis and job_analysis["must_have_skills"]:
            job_description.required_skills = list(set(job_description.required_skills + job_analysis["must_have_skills"]))
        if "nice_to_have_skills" in job_analysis and job_analysis["nice_to_have_skills"]:
            job_description.nice_to_have_skills = list(set(job_description.nice_to_have_skills + job_analysis["nice_to_have_skills"]))

        # 2. Filter candidates
        valid_candidates = []
        for c in candidates:
            # Profile candidates first to calculate profiling scores
            c_profile = self.candidate_profiler.profile(c)

            # Filter traps
            if self.ranking_engine.is_honeypot(c):
                continue
            
            current_title = ""
            headline = ""
            if c.profile:
                if hasattr(c.profile, 'current_title'):
                    current_title = getattr(c.profile, 'current_title') or ""
                elif isinstance(c.profile, dict):
                    current_title = c.profile.get('current_title') or ""
                elif hasattr(c.profile, 'experience_analysis') and isinstance(c.profile.experience_analysis, dict):
                    current_title = c.profile.experience_analysis.get('current_role') or ""
                
                if hasattr(c.profile, 'headline'):
                    headline = getattr(c.profile, 'headline') or ""
                elif isinstance(c.profile, dict):
                    headline = c.profile.get('headline') or ""

            if not current_title and c.experience:
                current_title = c.experience[0].title or ""

            title_score = self.ranking_engine.get_title_score(
                current_title, 
                headline or c.summary or ""
            )
            if title_score < 0:
                continue

            if self.ranking_engine.has_only_consulting_history(c.experience):
                continue

            if self.ranking_engine.has_only_academic_history(c.experience):
                continue

            valid_candidates.append(c)

        # 3. Hybrid scoring
        results = self.ranking_engine.rank_candidates(valid_candidates, job_description, weights=weights)

        # 4. LLM / Heuristic Re-ranking (Top 50 refinement)
        results = self.re_ranking_engine.rerank_candidates(valid_candidates, results, job_description)

        # 5. Explainability & Skill Gap Analysis (for Top 100 or all results if fewer)
        cand_map = {c.id: c for c in valid_candidates}
        top_results = results[:100]
        for res in top_results:
            c = cand_map.get(res.candidate_id)
            if c:
                # Add explainability highlights
                self.explanation_engine.explain_candidate(c, res, job_description)
                
                # Skill gap analysis
                gaps = self.skill_gap_analyzer.analyze_gaps(c, job_description)
                # Store gap item names in the gaps attribute
                res.gaps = [f"{g.name} ({g.importance}; Learn Time: {g.learning_time}; Impact: {g.hiring_impact})" for g in gaps]
                res.missing_skills = [g.name for g in gaps if g.importance == "High Priority"]

        # Sort all results again to ensure correct ranking order after re-ranking and explanation offsets
        results.sort(key=lambda x: (-x.overall_score, x.candidate_id))
        for rank, res in enumerate(results, 1):
            res.rank = rank

        # 6. Bias detection and fairness auditing
        fairness = 1.0
        warnings = []
        if check_bias:
            self.bias_detector.analyze_ranking_bias(valid_candidates, results)
            self.bias_detector.apply_fairness_constraints(results)
            fairness = self.bias_detector.calculate_fairness_score(results)

        return RankingBatch(
            job_id=job_description.id,
            results=results,
            total_candidates=len(candidates),
            timestamp=datetime.now().isoformat(),
            fairness_score=fairness,
            bias_warnings=warnings
        )

    def update_weights(self, weights: Dict[str, float]):
        self.ranking_engine = RankingEngine(weights=weights)

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        return {
            "embedding_stats": self.embedding_engine.get_embedding_stats(),
            "weights": self.ranking_engine.weights,
            "status": "ready"
        }

    def save_results(self, batch: RankingBatch, path: str):
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(batch.model_dump(), f, indent=2)

    def load_results(self, path: str) -> RankingBatch:
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return RankingBatch(**data)
