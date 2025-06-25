# Candidate Database System

The Robot Recruiter candidate database system provides persistent storage for repository analysis results, contributor profiles, and candidate data. This replaces the CSV file output with a structured database that enables advanced querying, relationship management, and data persistence.

## Overview

The database system consists of:

- **SQLAlchemy ORM models** for data structure
- **DatabaseManager class** for database operations
- **CLI tools** for database management
- **PostgreSQL support** (recommended) with SQLite fallback for testing

## Database Schema

### Core Tables

#### `repositories`
Stores repository information and metadata:
- Repository details (name, description, language, etc.)
- GitHub statistics (stars, forks, issues)
- Classification results
- Analysis timestamps

#### `contributors`
Individual contributor information:
- GitHub profile data
- Contribution counts
- Contact information
- Analysis metadata

#### `contributor_roles`
Role classifications for contributors:
- Code, documentation, testing scores
- Confidence levels
- Timestamps

#### `contributor_skills`
Skills and expertise detected:
- Skill names and categories
- Confidence scores
- Evidence for skill detection

#### `candidate_profiles`
Aggregated candidate profiles:
- Combined data from multiple repositories
- Total contribution statistics
- Primary classifications and skills
- Expertise scores

### Analysis Tables

#### `analysis_sessions`
Metadata for analysis runs:
- Session information
- Analysis targets and results
- Error tracking
- Configuration used

#### `session_repositories`
Many-to-many relationship between sessions and repositories.

## Setup

### 1. Database Installation

#### PostgreSQL (Recommended)
```bash
# Install PostgreSQL
brew install postgresql  # macOS
sudo apt-get install postgresql postgresql-contrib  # Ubuntu

# Create database
createdb robot_recruiter_candidates
```

#### SQLite (Development/Testing)
```bash
# No installation needed - SQLite is included with Python
```

### 2. Environment Configuration

Set the database URL environment variable:

```bash
# PostgreSQL
export CANDIDATE_DB_URL="postgresql://username:password@localhost/robot_recruiter_candidates"

# SQLite (for development)
export CANDIDATE_DB_URL="sqlite:///candidates.db"
```

### 3. Initialize Database

```bash
# Initialize tables
python -m src.github_talent_intelligence.candidate_cli init-db
```

## Usage

### CLI Commands

#### Initialize Database
```bash
python -m src.github_talent_intelligence.candidate_cli init-db
```

#### Import Analysis Results
```bash
python -m src.github_talent_intelligence.candidate_cli import-analysis \
  --analysis-dir caliptra_test_output \
  --session-name "Caliptra Analysis 2025-06-21"
```

#### List Candidates
```bash
# List first 10 candidates
python -m src.github_talent_intelligence.candidate_cli list-candidates

# List with pagination
python -m src.github_talent_intelligence.candidate_cli list-candidates \
  --limit 20 --offset 10
```

#### Get Candidate Details
```bash
# By GitHub ID
python -m src.github_talent_intelligence.candidate_cli get-candidate \
  --github-id 2548962

# By username (when implemented)
python -m src.github_talent_intelligence.candidate_cli get-candidate \
  --login bluegate010
```

#### Search Candidates
```bash
# Search by location
python -m src.github_talent_intelligence.candidate_cli search-candidates \
  --location "Mountain View"

# Search by company
python -m src.github_talent_intelligence.candidate_cli search-candidates \
  --company "Google"

# Search by classification
python -m src.github_talent_intelligence.candidate_cli search-candidates \
  --classification "Security"

# Search with minimum criteria
python -m src.github_talent_intelligence.candidate_cli search-candidates \
  --min-contributions 50 --min-followers 100
```

#### Database Statistics
```bash
python -m src.github_talent_intelligence.candidate_cli stats
```

### Programmatic Usage

#### Basic Database Operations

```python
from src.github_talent_intelligence.candidate_db import DatabaseManager

# Initialize database manager
db_manager = DatabaseManager("postgresql://localhost/robot_recruiter_candidates")

# Create tables
db_manager.create_tables()

# Save analysis results
session_id = db_manager.save_repository_analysis(
    repo_data, 
    contributors_data,
    "My Analysis Session"
)

# Get candidate profiles
candidates = db_manager.get_candidate_profiles(limit=10)

# Search candidates
results = db_manager.search_candidates(
    location="San Francisco",
    company="Google",
    classification="Security"
)
```

#### Working with Sessions

```python
# Get database session
session = db_manager.get_session()

try:
    # Query repositories
    repos = session.query(Repository).filter_by(classification="Security").all()
    
    # Query contributors with roles
    contributors = session.query(Contributor).join(ContributorRole).all()
    
    # Complex queries
    top_contributors = session.query(Contributor)\
        .filter(Contributor.contributions > 50)\
        .order_by(Contributor.contributions.desc())\
        .limit(10)\
        .all()
        
finally:
    session.close()
```

## Integration with Analysis Pipeline

### Option 1: Direct Database Storage

Modify the analysis CLI to save directly to database:

```python
# In cli.py, add database option
@click.option('--save-to-db', is_flag=True, help='Save results to database')
@click.option('--database-url', envvar='CANDIDATE_DB_URL', 
              default='postgresql://localhost/robot_recruiter_candidates')

# After analysis, save to database
if save_to_db:
    db_manager = DatabaseManager(database_url)
    db_manager.save_repository_analysis(repo_data, contributors_data)
```

### Option 2: Import Existing Results

Import analysis results from existing CSV/JSON files:

```bash
# Import Caliptra analysis
python -m src.github_talent_intelligence.candidate_cli import-analysis \
  --analysis-dir caliptra_test_output \
  --session-name "Caliptra Security Analysis"
```

## Data Migration

### From CSV to Database

```python
import pandas as pd
from src.github_talent_intelligence.candidate_db import DatabaseManager

# Load CSV data
contributors_df = pd.read_csv('contributors.csv')
repos_df = pd.read_csv('repositories.csv')

# Initialize database
db_manager = DatabaseManager("postgresql://localhost/robot_recruiter_candidates")

# Convert and save data
for _, row in repos_df.iterrows():
    repo_data = row.to_dict()
    # Convert to proper format and save
    db_manager.save_repository_analysis(repo_data, contributors_data)
```

## Performance Considerations

### Indexing

Create indexes for common queries:

```sql
-- Contributor lookups
CREATE INDEX idx_contributors_github_id ON contributors(github_id);
CREATE INDEX idx_contributors_login ON contributors(login);
CREATE INDEX idx_contributors_company ON contributors(company);
CREATE INDEX idx_contributors_location ON contributors(location);

-- Repository queries
CREATE INDEX idx_repositories_classification ON repositories(classification);
CREATE INDEX idx_repositories_language ON repositories(language);

-- Analysis sessions
CREATE INDEX idx_analysis_sessions_target ON analysis_sessions(target);
CREATE INDEX idx_analysis_sessions_status ON analysis_sessions(status);
```

### Query Optimization

- Use pagination for large result sets
- Implement caching for frequently accessed data
- Consider materialized views for complex aggregations
- Use database-level filtering instead of application-level filtering

## Backup and Maintenance

### Regular Backups

```bash
# PostgreSQL backup
pg_dump robot_recruiter_candidates > backup_$(date +%Y%m%d).sql

# Restore
psql robot_recruiter_candidates < backup_20250621.sql
```

### Data Cleanup

```python
# Remove old analysis sessions
session.query(AnalysisSession)\
    .filter(AnalysisSession.started_at < datetime.now() - timedelta(days=90))\
    .delete()

# Archive old contributor data
# (Implement based on your retention policy)
```

## Testing

Run the database tests:

```bash
# Run all tests
pytest tests/test_candidate_db.py -v

# Run with coverage
pytest tests/test_candidate_db.py --cov=src.github_talent_intelligence.candidate_db
```

## Future Enhancements

### Planned Features

1. **Advanced Search**: Full-text search, skill matching, expertise scoring
2. **Data Aggregation**: Automated candidate profile creation from multiple repositories
3. **API Endpoints**: REST API for database operations
4. **Analytics Dashboard**: Web interface for data visualization
5. **Integration**: Connect with ATS systems, LinkedIn, etc.
6. **Machine Learning**: Automated candidate scoring and recommendations

### Schema Extensions

- **Candidate Interactions**: Track outreach, responses, interviews
- **Skill Validation**: Verify skills through code analysis
- **Reputation Scoring**: GitHub activity, community contributions
- **Geographic Data**: Enhanced location and timezone information
- **Social Networks**: GitHub connections, collaboration patterns

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check database URL and credentials
2. **Permission Errors**: Ensure database user has proper permissions
3. **Import Failures**: Verify JSON/CSV file format and data integrity
4. **Performance Issues**: Add indexes, optimize queries, consider partitioning

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues and questions:

1. Check the test files for usage examples
2. Review the database schema documentation
3. Run tests to verify functionality
4. Check logs for error details 