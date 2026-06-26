import json
from pathlib import Path

def scan_advanced_zero():
    candidates_path = Path(r"c:\Users\nithu\OneDrive\Desktop\AI_Recruiter\data\candidates.jsonl")
    print(f"Reading from {candidates_path}")
    
    anomalies = []
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            skills = c.get("skills", [])
            
            advanced_zero_duration = []
            for s in skills:
                prof = s.get("proficiency", "").lower()
                dur = s.get("duration_months", 0)
                if prof == "advanced" and dur == 0:
                    advanced_zero_duration.append(s.get("name"))
            
            if len(advanced_zero_duration) >= 3:
                anomalies.append({
                    "id": c.get("candidate_id"),
                    "skills": advanced_zero_duration
                })
                
    print(f"Found {len(anomalies)} candidates with >=3 advanced skills of 0 duration:")
    for a in anomalies[:10]:
        print(f"  {a['id']}: {a['skills']}")

if __name__ == "__main__":
    scan_advanced_zero()
