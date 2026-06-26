#!/usr/bin/env python3
"""
CLI entry point for Candidate Discovery and Ranking.
Streams candidates, filters traps/exclusions, ranks them, and writes results to CSV.
"""

import argparse
import sys
import csv
import re
import json
from pathlib import Path

# Add ai_recruiter package directory to Python path
ai_recruiter_dir = Path(__file__).parent / "ai_recruiter"
sys.path.insert(0, str(ai_recruiter_dir))

from models.job_description import JobDescription
from models.candidate import Candidate
from core.ranking_engine import RankingEngine
from core.job_analyzer import JobAnalyzer
from core.re_ranking_engine import ReRankingEngine
from core.explanation_engine import ExplanationEngine
from core.skill_gap_analyzer import SkillGapAnalyzer
from core.embedding_engine import EmbeddingEngine
from utils.data_loader import DataLoader


def main():
    parser = argparse.ArgumentParser(description="Rank candidates for Senior AI Engineer JD.")
    parser.add_argument(
        "--candidates",
        type=str,
        default="data/candidates.jsonl",
        help="Path to candidates JSONL file"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="submission.csv",
        help="Path to output CSV file"
    )
    args = parser.parse_args()

    candidates_path = Path(args.candidates)
    out_path = Path(args.out)

    if not candidates_path.exists():
        print(f"Error: Candidate file not found at {candidates_path}")
        sys.exit(1)

    print(f"Loading Job Description for Founding Team Senior AI Engineer...")
    job = JobDescription(
        id="jd_senior_ai_engineer",
        title="Senior AI Engineer — Founding Team",
        company="Redrob AI",
        description="Senior AI Engineer position on the founding team of Redrob AI",
        years_required=5,
        experience_level="Senior",
        location="Pune/Noida, India",
        required_skills=["Python", "embeddings-based retrieval", "vector databases", "search", "ranking", "evaluation frameworks"],
        raw_text="Job Description: Senior AI Engineer — Founding Team"
    )

    # 1. Job Understanding
    print("Running Job Description Understanding...")
    analyzer = JobAnalyzer()
    job_analysis = analyzer.analyze(job)
    if "must_have_skills" in job_analysis and job_analysis["must_have_skills"]:
        job.required_skills = list(set(job.required_skills + job_analysis["must_have_skills"]))
    if "nice_to_have_skills" in job_analysis and job_analysis["nice_to_have_skills"]:
        job.nice_to_have_skills = list(set(job.nice_to_have_skills + job_analysis["nice_to_have_skills"]))

    # 2. Embedding Job Description
    print("Generating Job Description Embedding...")
    embedding_engine = EmbeddingEngine()
    job_emb = embedding_engine.embed_job_description(job)

    # Check if candidate embeddings cache is populated
    cache_size = len(embedding_engine.candidate_embeddings)
    if cache_size < 1000:
        print(f"Candidate embeddings cache is incomplete (size: {cache_size}).")
        print("Generating candidate embeddings from candidates JSONL file... This runs once and takes a few seconds.")
        count = 0
        with open(candidates_path, "r", encoding="utf-8") as f:
            for line in f:
                count += 1
                if count % 20000 == 0:
                    print(f"  Processed {count} candidate embeddings...")
                candidate = Candidate(**json.loads(line))
                embedding_engine.embed_candidate(candidate)
        print("Saving candidate embeddings cache to disk...")
        embedding_engine.save_candidate_embeddings()
        print(f"Embeddings cache successfully saved. Size: {len(embedding_engine.candidate_embeddings)}")

    # 3. Vector Similarity Search
    print("Performing Vector Similarity Search over 100K candidates...")
    similarities = []
    
    # Fast regex to extract candidate_id from JSONL lines to avoid JSON deserialization overhead
    id_pattern = re.compile(r'"candidate_id"\s*:\s*"([^"]+)"')
    
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            match = id_pattern.search(line)
            if match:
                cid = match.group(1)
                # Lookup cached candidate embedding
                cand_emb = embedding_engine.candidate_embeddings.get(cid)
                if cand_emb:
                    sim = embedding_engine.semantic_similarity(job_emb, cand_emb)
                    similarities.append((cid, sim))

    # Keep top 2000 matching candidate IDs
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_candidates_ids = set(cid for cid, _ in similarities[:2000])
    print(f"Top 2000 candidate IDs retrieved. Loading profiles...")

    # 4. Stream & filter top candidate records
    ranking_engine = RankingEngine()
    valid_candidates = []
    
    skipped_honeypot = 0
    skipped_unrelated = 0
    skipped_consulting = 0
    skipped_academic = 0

    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            match = id_pattern.search(line)
            if match:
                cid = match.group(1)
                if cid in top_candidates_ids:
                    candidate = Candidate(**json.loads(line))
                    
                    # 1. Filter out honeypots
                    if ranking_engine.is_honeypot(candidate):
                        skipped_honeypot += 1
                        continue

                    # 2. Filter out completely unrelated roles
                    curr_title = candidate.profile.current_title if candidate.profile else ""
                    headline = candidate.profile.headline if candidate.profile else ""
                    title_score = ranking_engine.get_title_score(curr_title, headline)
                    if title_score < 0:
                        skipped_unrelated += 1
                        continue

                    # 3. Filter out consulting-only
                    if ranking_engine.has_only_consulting_history(candidate.career_history):
                        skipped_consulting += 1
                        continue

                    # 4. Filter out academic-only
                    if ranking_engine.has_only_academic_history(candidate.career_history):
                        skipped_academic += 1
                        continue

                    valid_candidates.append(candidate)

    print(f"Filtering complete.")
    print(f"  Honeypot trap profiles filtered: {skipped_honeypot}")
    print(f"  Unrelated roles filtered: {skipped_unrelated}")
    print(f"  Consulting-only profiles filtered: {skipped_consulting}")
    print(f"  Academic-only profiles filtered: {skipped_academic}")
    print(f"  Remaining valid candidates: {len(valid_candidates)}")

    # 5. Hybrid Scoring
    print("Running Hybrid Scoring Engine...")
    results = ranking_engine.rank_candidates(valid_candidates, job)

    # 6. Re-ranking (Top 50)
    print("Running Re-ranking Engine on Top 50 candidates...")
    re_ranker = ReRankingEngine()
    results = re_ranker.rerank_candidates(valid_candidates, results, job)

    # 7. Explainability & Skill Gap (Top 100)
    print("Generating Explainability highlights and Skill Gap Analysis...")
    explanation_engine = ExplanationEngine()
    gap_analyzer = SkillGapAnalyzer()
    
    cand_map = {c.id: c for c in valid_candidates}
    top_100 = results[:100]

    for res in top_100:
        c = cand_map.get(res.candidate_id)
        if c:
            explanation_engine.explain_candidate(c, res, job)
            gaps = gap_analyzer.analyze_gaps(c, job)
            res.gaps = [f"{g.name} ({g.importance}; Learn Time: {g.learning_time}; Impact: {g.hiring_impact})" for g in gaps]
            res.missing_skills = [g.name for g in gaps if g.importance == "High Priority"]

    # Final Sort
    results.sort(key=lambda x: (-x.overall_score, x.candidate_id))
    for rank, res in enumerate(results[:100], 1):
        res.rank = rank

    top_100_final = results[:100]

    # 8. Output CSVs
    # A. Standard submission.csv (4 columns for the validator)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing standard top 100 candidates to {out_path}...")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for res in top_100_final:
            writer.writerow([
                res.candidate_id,
                res.rank,
                f"{res.overall_score:.4f}",
                res.reasoning
            ])

    # B. Recruiter-facing enhanced_shortlist.csv (All details requested in item 13)
    enhanced_path = out_path.parent / "enhanced_shortlist.csv"
    print(f"Writing recruiter-facing detailed candidates shortlist to {enhanced_path}...")
    with open(enhanced_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rank", "Candidate Name", "Overall Score", "Semantic Score", 
            "Experience Score", "Behaviour Score", "Confidence Score", 
            "Reason for Selection", "Missing Skills", "Hiring Recommendation"
        ])
        for res in top_100_final:
            writer.writerow([
                res.rank,
                res.candidate_name,
                f"{res.overall_score:.2f}",
                f"{res.semantic_score:.2f}",
                f"{res.experience_score:.2f}",
                f"{res.behavior_score:.2f}",
                f"{res.confidence_score:.2f}",
                res.why_selected or res.reasoning,
                ", ".join(res.missing_skills),
                res.hiring_recommendation
            ])

    print("Success! Candidate ranking files generated.")


if __name__ == "__main__":
    main()
