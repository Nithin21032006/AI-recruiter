import json
from pathlib import Path
from datetime import datetime

def scan_date_anomalies():
    candidates_path = Path(r"c:\Users\nithu\OneDrive\Desktop\AI_Recruiter\data\candidates.jsonl")
    print(f"Reading from {candidates_path}")
    
    current_date = datetime(2026, 6, 23) # Current competition time
    anomalies = []
    
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c.get("candidate_id")
            career = c.get("career_history", [])
            
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
                        
                    # Calculate actual months between start_dt and end_dt
                    elapsed_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1
                    
                    # Check if duration_months exceeds the elapsed time significantly
                    if duration > elapsed_months + 1:
                        anomalies.append({
                            "id": cid,
                            "reason": f"Job at {job.get('company')} lists duration_months={duration} but elapsed months from {start_str} to {end_str or 'present'} is {elapsed_months}"
                        })
                        break
                except Exception as e:
                    pass
                    
    print(f"Found {len(anomalies)} date anomalies:")
    for a in anomalies[:10]:
        print(f"Candidate: {a['id']}, Reason: {a['reason']}")

if __name__ == "__main__":
    scan_date_anomalies()
