import re
from typing import List, Dict, Any

class TextProcessor:
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        cleaned = self.clean_text(text).lower()
        words = re.findall(r'[a-zA-Z0-9\+\#\-\.]+', cleaned)
        return words

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        if not text:
            return {}
        text_lower = text.lower()
        skills = {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "tools": []
        }
        
        categories = {
            "languages": ["python", "javascript", "typescript", "c++", "java", "scala", "go", "rust", "r", "sql"],
            "frameworks": ["django", "flask", "fastapi", "react", "vue", "angular", "tensorflow", "pytorch", "keras", "scikit-learn", "spark"],
            "databases": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "pinecone", "weaviate", "qdrant", "milvus"],
            "tools": ["docker", "kubernetes", "aws", "gcp", "azure", "git", "jenkins", "airflow", "mlflow"]
        }
        
        for cat, kw_list in categories.items():
            for kw in kw_list:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    skills[cat].append(kw)
        return skills

    def extract_experience(self, text: str) -> Dict[str, Any]:
        if not text:
            return {"years": 0.0, "level": "Mid"}
        text_lower = text.lower()
        
        years_match = re.search(r'(\d+(?:\.\d+)?)\s*[-+]?\s*years?', text_lower)
        years = float(years_match.group(1)) if years_match else 0.0
        
        level = "Mid"
        if "senior" in text_lower or "lead" in text_lower or "principal" in text_lower:
            level = "Senior"
        elif "junior" in text_lower or "entry" in text_lower or "intern" in text_lower:
            level = "Junior"
            
        return {"years": years, "level": level}

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    def extract_keywords(self, text: str, top_n: int = 15) -> List[str]:
        words = self.tokenize(text)
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "are", "was", "were", "of", "to"}
        filtered = [w for w in words if w not in stop_words and len(w) > 2]
        
        freq = {}
        for w in filtered:
            freq[w] = freq.get(w, 0) + 1
            
        sorted_words = sorted(freq.keys(), key=lambda x: freq[x], reverse=True)
        return sorted_words[:top_n]
