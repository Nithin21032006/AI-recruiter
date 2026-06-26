import json
from pathlib import Path
from datetime import datetime

def scan_all_honeypots():
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
            
            # 1. Date anomaly: duration_months > elapsed months between start_date and end_date/present
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
                        is_honeypot = True
                        reasons.append(f"Job at {job.get('company')} duration={duration} > elapsed={elapsed_months} ({start_str} to {end_str or 'present'})")
                except Exception as e:
                    pass
            
            # 2. Skill anomaly: "expert" or "advanced" skill with duration_months == 0
            for s in skills:
                name = s.get("name")
                prof = s.get("proficiency", "").lower()
                dur = s.get("duration_months", 0)
                if prof in ["expert", "advanced"] and dur == 0:
                    is_honeypot = True
                    reasons.append(f"Skill {name} has proficiency '{prof}' but 0 duration_months")
            
            # 3. profile years_of_experience is impossible given career history durations
            # E.g. total experience from career history is way larger than profile years_of_experience
            profile_years = profile.get("years_of_experience", 0.0)
            career_years = sum(job.get("duration_months", 0) for job in career) / 12.0
            if career_years > profile_years + 2.0:
                is_honeypot = True
                reasons.append(f"Profile experience is {profile_years} years, but career history sums to {career_years:.2f} years")
            
            if is_honeypot:
                honeypot_ids.append((cid, reasons))
                
    print(f"Total potential honeypots found: {len(honeypot_ids)}")
    with open("honeypots.json", "w") as out:
        json.dump({cid: reasons for cid, reasons in honeypot_ids}, out, indent=2)
    print("Saved details to honeypots.json")
    
    # Print sample
    for cid, reasons in honeypot_ids[:10]:
        print(f"{cid}: {reasons[:2]}")

if __name__ == "__main__":
    scan_all_honeypots()
