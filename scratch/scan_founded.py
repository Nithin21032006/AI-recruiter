import json
import re
from pathlib import Path

def scan_founded():
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
            
            # Check for the word "founded"
            for job in career:
                desc = job.get("description", "")
                company = job.get("company", "")
                duration_months = job.get("duration_months", 0)
                
                # Check for "founded" in description
                if "founded" in desc.lower():
                    # Look for years or months in description, e.g., "founded 3 years ago" or "founded in 2023"
                    anomalies.append({
                        "id": cid,
                        "company": company,
                        "duration_months": duration_months,
                        "desc": desc,
                        "start_date": job.get("start_date"),
                        "end_date": job.get("end_date")
                    })
                    if len(anomalies) >= 20:
                        break
            if len(anomalies) >= 20:
                break
                
    print(f"Found {len(anomalies)} instances of 'founded':")
    for a in anomalies:
        print(f"Candidate: {a['id']}, Company: {a['company']}, Duration: {a['duration_months']} months")
        print(f"Start: {a['start_date']}, End: {a['end_date']}")
        print(f"Desc: {a['desc']}\n")

if __name__ == "__main__":
    scan_founded()
