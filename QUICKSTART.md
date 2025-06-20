# Quick Start Guide - GitHub Talent Intelligence Platform

Get up and running with the GitHub Talent Intelligence Platform in minutes!

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### 2. Set Up GitHub Token

```bash
# Option 1: Environment variable
export GITHUB_TOKEN=your_github_token_here

# Option 2: Create .env file
echo "GITHUB_TOKEN=your_github_token_here" > .env
```

### 3. Run Interactive Setup

```bash
python talent_analyzer.py setup
```

This will guide you through the setup process and test your configuration.

## 🎯 Quick Examples

### Analyze an Organization

```bash
# Analyze all repositories in an organization
python talent_analyzer.py analyze --org ChainSafe --output results

# Use specific output formats
python talent_analyzer.py analyze --org ethereum --formats json,csv --output results
```

### Get Contributor Insights

```bash
# Analyze contributors to a specific repository
python talent_analyzer.py contributors owner/repo --output insights.json
```

### AI Recruiting Integration

```bash
# Run the AI recruiting integration example
python example_integration.py
```

## 🔧 Programmatic Usage

### Basic Analysis

```python
from talent_intelligence import TalentAnalyzer

# Initialize analyzer
analyzer = TalentAnalyzer()

# Analyze organization
repositories = analyzer.analyze_organization("ChainSafe")

# Save results
analyzer.save_results(repositories, "results", ["json", "csv"])
```

### AI Recruiting Integration

```python
from recruiting_integration import RecruitingIntegration

# Initialize integration
integration = RecruitingIntegration()

# Discover talent
talent_results = integration.discover_talent(
    organizations=["ChainSafe", "ethereum"],
    skills=["Python", "Go", "Rust"],
    min_contributions=20
)

# Assess specific candidate
assessment = integration.assess_candidate("username")

# Match to role
matches = integration.match_candidates_to_role(
    role_requirements={
        'title': 'DevOps Engineer',
        'skills': ['Docker', 'Kubernetes', 'Python'],
        'experience_level': 'mid'
    },
    candidates=talent_results['candidates']
)
```

## 📊 Output Formats

The platform generates multiple output formats:

- **JSON**: Complete analysis data for programmatic use
- **CSV**: Tabular data for spreadsheet analysis
- **Recruiting**: Optimized format for AI recruiting platforms
- **HTML**: Human-readable reports

## 🎨 Configuration

Customize the platform by editing `config.yaml`:

```yaml
github:
  rate_limit_delay: 0.1  # API call delay

analysis:
  use_nlp: true          # Use AI classification
  classify_roles: true   # Analyze contributor roles

recruiting:
  target_skills:         # Skills to look for
    - "Python"
    - "Go"
    - "Blockchain"
```

## 🔍 What You Get

### Repository Analysis
- **Classification**: AI-powered categorization (BlockOps, Staking, Protocol, etc.)
- **Metrics**: Stars, forks, contributors, activity
- **Topics**: GitHub topics and technical indicators

### Contributor Intelligence
- **Skills**: Automated skill detection
- **Expertise**: Scoring based on contributions and activity
- **Roles**: Analysis of contribution patterns
- **Social Proof**: Followers, public repos, community engagement

### AI Recruiting Features
- **Talent Discovery**: Find skilled contributors across GitHub
- **Role Matching**: Match candidates to specific job requirements
- **Candidate Assessment**: Comprehensive evaluation of technical talent
- **ATS Integration**: Export data for applicant tracking systems

## 🚨 Rate Limits

GitHub API has rate limits:
- **Authenticated**: 5,000 requests/hour
- **Unauthenticated**: 60 requests/hour

The platform automatically handles rate limiting with configurable delays.

## 🐛 Troubleshooting

### Common Issues

1. **GitHub Token Error**
   ```bash
   # Check token is set
   echo $GITHUB_TOKEN
   
   # Or check .env file
   cat .env
   ```

2. **Rate Limit Errors**
   ```bash
   # Increase delay in config.yaml
   github:
     rate_limit_delay: 0.2
   ```

3. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt --upgrade
   ```

### Getting Help

- Check the logs for detailed error messages
- Verify your GitHub token has the necessary permissions
- Ensure you're not hitting GitHub API rate limits

## 📈 Next Steps

1. **Customize Categories**: Add your own classification rules
2. **Integrate with ATS**: Export data to your recruiting platform
3. **Build Workflows**: Create automated talent discovery pipelines
4. **Scale Up**: Analyze multiple organizations and repositories

## 🎉 Success!

You're now ready to discover and analyze GitHub talent for your AI recruiting application!

For more advanced usage, check out the full documentation and examples. 