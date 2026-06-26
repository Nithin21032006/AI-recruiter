import json
from pathlib import Path

def analyze_skill_anomalies():
    candidates_path = Path(r"c:\Users\nithu\OneDrive\Desktop\AI_Recruiter\data\candidates.jsonl")
    print(f"Reading from {candidates_path}")
    
    counts = {}
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            skills = c.get("skills", [])
            
            expert_zero_duration = 0
            for s in skills:
                prof = s.get("proficiency", "").lower()
                dur = s.get("duration_months", 0)
                if prof == "expert" and dur == 0:
                    expert_zero_duration += 1
            
            if expert_zero_duration > 0:
                counts[expert_zero_duration] = counts.get(expert_zero_duration, 0) + 1
                
    print("Number of expert skills with 0 duration: count of candidates")
    for k in sorted(counts.keys()):
        print(f"   {k} skill(s): {counts[k]} candidates")

if __name__ == "__main__":
    analyze_skill_anomalies()
