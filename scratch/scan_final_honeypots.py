import json
from pathlib import Path
from datetime import datetime

def scan_final_honeypots():
    candidates_path = Path(r"c:\Users\nithu\OneDrive\Desktop\AI_Recruiter\data\candidates.jsonl")
    print(f"Reading from {candidates_path}")
    
    current_date = datetime(2026, 6, 23)
    honeypots = set()
    
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c.get("candidate_id")
            profile = c.get("profile", {})
            career = c.get("career_history", [])
            skills = c.get("skills", [])
            
            is_hp = False
            
            # Rule 1: Dates vs Duration contradiction
            for job in career:
                start_str = job.get("start_date")
                end_str = job.get("end_date")
                duration = job.get("duration_months", 0)
                
                if not start_str:
                    continue
                try:
                    s_yr, s_mo = map(int, start_str.split("-")[:2])
                    start_dt = datetime(s_yr, s_mo, 1)
                    
                    if end_str:
                        e_yr, e_mo = map(int, end_str.split("-")[:2])
                        end_dt = datetime(e_yr, e_mo, 1)
                    else:
                        end_dt = current_date
                        
                    elapsed_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1
                    if duration > elapsed_months + 1:
                        is_hp = True
                except:
                    pass
            
            # Rule 2: Expert skill with 0 duration
            for s in skills:
                prof = s.get("proficiency", "").lower()
                dur = s.get("duration_months", 0)
                if prof == "expert" and dur == 0:
                    is_hp = True
            
            # Rule 3: career_years > profile_years + 2.0
            profile_years = profile.get("years_of_experience", 0.0)
            career_years = sum(job.get("duration_months", 0) for job in career) / 12.0
            if career_years > profile_years + 2.0:
                is_hp = True
                
            # Rule 4: Skill duration exceeds profile experience by more than 4 years
            for s in skills:
                dur_months = s.get("duration_months", 0)
                if dur_months > profile_years * 12 + 48 and profile_years > 0:
                    is_hp = True
                    
            if is_hp:
                honeypots.add(cid)
                
    print(f"Total unique honeypots found: {len(honeypots)}")
    
if __name__ == "__main__":
    scan_final_honeypots()
