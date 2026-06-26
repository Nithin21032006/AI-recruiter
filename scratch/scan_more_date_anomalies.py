import json
from pathlib import Path
from datetime import datetime

def scan_more_date_anomalies():
    candidates_path = Path(r"c:\Users\nithu\OneDrive\Desktop\AI_Recruiter\data\candidates.jsonl")
    print(f"Reading from {candidates_path}")
    
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
                        
                        # Check if end date is before start date
                        if end_dt < start_dt:
                            anomalies.append({
                                "id": cid,
                                "reason": f"End date {end_str} is before start date {start_str}"
                            })
                            break
                            
                    # Check if duration_months is 0 but start and end dates are different
                    if duration == 0 and end_str and end_str != start_str:
                        anomalies.append({
                            "id": cid,
                            "reason": f"Duration is 0 but start_date={start_str} and end_date={end_str}"
                        })
                        break
                except Exception as e:
                    pass
                    
    print(f"Found {len(anomalies)} additional date anomalies:")
    for a in anomalies:
        print(f"Candidate: {a['id']}, Reason: {a['reason']}")

if __name__ == "__main__":
    scan_more_date_anomalies()
