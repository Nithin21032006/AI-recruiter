"""
Test Suite for AI Recruiter Pipeline

This module contains comprehensive tests for all components.
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from models.job_description import JobDescription, SalaryRange
from models.candidate import Candidate, Skill, Experience, Education
from models.ranking_result import RankingResult, ScoreBreakdown, BiasAudit, RankingBatch
from core.job_analyzer import JobAnalyzer
from core.candidate_profiler import CandidateProfiler
from core.embedding_engine import EmbeddingEngine
from core.ranking_engine import RankingEngine
from core.bias_detector import BiasDetector
from pipeline import RecruitmentPipeline
from utils.text_processor import TextProcessor


class TestJobDescription:
    """Test JobDescription model."""
    
    def test_create_job_description(self):
        """Test creating job description."""
        job = JobDescription(
            id="jd_001",
            title="Senior Python Developer",
            company="TechCorp",
            description="Looking for experienced Python developer",
            years_required=5,
            experience_level="Senior",
            location="Remote",
            required_skills=["Python", "Django"],
            raw_text="Looking for experienced Python developer"
        )
        
        assert job.id == "jd_001"
        assert job.title == "Senior Python Developer"
        assert len(job.required_skills) == 2
    
    def test_job_description_with_salary(self):
        """Test job description with salary range."""
        salary_range = SalaryRange(min=100000.0, max=150000.0, currency="USD")
        job = JobDescription(
            id="jd_002",
            title="Senior Developer",
            company="TechCorp",
            description="Job description",
            salary_range=salary_range,
            raw_text="Job description"
        )
        
        assert job.salary_range.min == 100000.0
        assert job.salary_range.currency == "USD"


class TestCandidate:
    """Test Candidate model."""
    
    def test_create_candidate(self):
        """Test creating candidate."""
        candidate = Candidate(
            id="cand_001",
            name="John Doe",
            email="john@example.com",
            location="SF",
            skills=[Skill(name="Python", proficiency="Expert", years=5)]
        )
        
        assert candidate.id == "cand_001"
        assert candidate.name == "John Doe"
        assert len(candidate.skills) == 1
    
    def test_candidate_get_skill_proficiency(self):
        """Test getting skill proficiency."""
        candidate = Candidate(
            id="cand_001",
            name="John Doe",
            email="john@example.com",
            skills=[Skill(name="Python", proficiency="Expert", years=5)]
        )
        
        proficiency = candidate.get_skill_proficiency("python")
        assert proficiency == "Expert"


class TestTextProcessor:
    """Test TextProcessor utility."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.processor = TextProcessor()
    
    def test_clean_text(self):
        """Test text cleaning."""
        text = "  Hello   World  \n  Test  "
        cleaned = self.processor.clean_text(text)
        
        assert "  " not in cleaned
        assert cleaned.strip() == cleaned
    
    def test_extract_skills(self):
        """Test skill extraction."""
        text = "I have expertise in Python, Django, and PostgreSQL"
        skills = self.processor.extract_skills(text)
        
        assert "Python" in str(skills) or "python" in str(skills).lower()
        assert len(skills) > 0


class TestJobAnalyzer:
    """Test JobAnalyzer component."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = JobAnalyzer()
    
    def test_analyze_job(self):
        """Test job analysis."""
        job = JobDescription(
            id="jd_001",
            title="Senior Python Developer",
            company="TechCorp",
            description="We need experienced Python developer with Django experience",
            years_required=5,
            experience_level="Senior",
            required_skills=["Python", "Django", "PostgreSQL"],
            nice_to_have_skills=["Docker", "Kubernetes"],
            responsibilities=["Build APIs", "Write tests"],
            raw_text="Full job description"
        )
        
        analysis = self.analyzer.analyze(job)
        
        assert 'job_id' in analysis
        assert 'title' in analysis
        assert 'skills_extracted' in analysis


class TestCandidateProfiler:
    """Test CandidateProfiler component."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.profiler = CandidateProfiler()
    
    def test_profile_candidate(self):
        """Test candidate profiling."""
        candidate = Candidate(
            id="cand_001",
            name="John Doe",
            email="john@example.com",
            location="SF",
            summary="5 years backend development",
            skills=[
                Skill(name="Python", proficiency="Expert", years=5),
                Skill(name="Django", proficiency="Advanced", years=4)
            ],
            experience=[
                Experience(
                    title="Senior Developer",
                    company="TechCorp",
                    start_date="2019-06",
                    end_date="present",
                    duration_years=5,
                    description="Backend development"
                )
            ],
            education=[
                Education(
                    degree="Bachelor",
                    field="Computer Science",
                    university="UC Berkeley",
                    graduation_year=2019
                )
            ]
        )
        
        profile = self.profiler.profile(candidate)
        
        assert 'candidate_id' in profile
        assert 'skills_analysis' in profile
        assert 'experience_analysis' in profile


class TestEmbeddingEngine:
    """Test EmbeddingEngine component."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = EmbeddingEngine()
    
    def test_embed_text(self):
        """Test text embedding."""
        text = "Python developer with 5 years experience"
        embedding = self.engine.embed_text(text)
        
        assert embedding is not None
        assert len(embedding) > 0
    
    def test_semantic_similarity(self):
        """Test semantic similarity calculation."""
        text1 = "Python developer with database experience"
        text2 = "Backend engineer with SQL knowledge"
        
        emb1 = self.engine.embed_text(text1)
        emb2 = self.engine.embed_text(text2)
        similarity = self.engine.semantic_similarity(emb1, emb2)
        
        assert 0 <= similarity <= 1


class TestRankingEngine:
    """Test RankingEngine component."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = RankingEngine()
    
    def test_calculate_skill_match(self):
        """Test skill match calculation."""
        required_skills = ["Python", "Django"]
        candidate = Candidate(
            id="cand_001",
            name="John Doe",
            email="john@example.com",
            skills=[Skill(name=s, proficiency="Expert", years=5) for s in ["Python", "Django", "PostgreSQL"]]
        )
        
        score = self.engine.calculate_skill_match(candidate, required_skills)
        
        assert score == 1.0
    
    def test_calculate_experience_fit(self):
        """Test experience fit calculation."""
        candidate = Candidate(
            id="cand_001",
            name="John Doe",
            email="john@example.com",
            experience=[Experience(title="Dev", company="C", start_date="2020-01", description="desc", duration_years=7)]
        )
        job = JobDescription(
            id="jd_001",
            title="Dev",
            company="C",
            description="desc",
            years_required=5,
            raw_text="desc"
        )
        
        score = self.engine.calculate_experience_fit(candidate, job)
        
        assert score == 1.0
    
    def test_rank_candidates(self):
        """Test ranking candidates."""
        job = JobDescription(
            id="jd_001",
            title="Senior Developer",
            company="TechCorp",
            description="Test job",
            years_required=5,
            required_skills=["Python", "Django"],
            raw_text="Test"
        )
        
        candidate = Candidate(
            id="cand_001",
            name="John Doe",
            email="john@example.com",
            skills=[
                Skill(name="Python", proficiency="Expert", years=7),
                Skill(name="Django", proficiency="Advanced", years=5)
            ],
            experience=[
                Experience(
                    title="Senior Dev",
                    company="Company",
                    start_date="2019-01",
                    end_date="present",
                    duration_years=5,
                    description="Senior Dev"
                )
            ]
        )
        
        rankings = self.engine.rank_candidates([candidate], job)
        
        assert len(rankings) == 1
        assert rankings[0].rank == 1


class TestBiasDetector:
    """Test BiasDetector component."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.detector = BiasDetector()
    
    def test_calculate_fairness_score(self):
        """Test fairness score calculation."""
        result1 = RankingResult(
            candidate_id="cand_001",
            candidate_name="John Doe",
            rank=1,
            overall_score=90,
            score=90,
            breakdown=ScoreBreakdown(
                semantic_similarity=0.9,
                skill_match=0.9,
                experience_match=0.9,
                education_match=0.9
            ),
            bias_audit=BiasAudit()
        )
        
        result2 = RankingResult(
            candidate_id="cand_002",
            candidate_name="Jane Smith",
            rank=2,
            overall_score=85,
            score=85,
            breakdown=ScoreBreakdown(
                semantic_similarity=0.85,
                skill_match=0.85,
                experience_match=0.85,
                education_match=0.85
            ),
            bias_audit=BiasAudit()
        )
        
        fairness = self.detector.calculate_fairness_score([result1, result2])
        
        assert 0 <= fairness <= 1


class TestPipeline:
    """Test RecruitmentPipeline orchestration."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.pipeline = RecruitmentPipeline()
    
    def test_pipeline_initialization(self):
        """Test pipeline initializes correctly."""
        assert self.pipeline.job_analyzer is not None
        assert self.pipeline.candidate_profiler is not None
        assert self.pipeline.embedding_engine is not None
        assert self.pipeline.ranking_engine is not None
        assert self.pipeline.bias_detector is not None
    
    def test_match_candidates(self):
        """Test end-to-end matching."""
        job = JobDescription(
            id="jd_001",
            title="Senior Python Developer",
            company="TechCorp",
            description="Looking for experienced Python developer",
            years_required=5,
            required_skills=["Python", "Django"],
            raw_text="Test"
        )
        
        candidate = Candidate(
            id="cand_001",
            name="John Doe",
            email="john@example.com",
            skills=[Skill(name="Python", proficiency="Expert", years=7)],
            experience=[
                Experience(
                    title="Senior Dev",
                    company="Company",
                    start_date="2019-01",
                    end_date="present",
                    duration_years=5,
                    description="Senior Dev"
                )
            ]
        )
        
        batch = self.pipeline.match_candidates(
            job,
            [candidate],
            check_bias=False
        )
        
        assert len(batch.results) == 1
        assert batch.results[0].rank == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
