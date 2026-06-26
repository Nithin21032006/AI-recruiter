import json
from typing import List, Generator
from models.job_description import JobDescription
from models.candidate import Candidate

class DataLoader:
    @staticmethod
    def stream_candidates_from_jsonl(path: str) -> Generator[Candidate, None, None]:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    yield Candidate(**data)

    @staticmethod
    def load_candidates_from_json(path: str) -> List[Candidate]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return [Candidate(**item) for item in data]
            else:
                return [Candidate(**data)]

    @staticmethod
    def load_job_description_from_json(path: str) -> JobDescription:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return JobDescription(**data)

    @staticmethod
    def save_job_description_to_json(job: JobDescription, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(job.model_dump(), f, indent=2)

    @staticmethod
    def save_candidates_to_json(candidates: List[Candidate], path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in candidates], f, indent=2)
