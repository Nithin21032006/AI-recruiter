import os
import re
import json
from typing import Dict, Any, List
from models.job_description import JobDescription
from utils.text_processor import TextProcessor

class JobAnalyzer:
    def __init__(self):
        self.text_processor = TextProcessor()

    def analyze(self, job: JobDescription) -> Dict[str, Any]:
        text = job.raw_text or job.description
        
        # 1. Standard analysis fields (from old implementation to keep test compatibility)
        skills = self.text_processor.extract_skills(text)
        keywords = self.text_processor.extract_keywords(text)
        all_skills = list(set(skills.get("languages", []) + skills.get("frameworks", []) + skills.get("databases", []) + skills.get("tools", [])))
        complexity_score = min(9.0, len(all_skills) * 0.8 + (job.years_required * 0.5))
        complexity_level = "Low"
        if complexity_score > 6.0:
            complexity_level = "High"
        elif complexity_score > 3.0:
            complexity_level = "Medium"
            
        old_analysis = {
            "job_id": job.id,
            "title": job.title,
            "skills_extracted": {
                "required": job.required_skills,
                "preferred": job.nice_to_have_skills,
                "extracted": skills,
                "all_unique": list(set(job.required_skills + job.nice_to_have_skills + all_skills))
            },
            "requirements": {
                "years": job.years_required,
                "level": job.experience_level,
                "location": job.location
            },
            "seniority_level": job.experience_level,
            "keywords": keywords,
            "job_complexity": {
                "complexity_score": complexity_score,
                "complexity_level": complexity_level
            }
        }
        
        # 2. Extract new fields (LLM or fallback)
        new_analysis = {}
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"""
                You are an expert AI recruiting assistant. Analyze the following job description and extract the details in structured JSON format.

                Job Description:
                {text}

                Extract the following fields and return ONLY a valid JSON object matching this schema (do not include markdown wrapping or backticks):
                {{
                    "role": "string (the primary title/role)",
                    "seniority": "string (e.g., Senior, Mid, Junior, Lead)",
                    "responsibilities": ["list of strings representing key responsibilities"],
                    "must_have_skills": ["list of required technical/hard skills"],
                    "nice_to_have_skills": ["list of preferred/nice-to-have technical skills"],
                    "soft_skills": ["list of soft skills, e.g. communication, collaboration"],
                    "leadership": "string or boolean (leadership requirements or management scope)",
                    "industry": "string (e.g. HR-tech, Finance, AI)",
                    "tech_stack": ["list of technologies mentioned in the stack"],
                    "expected_projects": ["list of projects or tasks the candidate will work on"],
                    "education": "string (required degree or education level)",
                    "culture_fit": ["list of cultural values or fit attributes"]
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
                parsed_json = json.loads(response_text)
                required_keys = [
                    "role", "seniority", "responsibilities", "must_have_skills", 
                    "nice_to_have_skills", "soft_skills", "leadership", "industry", 
                    "tech_stack", "expected_projects", "education", "culture_fit"
                ]
                if all(k in parsed_json for k in required_keys):
                    new_analysis = parsed_json
            except Exception:
                pass
                
        if not new_analysis:
            new_analysis = self._fallback_analyze(job)
            
        merged = {**old_analysis, **new_analysis}
        return merged

    def _fallback_analyze(self, job: JobDescription) -> Dict[str, Any]:
        text = job.raw_text or job.description
        text_lower = text.lower()
        
        # 1. Role
        role = job.title
        
        # 2. Seniority
        seniority = job.experience_level or "Mid"
        if not job.experience_level:
            if any(kw in text_lower for kw in ["senior", "sr."]):
                seniority = "Senior"
            elif any(kw in text_lower for kw in ["lead", "principal"]):
                seniority = "Lead"
            elif any(kw in text_lower for kw in ["junior", "jr."]):
                seniority = "Junior"
                
        # 3. Responsibilities
        responsibilities = []
        sentences = re.split(r'[.!?]\s+', text)
        responsibility_keywords = ["responsible", "design", "build", "develop", "lead", "manage", "collaborate", "ensure", "write", "maintain"]
        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean:
                continue
            if (sent_clean.startswith(("-", "*", "•")) or 
                any(sent_clean.lower().startswith(kw) for kw in responsibility_keywords) or
                ("will" in sent_clean.lower() and any(kw in sent_clean.lower() for kw in responsibility_keywords))):
                cleaned_sent = re.sub(r'^[\-\*•\d\.\s]+', '', sent_clean)
                if len(cleaned_sent) > 10:
                    responsibilities.append(cleaned_sent)
        if not responsibilities:
            responsibilities = [f"Develop and deliver core systems for {job.title}.", "Collaborate with cross-functional teams."]
            
        # 4. Must Have Skills
        must_have = job.required_skills.copy() if job.required_skills else []
        if not must_have:
            skills = self.text_processor.extract_skills(text)
            must_have = list(set(skills.get("languages", []) + skills.get("frameworks", [])))
            
        # 5. Nice To Have Skills
        nice_to_have = job.nice_to_have_skills.copy() if job.nice_to_have_skills else []
        if not nice_to_have:
            skills = self.text_processor.extract_skills(text)
            nice_to_have = list(set(skills.get("databases", []) + skills.get("tools", [])))
            
        # 6. Soft Skills
        soft_skills = []
        soft_skill_keywords = {
            "Communication": ["communication", "present", "write", "verbal", "report"],
            "Collaboration": ["collaborate", "team", "share", "partner", "cooperate"],
            "Problem Solving": ["solve", "optimize", "analytical", "troubleshoot"],
            "Adaptability": ["adapt", "learn", "fast-paced", "flexible"],
            "Ownership": ["ownership", "autonomy", "self-starter", "independent"]
        }
        for skill, kw_list in soft_skill_keywords.items():
            if any(kw in text_lower for kw in kw_list):
                soft_skills.append(skill)
        if not soft_skills:
            soft_skills = ["Collaboration", "Communication"]
            
        # 7. Leadership
        leadership = "None"
        if any(kw in text_lower for kw in ["lead", "manager", "mentor", "leadership"]):
            leadership = "Team leadership and mentoring"
            
        # 8. Industry
        industry = "Software / Tech"
        industry_keywords = {
            "AI / Machine Learning": ["ai", "ml", "machine learning", "nlp", "computer vision", "generative ai"],
            "HR-Tech / Recruitment": ["hr-tech", "recruiting", "talent", "hiring", "applicant", "job board"],
            "Finance / Fintech": ["fintech", "finance", "banking", "payment"],
            "Healthcare": ["healthcare", "medical", "clinical", "health"]
        }
        for ind, kw_list in industry_keywords.items():
            if any(kw in text_lower for kw in kw_list):
                industry = ind
                break
                
        # 9. Tech Stack
        tech_stack = list(set(must_have + nice_to_have))
        if not tech_stack:
            tech_stack = ["Python", "SQL", "Git"]
            
        # 10. Expected Projects
        expected_projects = []
        project_keywords = ["project", "pipeline", "platform", "system", "infrastructure", "dashboard", "engine"]
        for sent in sentences:
            sent_clean = sent.strip()
            if any(kw in sent_clean.lower() for kw in project_keywords) and len(sent_clean) > 20:
                cleaned_sent = re.sub(r'^[\-\*•\d\.\s]+', '', sent_clean)
                expected_projects.append(cleaned_sent)
        if not expected_projects:
            expected_projects = [f"Build and optimize the {job.title} backend and infrastructure."]
            
        # 11. Education
        education = "Bachelor's degree in Computer Science or equivalent experience"
        if "master" in text_lower or "m.s." in text_lower:
            education = "Master's degree in Computer Science or a related quantitative field"
        elif "phd" in text_lower or "ph.d" in text_lower:
            education = "Ph.D. in Machine Learning, Computer Science, or similar field"
            
        # 12. Culture Fit
        culture_fit = []
        culture_keywords = {
            "Innovation-driven": ["innovative", "cutting-edge", "research", "explore"],
            "High Ownership": ["ownership", "founder", "autonomy", "self-directed"],
            "Collaboration-focused": ["collaborative", "team player", "inclusive", "diversity"],
            "Fast-paced / Startup": ["startup", "fast-paced", "agile", "growth"]
        }
        for cult, kw_list in culture_keywords.items():
            if any(kw in text_lower for kw in kw_list):
                culture_fit.append(cult)
        if not culture_fit:
            culture_fit = ["High Ownership", "Collaboration-focused"]
            
        return {
            "role": role,
            "seniority": seniority,
            "responsibilities": responsibilities,
            "must_have_skills": must_have,
            "nice_to_have_skills": nice_to_have,
            "soft_skills": soft_skills,
            "leadership": leadership,
            "industry": industry,
            "tech_stack": tech_stack,
            "expected_projects": expected_projects,
            "education": education,
            "culture_fit": culture_fit
        }

    def extract_skills(self, job_description: JobDescription) -> Dict[str, Any]:
        skills = self.text_processor.extract_skills(job_description.raw_text or job_description.description)
        all_skills = list(set(skills.get("languages", []) + skills.get("frameworks", []) + skills.get("databases", []) + skills.get("tools", [])))
        return {
            "required": job_description.required_skills,
            "preferred": job_description.nice_to_have_skills,
            "extracted": skills,
            "all_unique": list(set(job_description.required_skills + job_description.nice_to_have_skills + all_skills))
        }

    def extract_requirements(self, job_description: JobDescription) -> Dict[str, Any]:
        return {
            "years": job_description.years_required,
            "level": job_description.experience_level,
            "location": job_description.location,
            "education": job_description.education,
            "responsibilities": job_description.responsibilities
        }

    def identify_seniority_level(self, job_description: JobDescription) -> Dict[str, Any]:
        return {
            "stated_level": job_description.experience_level,
            "inferred_level": job_description.experience_level,
            "seniority_score": 2 if job_description.experience_level == "Senior" else 1
        }

    def extract_keywords(self, job_description: JobDescription) -> List[str]:
        return self.text_processor.extract_keywords(job_description.raw_text or job_description.description)

    def assess_job_complexity(self, job_description: JobDescription) -> Dict[str, Any]:
        skills = self.text_processor.extract_skills(job_description.raw_text or job_description.description)
        all_skills = list(skills.get("languages", []) + skills.get("frameworks", []) + skills.get("databases", []) + skills.get("tools", []))
        complexity_score = min(9.0, len(all_skills) * 0.8 + (job_description.years_required * 0.5))
        return {
            "complexity_score": complexity_score,
            "complexity_level": "High" if complexity_score > 6.0 else "Medium" if complexity_score > 3.0 else "Low"
        }
