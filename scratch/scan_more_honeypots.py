import json
from pathlib import Path
from datetime import datetime

def scan_more_honeypots():
    candidates_path = Path(r"c:\Users\nithu\OneDrive\Desktop\AI_Recruiter\data\candidates.jsonl")
    print(f"Reading from {candidates_path}")
    
    current_date = datetime(2026, 6, 23)
    honeypot_ids = []
    
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c.get("candidate_id")
            profile = c.get("profile", {})
            career = c.get("career_history", [])
            skills = c.get("skills", [])
            
            is_honeypot = False
            reasons = []
            
            profile_years = profile.get("years_of_experience", 0.0)
            career_years = sum(job.get("duration_months", 0) for job in career) / 12.0
            
            # 1. Career duration is way smaller than profile experience
            # e.g., profile lists 8 years, but career lists 1 year
            if profile_years > 3.0 and career_years < profile_years * 0.4:
                is_honeypot = True
                reasons.append(f"Profile experience is {profile_years} years, but career history sums to only {career_years:.2f} years")
            
            # 2. Skill duration exceeds profile experience
            for s in skills:
                name = s.get("name")
                dur_months = s.get("duration_months", 0)
                dur_years = dur_months / 12.0
                if dur_years > profile_years + 2.0 and profile_years > 0:
                    is_honeypot = True
                    reasons.append(f"Skill {name} duration is {dur_years:.2f} years, exceeding profile experience of {profile_years} years")
                
                # Check if skill duration exceeds total career history duration
                if dur_months > (sum(job.get("duration_months", 0) for job in career) + 24) and career_years > 0:
                    is_honeypot = True
                    reasons.append(f"Skill {name} duration is {dur_months} months, exceeding total career history duration of {sum(job.get('duration_months', 0) for job in career)} months")
            
            if is_honeypot:
                honeypot_ids.append((cid, reasons))
                
    print(f"Total potential honeypots found: {len(honeypot_ids)}")
    for cid, reasons in honeypot_ids[:10]:
        print(f"{cid}: {reasons}")

if __name__ == "__main__":
    scan_more_honeypots()
