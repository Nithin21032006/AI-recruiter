import json
from pathlib import Path

def scan_candidates():
    candidates_path = Path(r"c:\Users\nithu\OneDrive\Desktop\AI_Recruiter\data\candidates.jsonl")
    
    print(f"Reading from {candidates_path}")
    count = 0
    anomalies = []
    
    candidates = []
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                candidates.append(json.loads(line))
                        
    for c in candidates:
        cid = c.get("candidate_id")
        skills = c.get("skills", [])
        career = c.get("career_history", [])
        
        # 1. Check "expert" proficiency in multiple skills with 0 or very small duration_months
        expert_zero_duration = []
        for s in skills:
            prof = s.get("proficiency", "").lower()
            dur = s.get("duration_months", 0)
            if prof == "expert" and dur == 0:
                expert_zero_duration.append(s.get("name"))
        
        if len(expert_zero_duration) >= 3:
            anomalies.append({
                "id": cid,
                "reason": f"Expert in {len(expert_zero_duration)} skills ({expert_zero_duration}) but with 0 duration_months",
                "candidate": c
            })
            continue
            
        # 2. Check dates contradiction
        # E.g. job duration is impossible (start_date to end_date doesn't match duration_months)
        for job in career:
            start_date = job.get("start_date")
            end_date = job.get("end_date")
            duration_months = job.get("duration_months", 0)
            # Parse start and end date and compute expected months
            if start_date and end_date:
                try:
                    s_yr, s_mo = map(int, start_date.split("-")[:2])
                    e_yr, e_mo = map(int, end_date.split("-")[:2])
                    expected_months = (e_yr - s_yr) * 12 + (e_mo - s_mo) + 1
                    if abs(duration_months - expected_months) > 3 and expected_months > 0:
                        anomalies.append({
                            "id": cid,
                            "reason": f"Job at {job.get('company')} duration_months={duration_months} but expected_months={expected_months} from {start_date} to {end_date}",
                            "candidate": c
                        })
                        break
                except Exception as e:
                    pass

    print(f"Found {len(anomalies)} anomalies in first {len(candidates)} candidates:")
    for a in anomalies[:5]:
        print(f"Candidate: {a['id']}, Reason: {a['reason']}")
        # print(json.dumps(a['candidate']['profile'], indent=2))
        
if __name__ == "__main__":
    scan_candidates()
