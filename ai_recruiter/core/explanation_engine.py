import os
import json
from typing import Dict, Any, List
from models.job_description import JobDescription
from models.candidate import Candidate
from models.ranking_result import RankingResult

class ExplanationEngine:
    def __init__(self):
        pass

    def explain_candidate(
        self,
        candidate: Candidate,
        result: RankingResult,
        job: JobDescription
    ):
        """
        Generates detailed explainability fields for a shortlisted candidate.
        Uses LLM if available, otherwise runs high-fidelity heuristic parsing.
        """
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        success = False

        if api_key:
            try:
                success = self._explain_with_llm(candidate, result, job, api_key)
            except Exception:
                success = False

        if not success:
            self._explain_with_heuristics(candidate, result, job)

    def _explain_with_llm(
        self,
        candidate: Candidate,
        result: RankingResult,
        job: JobDescription,
        api_key: str
    ) -> bool:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        skills = ", ".join(candidate.get_skill_names())
        exp_list = [f"{exp.title} at {exp.company} (Duration: {exp.duration_years or 0:.1f} yrs) - {exp.description}" for exp in candidate.experience]
        edu_list = [f"{edu.degree} in {edu.field} from {edu.university}" for edu in candidate.education]

        prompt = f"""
        You are an expert recruiter providing a detailed evaluation explaining why a candidate was selected for a job.
        
        Job Details:
        Title: {job.title}
        Description: {job.description}
        Required Skills: {", ".join(job.required_skills)}
        
        Candidate Details:
        Name: {candidate.name or "Anonymized"}
        Summary: {candidate.summary or ""}
        Skills: {skills}
        Experience: {"; ".join(exp_list)}
        Education: {"; ".join(edu_list)}
        Overall Match Score: {result.overall_score:.2f}%
        
        Generate the evaluation details in JSON format. Return ONLY a JSON object matching this schema (do not include markdown wrapping or backticks):
        {{
          "why_selected": "detailed paragraph explaining why they are a good fit",
          "strengths": ["list of top 3-4 candidate strengths"],
          "weaknesses": ["list of 2-3 candidate weaknesses or technical gaps"],
          "missing_skills": ["list of skills from the Job Description that the candidate does not have"],
          "relevant_projects": ["list of 2-3 specific projects from the candidate's experience that align with the Job Description requirements"],
          "career_highlights": ["list of key achievements, e.g. rapid progression, long tenure, top tier company/education, certifications"],
          "hiring_recommendation": "Strong Hire" | "Hire" | "No Hire",
          "confidence_score": float (0.0 to 100.0 representing recruiter confidence in this candidate match)
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

        parsed = json.loads(response_text)
        result.why_selected = parsed.get("why_selected", "")
        result.key_strengths = parsed.get("strengths", [])
        result.gaps = parsed.get("weaknesses", [])
        result.weaknesses = parsed.get("weaknesses", [])
        result.missing_skills = parsed.get("missing_skills", [])
        result.relevant_projects = parsed.get("relevant_projects", [])
        result.career_highlights = parsed.get("career_highlights", [])
        result.hiring_recommendation = parsed.get("hiring_recommendation", "Hire")
        result.confidence_score = float(parsed.get("confidence_score", result.confidence_score))
        return True

    def _explain_with_heuristics(
        self,
        candidate: Candidate,
        result: RankingResult,
        job: JobDescription
    ):
        # 1. Identify missing skills
        req_skills_lower = [s.lower() for s in job.required_skills]
        cand_skills_lower = [s.name.lower() for s in candidate.skills]
        missing_skills = []
        for rs in job.required_skills:
            if rs.lower() not in cand_skills_lower:
                missing_skills.append(rs)
        result.missing_skills = missing_skills

        # 2. Extract relevant projects
        relevant_projects = []
        jd_keywords = ["ai", "ml", "embeddings", "vector", "search", "retrieval", "ranking", "python", "fastapi", "django", "scaling", "eval"]
        for exp in candidate.experience:
            desc_lower = (exp.description or "").lower()
            title_lower = (exp.title or "").lower()
            
            # Count keyword hits
            hits = sum(1 for kw in jd_keywords if kw in desc_lower or kw in title_lower)
            if hits >= 2:
                # Extract a concise description of the project/experience
                p_text = f"As a {exp.title} at {exp.company}: "
                sentences = [s.strip() for s in exp.description.split(".") if s.strip()]
                added_sent = 0
                for sent in sentences:
                    if any(kw in sent.lower() for kw in jd_keywords):
                        p_text += sent + ". "
                        added_sent += 1
                        if added_sent >= 2:
                            break
                if len(p_text) > 40:
                    relevant_projects.append(p_text.strip())

        if not relevant_projects:
            # Fallback to standard project descriptions
            for exp in candidate.experience[:2]:
                if exp.description and len(exp.description) > 30:
                    relevant_projects.append(f"Worked as {exp.title} at {exp.company}: {exp.description[:120]}...")
        result.relevant_projects = relevant_projects[:3]

        # 3. Extract career highlights
        highlights = []
        total_years = candidate.get_total_experience_years()
        if total_years > 5.0:
            highlights.append(f"Solid tenure of {total_years:.1f} years in the tech industry.")
        
        # Check tenure at a single company
        for exp in candidate.experience:
            if (exp.duration_years or 0) >= 3.0:
                highlights.append(f"Long-term stability with {exp.duration_years or 0:.1f} years of tenure at {exp.company}.")
                break
                
        # Education highlights
        for edu in candidate.education:
            deg = (edu.degree or "").lower()
            if any(k in deg for k in ["master", "phd", "m.tech", "ph.d"]):
                highlights.append(f"Advanced academic credential: {edu.degree} in {edu.field or 'CS'}.")
                break
        
        if len(candidate.certifications) > 0:
            highlights.append(f"Earned {len(candidate.certifications)} professional training certifications.")

        if not highlights:
            highlights = ["Consistent career path in software development and engineering."]
        result.career_highlights = highlights[:3]

        # Strengths & Weaknesses
        # Build list of strengths/weaknesses from details
        strengths = result.key_strengths.copy() if result.key_strengths else []
        if not strengths:
            if total_years >= 5:
                strengths.append(f"Experienced professional ({total_years:.1f} years)")
            if len(candidate.skills) > 8:
                strengths.append(f"Broad technical skill set ({len(candidate.skills)} skills)")
            if len(missing_skills) == 0:
                strengths.append("Matches all primary job requirements")
            else:
                strengths.append("Matches majority of job description criteria")
        result.key_strengths = strengths

        weaknesses = result.gaps.copy() if result.gaps else []
        if not weaknesses:
            if missing_skills:
                weaknesses.append(f"Missing specific skills: {', '.join(missing_skills[:3])}")
            if total_years < job.years_required:
                weaknesses.append(f"Has {total_years:.1f} years of experience vs {job.years_required} years required")
            if not weaknesses:
                weaknesses.append("Notice period or location alignment details")
        result.weaknesses = weaknesses
        result.gaps = weaknesses

        # Recompute Recommendation & overall Score
        if result.overall_score >= 88.0:
            rec = "Strong Hire"
        elif result.overall_score >= 70.0:
            rec = "Hire"
        else:
            rec = "No Hire"
        result.hiring_recommendation = rec

        # Generate Why Selected
        skills_part = f"possesses critical skills like {', '.join(candidate.get_skill_names()[:3])}"
        result.why_selected = (
            f"Candidate displays {result.overall_score:.1f}% alignment with the {job.title} role. "
            f"They have {total_years:.1f} years of experience, {skills_part}, and show strong "
            f"career growth indicators. Recruiter recommendation is '{rec}'."
        )
