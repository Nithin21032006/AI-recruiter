import hashlib
import math
import json
import os
from models.job_description import JobDescription
from models.candidate import Candidate
from utils.text_processor import TextProcessor
from typing import List, Dict, Tuple, Any

class EmbeddingEngine:
    def __init__(self, cache_path: str = "data/candidate_embeddings.json"):
        self.text_processor = TextProcessor()
        self.cache = {}
        self.cache_path = cache_path
        self.candidate_embeddings = {}
        
        # Load pre-computed candidate embeddings if they exist
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self.candidate_embeddings = json.load(f)
            except Exception:
                pass
                
        self.vocabulary = [
            "python", "django", "flask", "fastapi", "embeddings", "retrieval", "vector",
            "database", "search", "ranking", "evaluation", "frameworks", "ndcg", "mrr", "map",
            "rag", "pinecone", "weaviate", "qdrant", "milvus", "elasticsearch", "opensearch", "faiss",
            "machine", "learning", "ai", "ml", "nlp", "deep", "neural", "network", "transformer",
            "bert", "gpt", "llm", "lora", "fine-tune", "deployment", "production", "scale", "system"
        ]
        self.vocab_indices = {w: i for i, w in enumerate(self.vocabulary)}

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * len(self.vocabulary)
        
        cache_key = self._get_cache_key(text)
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        words = self.text_processor.tokenize(text)
        vector = [0.0] * len(self.vocabulary)
        
        for w in words:
            idx = self.vocab_indices.get(w)
            if idx is not None:
                vector[idx] += 1.0
                
        magnitude = math.sqrt(sum(v**2 for v in vector))
        if magnitude > 0.0:
            vector = [v / magnitude for v in vector]
            
        self.cache[cache_key] = vector
        return vector

    def embed_job_description(self, job: JobDescription) -> List[float]:
        text = f"{job.title} {job.description} {' '.join(job.required_skills)} {' '.join(job.nice_to_have_skills)}"
        return self.embed_text(text)

    def embed_candidate(self, candidate: Candidate) -> List[float]:
        # Fast lookup in persistent storage
        if candidate.id in self.candidate_embeddings:
            return self.candidate_embeddings[candidate.id]
            
        # If not cached, generate the embedding vector
        skills_text = " ".join(candidate.get_skill_names())
        exp_text = " ".join([f"{exp.title} {exp.description}" for exp in candidate.experience])
        text = f"{candidate.summary or ''} {skills_text} {exp_text}"
        vector = self.embed_text(text)
        
        # Save to cache
        self.candidate_embeddings[candidate.id] = vector
        return vector

    def save_candidate_embeddings(self):
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.candidate_embeddings, f)
        except Exception:
            pass

    def semantic_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        if not emb1 or not emb2 or len(emb1) != len(emb2):
            return 0.0
        # Cosine similarity of normalized vectors is the dot product (fast)
        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        return min(1.0, max(0.0, dot_product))

    def find_similar(self, query: str, documents: List[str], k: int = 5) -> List[Tuple[int, float]]:
        q_emb = self.embed_text(query)
        scores = []
        for idx, doc in enumerate(documents):
            doc_emb = self.embed_text(doc)
            sim = self.semantic_similarity(q_emb, doc_emb)
            scores.append((idx, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def compute_skill_similarity(self, required: List[str], candidate_skills: List[str]) -> float:
        if not required:
            return 1.0
        req_set = set(s.lower() for s in required)
        cand_set = set(s.lower() for s in candidate_skills)
        matched = req_set.intersection(cand_set)
        return len(matched) / len(req_set)

    def get_embedding_stats(self) -> Dict[str, Any]:
        return {
            "vocabulary_size": len(self.vocabulary),
            "cached_embeddings_count": len(self.cache),
            "candidate_embeddings_count": len(self.candidate_embeddings),
            "model_name": "Persistent TF-IDF Vector Embedder"
        }
