import json
from pathlib import Path
from datetime import datetime

def scan_value_violations():
    candidates_path = Path(r"c:\Users\nithu\OneDrive\Desktop\AI_Recruiter\data\candidates.jsonl")
    print(f"Reading from {candidates_path}")
    
    anomalies = []
    
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c.get("candidate_id")
            signals = c.get("redrob_signals", {})
            
            # 1. Expected salary min > max
            sal = signals.get("expected_salary_range_inr_lpa", {})
            s_min = sal.get("min", 0.0)
            s_max = sal.get("max", 0.0)
            if s_min > s_max:
                anomalies.append({
                    "id": cid,
                    "reason": f"Expected salary min {s_min} > max {s_max}"
                })
                continue
                
            # 2. Signup date after last active date
            signup_str = signals.get("signup_date")
            active_str = signals.get("last_active_date")
            if signup_str and active_str:
                try:
                    s_dt = datetime.strptime(signup_str, "%Y-%m-%d")
                    a_dt = datetime.strptime(active_str, "%Y-%m-%d")
                    if s_dt > a_dt:
                        anomalies.append({
                            "id": cid,
                            "reason": f"Signup date {signup_str} is after last active date {active_str}"
                        })
                        continue
                except Exception as e:
                    pass
            
            # 3. Invalid rates (outside 0-1)
            response_rate = signals.get("recruiter_response_rate", 0.0)
            if response_rate < 0.0 or response_rate > 1.0:
                anomalies.append({
                    "id": cid,
                    "reason": f"recruiter_response_rate {response_rate} outside 0-1"
                })
                continue
                
            interview_rate = signals.get("interview_completion_rate", 0.0)
            if interview_rate < 0.0 or interview_rate > 1.0:
                anomalies.append({
                    "id": cid,
                    "reason": f"interview_completion_rate {interview_rate} outside 0-1"
                })
                continue

            offer_rate = signals.get("offer_acceptance_rate", 0.0)
            if offer_rate != -1.0 and (offer_rate < 0.0 or offer_rate > 1.0):
                anomalies.append({
                    "id": cid,
                    "reason": f"offer_acceptance_rate {offer_rate} outside 0-1 (and not -1)"
                })
                continue

    print(f"Found {len(anomalies)} value range violations:")
    for a in anomalies[:20]:
        print(f"Candidate: {a['id']}, Reason: {a['reason']}")

if __name__ == "__main__":
    scan_value_violations()
