# Quick Start Guide - Robot Recruiter

Get up and running with Robot Recruiter in minutes with secure API key management!

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### 2. Set Up Secure API Keys (Recommended)

```bash
# Set up 1Password integration for secure key storage
python -m src.github_talent_intelligence.cli setup-1password
```

This will:
- Check if 1Password CLI is available
- Detect existing API keys from environment variables
- Store them securely in 1Password
- Test the integration

### 3. Alternative: Environment Variables (for CI/CD)

```bash
# For CI/CD or development only
export GITHUB_TOKEN=your_github_token_here
export OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Run Interactive Setup

```bash
python -m src.github_talent_intelligence.cli setup
```

This will guide you through the setup process and test your configuration.

## 🔐 Security Best Practices

### ✅ Secure Setup (Recommended)

1. **Use 1Password Integration**:
   ```bash
   python -m src.github_talent_intelligence.cli setup-1password
   ```

2. **Remove Plain Text Files**:
   ```bash
   # Remove any .env files containing API keys
   rm .env
   rm -f .github_token
   ```

3. **Verify Security**:
   ```bash
   # Test that keys are retrieved from 1Password
   python -c "
   from src.github_talent_intelligence.token_manager import get_github_token, get_openai_api_key
   print('✅ GitHub Token:', get_github_token()[:10] + '...')
   print('✅ OpenAI Key:', get_openai_api_key()[:10] + '...')
   "
   ```

### ❌ Avoid Plain Text Storage

Never store API keys in plain text files:
```bash
# DON'T do this
echo "GITHUB_TOKEN=your_token" > .env
echo "OPENAI_API_KEY=your_key" >> .env
```

## 🎯 Quick Examples

### Analyze an Organization

```bash
# Analyze all repositories in an organization
python -m src.github_talent_intelligence.cli analyze --org ChainSafe --output results

# Use specific output formats
python -m src.github_talent_intelligence.cli analyze --org ethereum --formats json,csv --output results
```

### Get Contributor Insights

```bash
# Analyze contributors to a specific repository
python -m src.github_talent_intelligence.cli contributors owner/repo --output insights.json
```

### AI Recruiting Integration

```bash
# Run the AI recruiting integration example
python examples/ai_recruiting_integration.py
```

## 🔧 Programmatic Usage

### Basic Analysis

```python
from src.github_talent_intelligence import TalentAnalyzer

# Initialize analyzer (keys automatically retrieved from 1Password)
analyzer = TalentAnalyzer()

# Analyze organization
repositories = analyzer.analyze_organization("ChainSafe")

# Save results
analyzer.save_results(repositories, "results", ["json", "csv"])
```

### AI Recruiting Integration

```python
from src.github_talent_intelligence import RecruitingIntegration

# Initialize integration (keys automatically retrieved from 1Password)
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

### Manual Key Retrieval

```python
from src.github_talent_intelligence.token_manager import get_github_token, get_openai_api_key

# Get keys directly
github_token = get_github_token()
openai_key = get_openai_api_key()
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

1. **API Key Error**
   ```bash
   # Check if keys are accessible from 1Password
   python -c "
   from src.github_talent_intelligence.token_manager import get_github_token, get_openai_api_key
   get_github_token()
   get_openai_api_key()
   print('✅ Keys retrieved successfully')
   "
   ```

2. **1Password CLI Issues**
   ```bash
   # Check 1Password CLI installation
   op --version
   
   # Sign in if needed
   op signin
   ```

3. **Rate Limit Errors**
   ```bash
   # Increase delay in config.yaml
   github:
     rate_limit_delay: 0.2
   ```

4. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt --upgrade
   ```

### Getting Help

- Check the logs for detailed error messages
- Verify your API keys have the necessary permissions
- Ensure you're not hitting GitHub API rate limits
- See [1Password Integration Guide](docs/1password_integration.md) for detailed setup

## 📈 Next Steps

1. **Customize Categories**: Add your own classification rules
2. **Integrate with ATS**: Export data to your recruiting platform
3. **Build Workflows**: Create automated talent discovery pipelines
4. **Scale Up**: Analyze multiple organizations and repositories
5. **Team Setup**: Share 1Password items with team members

## 🔒 Security Checklist

- [ ] API keys stored in 1Password
- [ ] No plain text `.env` files with secrets
- [ ] `.gitignore` includes `.env` and `.github_token`
- [ ] 1Password CLI authenticated
- [ ] Keys tested and working
- [ ] Team members have access to 1Password items (if applicable)

## 🎉 Success!

You're now ready to discover and analyze GitHub talent for your AI recruiting application!

For more advanced usage, check out the full documentation and examples. 