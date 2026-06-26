import os
import json
import re
from typing import List
from models.job_description import JobDescription
from models.candidate import Candidate

class QuestionGenerator:
    def __init__(self):
        # Database of fallback question templates based on technology keywords
        self.question_templates = {
            "fastapi": [
                "Explain how you optimized asynchronous request handling and concurrency in FastAPI.",
                "How did you structure dependency injection and middleware in your FastAPI codebase?"
            ],
            "django": [
                "Explain how you optimized database query performance and avoided N+1 issues in Django ORM.",
                "How did you design the Django REST Framework serializers and viewsets for low latency?"
            ],
            "kubernetes": [
                "How did you set up auto-scaling rules and resource requests/limits in your Kubernetes clusters?",
                "Explain your approach to zero-downtime rolling updates and traffic routing in Kubernetes."
            ],
            "docker": [
                "Describe how you minimized Docker image sizes and structured multi-stage builds for production.",
                "How did you handle persistent volumes and networking configurations in your container setup?"
            ],
            "embeddings": [
                "Which embedding models (e.g. BGE, E5, MiniLM) have you used, and how did you select them for retrieval accuracy?",
                "How do you handle the trade-off between embedding vector dimensions and search speed?"
            ],
            "vector databases": [
                "How did you optimize indexing (e.g. HNSW vs IVF-Flat) and metadata filtering in your vector database?",
                "Explain how you handle vector database synchronization and updates when candidate data changes."
            ],
            "rag": [
                "How did you mitigate hallucinations and ensure retrieval quality (e.g. chunking strategies, parent document retrieval) in your RAG pipeline?",
                "Describe how you implemented LLM evaluation metrics like correctness and faithfulness for a RAG system."
            ],
            "python": [
                "Explain how you manage memory and leverage multiprocessing or asyncio in high-throughput Python systems.",
                "Describe your experience profiling Python code to find performance bottlenecks."
            ],
            "pytorch": [
                "How did you optimize PyTorch model training and inference pipelines (e.g. mixed precision, torch.compile)?",
                "Explain your approach to custom dataset loading and augmentation in PyTorch."
            ],
            "tensorflow": [
                "How did you handle model serving and inference performance scaling in TensorFlow Serving?",
                "Describe how you optimized graph execution and custom training loops in TensorFlow."
            ]
        }

    def generate_questions(self, candidate: Candidate, job: JobDescription, count: int = 5) -> List[str]:
        """
        Generates customized interview questions.
        Uses LLM if available, otherwise uses keyword-based question templates.
        """
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            try:
                return self._generate_with_llm(candidate, job, count, api_key)
            except Exception:
                pass
        return self._generate_with_heuristics(candidate, job, count)

    def _generate_with_llm(self, candidate: Candidate, job: JobDescription, count: int, api_key: str) -> List[str]:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        skills = ", ".join(candidate.get_skill_names())
        exp_list = [f"{exp.title} at {exp.company}: {exp.description}" for exp in candidate.experience[:3]]

        prompt = f"""
        You are an expert technical interviewer. Generate exactly {count} candidate-specific interview questions.
        The questions must directly tie the candidate's actual projects/skills to the Job Description requirements.
        
        Job Details:
        Title: {job.title}
        Required Skills: {", ".join(job.required_skills)}
        
        Candidate Details:
        Skills: {skills}
        Experience: {"; ".join(exp_list)}
        
        For example, if the candidate built a FastAPI API, ask a targeted question like: "Explain how you optimized asynchronous request handling in your FastAPI API at [Company]."
        
        Return ONLY a JSON list of {count} strings containing the questions (do not include markdown wrapping or backticks).
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

    def _generate_with_heuristics(self, candidate: Candidate, job: JobDescription, count: int) -> List[str]:
        questions = []
        cand_skills_lower = [s.name.lower() for s in candidate.skills]
        resume_text = ((candidate.summary or "") + " " + 
                       " ".join([exp.description or "" for exp in candidate.experience]) + " " +
                       " ".join([exp.title or "" for exp in candidate.experience])).lower()

        # Find matching templates
        for tech, q_list in self.question_templates.items():
            if tech in cand_skills_lower or tech in resume_text:
                for q in q_list:
                    if q not in questions:
                        questions.append(q)

        # Candidate project-based custom template generators
        for exp in candidate.experience:
            if not exp.title or not exp.company:
                continue
            desc = (exp.description or "").lower()
            if "database" in desc or "sql" in desc:
                questions.append(f"At {exp.company}, you worked on database systems as a {exp.title}. Describe how you optimized queries or schema designs there.")
            if "scale" in desc or "million" in desc or "performance" in desc:
                questions.append(f"Describe how you handled scaling and performance optimization challenges in your role as {exp.title} at {exp.company}.")
            if "pipeline" in desc or "etl" in desc or "data" in desc:
                questions.append(f"Explain how you designed and monitored data pipelines during your tenure at {exp.company}.")

        # Deduplicate and slice
        unique_questions = []
        for q in questions:
            if q not in unique_questions:
                unique_questions.append(q)

        # Fallbacks if we don't have enough questions
        fallbacks = [
            f"How does your experience as a software developer align with the core goals of our {job.title} role?",
            "What is your approach to testing and ensuring code reliability in a collaborative engineering team?",
            "Explain how you learn and evaluate new technologies or libraries when starting a project.",
            "Can you describe a challenging technical bottleneck you resolved in a past project?",
            "How do you structure backend architectures to keep them modular, testable, and clean?"
        ]

        for fb in fallbacks:
            if len(unique_questions) >= count:
                break
            if fb not in unique_questions:
                unique_questions.append(fb)

        return unique_questions[:count]
