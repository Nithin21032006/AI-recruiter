import os
import json
from typing import Dict, Any
from models.job_description import JobDescription
from models.candidate import Candidate
from models.ranking_result import RankingResult

class ComparisonEngine:
    def __init__(self):
        pass

    def compare_candidates(
        self,
        c1: Candidate,
        r1: RankingResult,
        c2: Candidate,
        r2: RankingResult,
        job: JobDescription
    ) -> Dict[str, Any]:
        """
        Compares two candidates side-by-side.
        Uses LLM if API key is available, otherwise falls back to a detailed heuristic comparison.
        """
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            try:
                return self._compare_with_llm(c1, r1, c2, r2, job, api_key)
            except Exception:
                pass
        return self._compare_with_heuristics(c1, r1, c2, r2, job)

    def _compare_with_llm(
        self,
        c1: Candidate,
        r1: RankingResult,
        c2: Candidate,
        r2: RankingResult,
        job: JobDescription,
        api_key: str
    ) -> Dict[str, Any]:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        c1_info = {
            "name": r1.candidate_name,
            "skills": ", ".join(c1.get_skill_names()),
            "experience": [f"{e.title} at {e.company} ({e.duration_years or 0:.1f} yrs)" for e in c1.experience],
            "scores": r1.model_dump(exclude={"reasoning", "breakdown", "bias_audit", "why_selected"})
        }

        c2_info = {
            "name": r2.candidate_name,
            "skills": ", ".join(c2.get_skill_names()),
            "experience": [f"{e.title} at {e.company} ({e.duration_years or 0:.1f} yrs)" for e in c2.experience],
            "scores": r2.model_dump(exclude={"reasoning", "breakdown", "bias_audit", "why_selected"})
        }

        prompt = f"""
        You are an expert recruitment head. Compare the following two candidates side-by-side for the Job Description.

        Job Description:
        Title: {job.title}
        Description: {job.description}

        Candidate A:
        {json.dumps(c1_info, indent=2)}

        Candidate B:
        {json.dumps(c2_info, indent=2)}

        Compare them across the following dimensions: Experience, Projects, Skills, Behaviour, Leadership, Growth, and provide an Overall Recommendation stating clearly why one candidate ranks higher.
        
        Return ONLY a valid JSON object matching this schema (do not include markdown wrapping or backticks):
        {{
            "experience_comparison": "string comparison text",
            "projects_comparison": "string comparison text",
            "skills_comparison": "string comparison text",
            "behaviour_comparison": "string comparison text",
            "leadership_comparison": "string comparison text",
            "growth_comparison": "string comparison text",
            "overall_recommendation": "string recommending the better candidate and explaining why"
        }}
        """
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        return json.loads(response_text)

    def _compare_with_heuristics(
        self,
        c1: Candidate,
        r1: RankingResult,
        c2: Candidate,
        r2: RankingResult,
        job: JobDescription
    ) -> Dict[str, Any]:
        # 1. Experience
        exp1 = c1.get_total_experience_years()
        exp2 = c2.get_total_experience_years()
        if exp1 > exp2:
            exp_comp = f"{r1.candidate_name} has more total experience ({exp1:.1f} years) compared to {r2.candidate_name} ({exp2:.1f} years)."
        elif exp2 > exp1:
            exp_comp = f"{r2.candidate_name} has more total experience ({exp2:.1f} years) compared to {r1.candidate_name} ({exp1:.1f} years)."
        else:
            exp_comp = f"Both candidates have equivalent total experience of {exp1:.1f} years."

        # 2. Projects
        p1_count = len(c1.experience)
        p2_count = len(c2.experience)
        proj_comp = f"{r1.candidate_name} has worked on {p1_count} distinct roles/projects, whereas {r2.candidate_name} has worked on {p2_count}."

        # 3. Skills
        s1 = set(s.name.lower() for s in c1.skills)
        s2 = set(s.name.lower() for s in c2.skills)
        req = set(s.lower() for s in job.required_skills)
        match1 = s1.intersection(req)
        match2 = s2.intersection(req)
        if len(match1) > len(match2):
            skills_comp = f"{r1.candidate_name} has higher alignment with core required skills, matching {len(match1)}/{len(req)} compared to {r2.candidate_name}'s {len(match2)}/{len(req)}."
        elif len(match2) > len(match1):
            skills_comp = f"{r2.candidate_name} has higher alignment with core required skills, matching {len(match2)}/{len(req)} compared to {r1.candidate_name}'s {len(match1)}/{len(req)}."
        else:
            skills_comp = f"Both candidates have a similar alignment with core required skills, matching {len(match1)}/{len(req)}."

        # 4. Behaviour
        b1 = r1.behavior_score
        b2 = r2.behavior_score
        if b1 > b2:
            beh_comp = f"{r1.candidate_name} scored higher on behavioural trust factors ({b1:.1f}/100) compared to {r2.candidate_name} ({b2:.1f}/100)."
        elif b2 > b1:
            beh_comp = f"{r2.candidate_name} scored higher on behavioural trust factors ({b2:.1f}/100) compared to {r1.candidate_name} ({b1:.1f}/100)."
        else:
            beh_comp = f"Both candidates scored equally on behavioural trust factors ({b1:.1f}/100)."

        # 5. Leadership
        l1 = getattr(r1, 'leadership_score', 50.0) or 50.0
        l2 = getattr(r2, 'leadership_score', 50.0) or 50.0
        if l1 > l2:
            lead_comp = f"{r1.candidate_name} demonstrates stronger leadership and mentoring potential based on their role history."
        elif l2 > l1:
            lead_comp = f"{r2.candidate_name} demonstrates stronger leadership and mentoring potential based on their role history."
        else:
            lead_comp = f"Both candidates show equivalent potential for leadership roles."

        # 6. Growth
        g1 = r1.growth_score
        g2 = r2.growth_score
        if g1 > g2:
            growth_comp = f"{r1.candidate_name} exhibits higher growth indicators based on professional certifications and achievements."
        elif g2 > g1:
            growth_comp = f"{r2.candidate_name} exhibits higher growth indicators based on professional certifications and achievements."
        else:
            growth_comp = f"Both candidates exhibit similar growth indicators."

        # 7. Recommendation
        better = r1.candidate_name if r1.overall_score >= r2.overall_score else r2.candidate_name
        score_diff = abs(r1.overall_score - r2.overall_score)
        overall_rec = (
            f"We recommend {better} as they score higher overall. "
            f"{r1.candidate_name} has overall match score {r1.overall_score:.1f}% vs "
            f"{r2.candidate_name} with {r2.overall_score:.1f}%. "
        )
        if score_diff < 3.0:
            overall_rec += "The candidates are extremely close; review specific project experience to make the final choice."
        else:
            overall_rec += f"{better} offers a cleaner skill match and better overall alignment with key JD parameters."

        return {
            "experience_comparison": exp_comp,
            "projects_comparison": proj_comp,
            "skills_comparison": skills_comp,
            "behaviour_comparison": beh_comp,
            "leadership_comparison": lead_comp,
            "growth_comparison": growth_comp,
            "overall_recommendation": overall_rec
        }
