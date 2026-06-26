import json
from pathlib import Path

def analyze_experience_discrepancy():
    candidates_path = Path(r"c:\Users\nithu\OneDrive\Desktop\AI_Recruiter\data\candidates.jsonl")
    print(f"Reading from {candidates_path}")
    
    thresholds = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
    counts = {t: 0 for t in thresholds}
    
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            profile = c.get("profile", {})
            career = c.get("career_history", [])
            
            profile_years = profile.get("years_of_experience", 0.0)
            career_years = sum(job.get("duration_months", 0) for job in career) / 12.0
            
            diff = career_years - profile_years
            for t in thresholds:
                if diff > t:
                    counts[t] += 1
                    
    print("Threshold of (career_years - profile_years): count of candidates")
    for t in thresholds:
        print(f"   > {t} years: {counts[t]} candidates")

if __name__ == "__main__":
    analyze_experience_discrepancy()
