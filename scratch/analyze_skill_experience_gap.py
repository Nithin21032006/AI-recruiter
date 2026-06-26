import json
from pathlib import Path

def analyze_skill_experience_gap():
    candidates_path = Path(r"c:\Users\nithu\OneDrive\Desktop\AI_Recruiter\data\candidates.jsonl")
    print(f"Reading from {candidates_path}")
    
    thresholds = [12, 24, 36, 48, 60, 72] # months of gap
    counts = {t: 0 for t in thresholds}
    
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            profile = c.get("profile", {})
            skills = c.get("skills", [])
            
            profile_months = profile.get("years_of_experience", 0.0) * 12.0
            
            # Find max skill duration
            max_skill_dur = max([s.get("duration_months", 0) for s in skills]) if skills else 0
            
            gap = max_skill_dur - profile_months
            for t in thresholds:
                if gap > t:
                    counts[t] += 1
                    
    print("Threshold of (skill_duration_months - profile_experience_months): count of candidates")
    for t in thresholds:
        print(f"   > {t} months ({t/12.0} years): {counts[t]} candidates")

if __name__ == "__main__":
    analyze_skill_experience_gap()
