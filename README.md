# AI Recruiter - Intelligent Candidate Ranking System

A comprehensive AI-powered recruitment platform that intelligently matches and ranks candidates against job descriptions using multi-dimensional analysis, semantic matching, and fairness detection.

## Features

- **Job Description Analysis**: Deep analysis of job requirements, skills, and complexity
- **Candidate Profiling**: Multi-dimensional candidate assessment including skills, experience, and soft skills
- **Semantic Matching**: Vector embeddings for intelligent semantic similarity
- **Intelligent Ranking**: Multi-criteria scoring with customizable weights
- **Bias Detection**: Identifies and mitigates demographic, experience, and education biases
- **Fairness Constraints**: Apply fairness rules to ensure equitable evaluation
- **RESTful API**: FastAPI-based API for easy integration
- **Extensible Architecture**: Modular design for easy customization

## Project Structure

```
ai_recruiter/
├── core/
│   ├── job_analyzer.py          # Job description analysis
│   ├── candidate_profiler.py     # Candidate profiling & analysis
│   ├── embedding_engine.py       # Vector embeddings & semantic search
│   ├── ranking_engine.py         # Intelligent scoring & ranking
│   └── bias_detector.py          # Bias detection & mitigation
├── models/
│   ├── job_description.py        # JobDescription model
│   ├── candidate.py              # Candidate model
│   └── ranking_result.py         # RankingResult model
├── utils/
│   ├── text_processor.py         # Text processing utilities
│   └── feature_extractor.py      # Feature engineering
├── data/
│   ├── sample_jd.json            # Sample job description
│   ├── sample_candidates.json    # Sample candidate profiles
│   └── sample_submission.csv     # Sample ranking output
├── config/
│   └── settings.py               # Configuration
├── pipeline.py                   # Main orchestration pipeline
├── api.py                        # FastAPI endpoints
└── requirements.txt              # Dependencies
```

## Installation

1. **Clone the repository**
```bash
cd AI_Recruiter
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Quick Start

### Using the Pipeline Directly

```python
from models.job_description import JobDescription, SalaryRange
from models.candidate import Candidate, Skill, Experience, Education
from pipeline import RecruitmentPipeline

# Initialize pipeline
pipeline = RecruitmentPipeline()

# Create job description
job = JobDescription(
    id="jd_001",
    title="Senior Python Developer",
    company="TechCorp",
    description="Looking for experienced Python developer...",
    required_skills=["Python", "Django", "PostgreSQL", "Docker"],
    experience_level="Senior",
    years_required=5,
    location="Remote",
    raw_text="Full job description text"
)

# Create candidates
candidate1 = Candidate(
    id="cand_001",
    name="Alice Johnson",
    email="alice@example.com",
    phone="+1-555-0101",
    location="SF",
    summary="7 years backend development experience",
    skills=[
        Skill(name="Python", proficiency="Expert", years=7),
        Skill(name="Django", proficiency="Advanced", years=5),
    ],
    experience=[
        Experience(
            title="Senior Backend Engineer",
            company="CloudTech",
            start_date="2021-06",
            end_date="present",
            duration_years=3,
            description="Led microservices development"
        )
    ],
    education=[
        Education(
            degree="Bachelor",
            field="Computer Science",
            university="UC Berkeley",
            graduation_year=2017
        )
    ],
    raw_resume="Full resume text"
)

# Match candidates
batch = pipeline.match_candidates(
    job_description=job,
    candidates=[candidate1],
    weights={
        'semantic_similarity': 0.25,
        'skill_match': 0.30,
        'experience_match': 0.25,
        'education_match': 0.20
    },
    check_bias=True
)

# Print results
for result in batch.results:
    print(f"\nRank {result.rank}: {result.candidate_name}")
    print(f"Score: {result.overall_score:.2f}%")
    print(f"Reasoning: {result.reasoning}")
    print(f"Strengths: {', '.join(result.key_strengths)}")
    print(f"Gaps: {', '.join(result.gaps)}")

# Check fairness
print(f"\nFairness Score: {batch.fairness_score:.2f}")
print(f"Bias Warnings: {batch.bias_warnings}")
```

### Using the FastAPI

1. **Start the server**
```bash
python -m uvicorn ai_recruiter.api:app --reload
```

2. **API Endpoints**

- `POST /api/v1/match` - Match and rank candidates
- `POST /api/v1/jobs/analyze` - Analyze job description
- `POST /api/v1/candidates/profile` - Profile a candidate
- `PUT /api/v1/config/weights` - Update scoring weights
- `GET /api/v1/metrics` - Get pipeline metrics
- `GET /health` - Health check

## Key Components

### JobAnalyzer
- Extracts required skills from job descriptions
- Identifies job complexity and seniority level
- Analyzes job responsibilities and requirements

### CandidateProfiler
- Analyzes technical skills with proficiency levels
- Evaluates work experience and progression
- Assesses soft skills from descriptions
- Calculates profile completeness

### EmbeddingEngine
- Creates semantic embeddings for job descriptions and resumes
- Computes similarity scores using cosine similarity
- Caches embeddings for performance

### RankingEngine
- Calculates multi-dimensional match scores:
  - Skill match (30%)
  - Experience fit (25%)
  - Semantic similarity (25%)
  - Education match (20%)
- Customizable weights
- Detailed score breakdown

### BiasDetector
- Detects demographic biases
- Identifies experience and education biases
- Calculates fairness scores
- Suggests mitigation strategies

## Scoring Criteria

Each candidate is evaluated across four key dimensions:

1. **Skill Match (30%)**: How many required skills the candidate has
2. **Experience Match (25%)**: Years of experience vs requirement
3. **Semantic Similarity (25%)**: Semantic match between resume and job
4. **Education Match (20%)**: Educational qualification alignment

Weights can be customized based on organizational priorities.

## Bias Detection Features

- **Demographic Diversity**: Checks for diversity in top candidates
- **Experience Bias**: Identifies if experience is overweighted
- **Education Bias**: Detects prestige institution bias
- **Fairness Score**: 0-1 score indicating overall fairness (higher is better)

## Sample Data

The `data/` folder contains sample datasets:

- `sample_jd.json`: Senior Python Developer position
- `sample_candidates.json`: 3 candidate profiles with varying match levels
- `sample_submission.csv`: Expected ranking output format

## Configuration

Adjust scoring weights in pipeline initialization:

```python
weights = {
    'semantic_similarity': 0.25,
    'skill_match': 0.30,
    'experience_match': 0.25,
    'education_match': 0.20
}

batch = pipeline.match_candidates(job, candidates, weights=weights)
```

## Performance Notes

- **Embedding**: Uses simple TF-IDF approach (can be upgraded to transformer models)
- **Scalability**: Suitable for 100-1000 candidates per job
- **Latency**: ~100ms per candidate on CPU
- **Caching**: Embeddings are cached for repeated queries

## Future Enhancements

- [ ] Integration with advanced NLP models (BERT, GPT)
- [ ] Machine learning-based ranking optimization
- [ ] Resume parsing from PDF/DOCX formats
- [ ] Database backend for storing results
- [ ] Advanced analytics dashboard
- [ ] Custom fairness constraints
- [ ] Integration with ATS systems

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=ai_recruiter
```

## Contributing

To contribute improvements:

1. Create a feature branch
2. Make your changes
3. Add tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Contact

For questions or support, please reach out to the development team.
