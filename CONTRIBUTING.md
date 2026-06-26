# Development Guide - AI Recruiter

## Getting Started

### Prerequisites
- Python 3.9+
- pip or conda
- Virtual environment (recommended)

### Installation

1. **Clone and navigate to project**
```bash
cd AI_Recruiter
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create data directories**
```bash
mkdir -p data results logs
```

## Project Architecture

### Layer 1: Models (`ai_recruiter/models/`)
Data structures with validation:
- `JobDescription`: Job posting with skills, requirements, salary
- `Candidate`: Resume profile with experience, skills, education
- `RankingResult`: Scoring breakdown and ranking outputs

### Layer 2: Utils (`ai_recruiter/utils/`)
Supporting functions:
- `TextProcessor`: Text cleaning, tokenization, skill extraction, keyword extraction
- `FeatureExtractor`: Advanced feature engineering (if implemented)

### Layer 3: Core (`ai_recruiter/core/`)
Analysis engines:
- `JobAnalyzer`: Extracts insights from job descriptions
- `CandidateProfiler`: Multi-dimensional candidate analysis
- `EmbeddingEngine`: Vector embeddings and semantic similarity
- `RankingEngine`: Multi-criteria scoring and ranking
- `BiasDetector`: Fairness analysis and bias detection

### Layer 4: API & Pipeline
- `pipeline.py`: Orchestrates all components end-to-end
- `api.py`: FastAPI REST endpoints

## Running the Application

### Test with Sample Data
```bash
cd ai_recruiter
python main.py
```

This will:
1. Load sample job description and candidates
2. Run complete matching pipeline
3. Print formatted rankings with bias analysis
4. Save results to `results/ranking_results.json`

### Start API Server
```bash
python -m uvicorn ai_recruiter.api:app --reload --host 0.0.0.0 --port 8000
```

Then visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Health Check
```
GET /health
```

### Matching
```
POST /api/v1/match
Body: {
  "job_description": {...},
  "candidates": [{...}],
  "weights": {...},  # optional
  "check_bias": true  # optional
}
```

### Analysis
```
POST /api/v1/jobs/analyze
POST /api/v1/candidates/profile
```

### Configuration
```
PUT /api/v1/config/weights
GET /api/v1/metrics
```

## Code Style

- **Language**: Python 3.9+
- **Type Hints**: Required for all functions
- **Docstrings**: Google-style docstrings required
- **Formatting**: Black formatter recommended
- **Linting**: flake8 recommended

### Example Function:
```python
def calculate_score(candidate_exp: int, required_exp: int) -> float:
    """
    Calculate experience match score.
    
    Args:
        candidate_exp: Years of candidate experience
        required_exp: Years required for job
        
    Returns:
        float: Score between 0 and 1
    """
    if required_exp <= 0:
        return 1.0
    
    return min(1.0, candidate_exp / required_exp)
```

## Data Format

### Job Description JSON
```json
{
  "id": "jd_001",
  "title": "Senior Developer",
  "company": "TechCorp",
  "description": "Looking for...",
  "required_skills": ["Python", "Docker"],
  "nice_to_have_skills": ["Kubernetes"],
  "years_required": 5,
  "experience_level": "Senior",
  "location": "Remote",
  "salary_range": {"min": 100000, "max": 150000, "currency": "USD"},
  "raw_text": "Full JD text"
}
```

### Candidate JSON
```json
{
  "id": "cand_001",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-0123",
  "location": "SF",
  "summary": "5+ years experience...",
  "skills": [
    {
      "name": "Python",
      "proficiency": "Expert",
      "years": 5,
      "endorsements": 10
    }
  ],
  "experience": [
    {
      "title": "Senior Dev",
      "company": "Company",
      "start_date": "2021-01",
      "end_date": "present",
      "duration_years": 3,
      "description": "...",
      "skills_used": ["Python", "Docker"]
    }
  ],
  "education": [
    {
      "degree": "Bachelor",
      "field": "Computer Science",
      "university": "UC Berkeley",
      "graduation_year": 2019
    }
  ],
  "raw_resume": "Full resume text"
}
```

## Adding New Features

### Adding a New Analysis Engine

1. Create new file in `core/` directory
2. Inherit from base analysis class (if exists) or create standalone
3. Implement `analyze()` method
4. Add to `pipeline.py` initialization
5. Update `__init__.py`

Example:
```python
# core/new_analyzer.py
class NewAnalyzer:
    def analyze(self, input_data):
        """Analyze input and return results."""
        return {...}
```

### Extending Scoring Logic

1. Modify `RankingEngine.calculate_*` methods
2. Update weights in `config/settings.py`
3. Update `ScoreBreakdown` model if needed
4. Test with sample data

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=ai_recruiter

# Run specific test
pytest tests/test_ranking.py::test_skill_match
```

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Print Intermediate Results
```python
# In pipeline.py
print(f"Job analysis: {jd_analysis}")
print(f"Candidate profiles: {candidate_profiles}")
print(f"Rankings: {rankings}")
```

### Use Python Debugger
```python
import pdb
pdb.set_trace()  # Set breakpoint

# Then step through: n (next), s (step into), c (continue)
```

## Performance Optimization

### Embedding Caching
- Embeddings are cached automatically using MD5 hashes
- Cache size configured in `settings.py`
- Clear cache by creating new `EmbeddingEngine` instance

### Batch Processing
- Pipeline processes candidates sequentially
- For large batches (1000+), implement batch processing:
  ```python
  for batch in chunks(candidates, 100):
      results.extend(pipeline.match_candidates(job, batch))
  ```

### Database Caching (Future)
- Store embeddings in database for production
- Implement Redis for distributed caching

## Common Issues & Solutions

### Issue: Import Errors
**Solution**: Ensure you're in the correct directory and Python path includes parent folder
```bash
cd ai_recruiter
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python main.py
```

### Issue: Module Not Found
**Solution**: Install missing packages
```bash
pip install -r requirements.txt
```

### Issue: Scoring Results Unexpected
**Solution**: Check weights sum to 1.0 and verify scoring logic in `RankingEngine`

### Issue: Bias Detection Not Working
**Solution**: Ensure `check_bias=True` in pipeline call and candidates have sufficient data

## Contributing Code

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes with tests
3. Format code: `black ai_recruiter/`
4. Lint code: `flake8 ai_recruiter/`
5. Run tests: `pytest`
6. Create pull request with description

## Documentation

- **README.md**: User-facing documentation
- **CONTRIBUTING.md**: This file
- **Docstrings**: Code-level documentation
- **Inline Comments**: Complex logic explanation

## Resources

- **Bias in AI**: https://fairmlbook.org
- **Vector Embeddings**: https://huggingface.co/docs/transformers/
- **Recruitment Analytics**: https://www.eeoc.gov/
- **Python Best Practices**: https://pep8.org/

## Contact

For questions or issues, please reach out to the development team.
