import os
import json
import re
from typing import List, Dict, Any
from models.job_description import JobDescription
from models.candidate import Candidate
from models.ranking_result import RankingResult

class ReRankingEngine:
    def __init__(self):
        pass

    def rerank_candidates(
        self,
        candidates: List[Candidate],
        results: List[RankingResult],
        job: JobDescription
    ) -> List[RankingResult]:
        """
        Reranks the top 50 candidates using LLM comparison or fallback heuristics.
        Applies a refinement offset to scores and updates reasoning, strengths, weaknesses,
        and hiring recommendation.
        """
        if not results:
            return results

        # Split results into top 50 and rest
        top_n = min(50, len(results))
        top_results = results[:top_n]
        remaining_results = results[top_n:]

        # Map candidate ID to candidate object
        cand_map = {c.id: c for c in candidates}

        # Check if we can use LLM
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        success = False

        if api_key:
            try:
                success = self._rerank_with_llm(top_results, cand_map, job, api_key)
            except Exception:
                success = False

        if not success:
            self._rerank_with_heuristics(top_results, cand_map, job)

        # Re-sort top results after score adjustments
        # Sort key: overall_score descending, then candidate_id ascending (for tie-breaking)
        top_results.sort(key=lambda x: (-x.overall_score, x.candidate_id))

        # Reassign ranks 1 to 50
        for i, res in enumerate(top_results, 1):
            res.rank = i

        # Reassign remaining ranks
        for i, res in enumerate(remaining_results, top_n + 1):
            res.rank = i

        return top_results + remaining_results

    def _rerank_with_llm(
        self,
        results: List[RankingResult],
        cand_map: Dict[str, Candidate],
        job: JobDescription,
        api_key: str
    ) -> bool:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # To avoid making 50 API calls (which takes too long and hits rate limits),
        # we can process them in small batches (e.g. 5 candidates per prompt)
        batch_size = 5
        for idx in range(0, len(results), batch_size):
            batch = results[idx:idx + batch_size]
            candidates_data = []
            for res in batch:
                c = cand_map.get(res.candidate_id)
                if not c:
                    continue
                skills = ", ".join(c.get_skill_names())
                exp_list = [f"{exp.title} at {exp.company} ({exp.duration_years or 0:.1f} yrs)" for exp in c.experience]
                candidates_data.append({
                    "candidate_id": res.candidate_id,
                    "name": res.candidate_name,
                    "skills": skills,
                    "experience": "; ".join(exp_list),
                    "summary": c.summary or "",
                    "current_score": res.overall_score
                })

            prompt = f"""
            You are an expert recruiter re-ranking candidates for the following Job Description:
            Role: {job.title}
            Description: {job.description}
            Required Skills: {", ".join(job.required_skills)}
            Preferred Skills: {", ".join(job.nice_to_have_skills)}

            Here are {len(candidates_data)} candidates with their current match scores. Compare each candidate against the Job Description.
            Decide if their match score should be adjusted slightly (from -10 to +10 points) based on semantic nuances, leadership qualities, relevant projects, and potential.

            Candidates:
            {json.dumps(candidates_data, indent=2)}

            For each candidate, respond with a JSON object. Return ONLY a JSON list of objects matching the schema (no markdown wrapping):
            [
              {{
                "candidate_id": "string",
                "score_adjustment": float (value between -10.0 and 10.0),
                "strengths": ["list of key strengths"],
                "weaknesses": ["list of weaknesses or gaps"],
                "hiring_recommendation": "Strong Hire" | "Hire" | "No Hire",
                "why_selected": "detailed text explaining why this candidate is selected"
              }}
            ]
            """
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean markdown wrapping if present
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()

            parsed = json.loads(response_text)
            parsed_map = {item["candidate_id"]: item for item in parsed}

            for res in batch:
                item = parsed_map.get(res.candidate_id)
                if item:
                    adj = float(item.get("score_adjustment", 0.0))
                    res.overall_score = min(100.0, max(1.0, res.overall_score + adj))
                    res.score = res.overall_score
                    res.key_strengths = item.get("strengths", [])
                    res.gaps = item.get("weaknesses", [])
                    res.weaknesses = item.get("weaknesses", [])
                    res.hiring_recommendation = item.get("hiring_recommendation", "Hire")
                    res.why_selected = item.get("why_selected", "")
                    
                    # Update reasoning if we have why_selected
                    if res.why_selected:
                        res.reasoning = res.why_selected

        return True

    def _rerank_with_heuristics(
        self,
        results: List[RankingResult],
        cand_map: Dict[str, Candidate],
        job: JobDescription
    ):
        for res in results:
            c = cand_map.get(res.candidate_id)
            if not c:
                continue

            adjustment = 0.0
            strengths = []
            weaknesses = []

            # 1. Check title alignment
            current_title = (c.profile.current_title or "").lower() if c.profile else ""
            jd_title_lower = job.title.lower()
            if jd_title_lower in current_title or current_title in jd_title_lower:
                adjustment += 4.0
                strengths.append("Directly aligned current job title.")
            elif any(kw in current_title for kw in ["senior", "lead", "architect"]):
                adjustment += 2.0
                strengths.append("Senior leadership title background.")

            # 2. Check technical skills alignment
            cand_skills_lower = set(s.name.lower() for s in c.skills)
            req_skills_lower = set(s.lower() for s in job.required_skills)
            nice_skills_lower = set(s.lower() for s in job.nice_to_have_skills)

            req_matches = cand_skills_lower.intersection(req_skills_lower)
            nice_matches = cand_skills_lower.intersection(nice_skills_lower)

            if len(req_matches) == len(req_skills_lower) and len(req_skills_lower) > 0:
                adjustment += 3.0
                strengths.append("Matches all mandatory technical skills.")
            elif len(req_matches) > 0:
                strengths.append(f"Matches {len(req_matches)}/{len(req_skills_lower)} required skills.")
            else:
                adjustment -= 2.0
                weaknesses.append("Missing core mandatory skills.")

            if len(nice_matches) > 0:
                adjustment += min(3.0, len(nice_matches) * 1.0)
                strengths.append(f"Possesses {len(nice_matches)} nice-to-have skill assets.")

            # 3. Check trust/platform activities
            signals = c.redrob_signals or {}
            response_rate = signals.get("recruiter_response_rate", 0.7)
            completion_rate = signals.get("interview_completion_rate", 0.7)
            github_score = signals.get("github_activity_score", 0.0)

            if response_rate >= 0.9:
                adjustment += 2.0
                strengths.append("Highly responsive candidate (90%+ rate).")
            if completion_rate >= 0.9:
                adjustment += 1.5
                strengths.append("Excellent interview completion history.")
            if github_score > 60:
                adjustment += 2.0
                strengths.append("Strong active open-source footprint.")

            # 4. Relocation and notice period
            notice = signals.get("notice_period_days", 30)
            if notice <= 15:
                adjustment += 2.0
                strengths.append("Immediately or quickly available.")
            elif notice > 60:
                adjustment -= 3.0
                weaknesses.append("Long notice period (>60 days).")

            res.overall_score = min(100.0, max(1.0, res.overall_score + adjustment))
            res.score = res.overall_score

            # Populate explainability fields
            res.key_strengths = strengths
            res.gaps = weaknesses
            res.weaknesses = weaknesses

            # Recommendation
            if res.overall_score >= 88.0:
                rec = "Strong Hire"
            elif res.overall_score >= 70.0:
                rec = "Hire"
            else:
                rec = "No Hire"
            res.hiring_recommendation = rec

            # Base reasoning
            skills_part = f"skilled in {', '.join(list(req_matches)[:3])}" if req_matches else "some adjacent skills"
            res.why_selected = (
                f"Candidate {c.name or 'Anonymized'} selected as a {rec} with {res.overall_score:.1f}% score. "
                f"They have {c.get_total_experience_years():.1f} years of experience, {skills_part}, "
                f"and display solid profile trust metrics."
            )
            res.reasoning = res.why_selected
