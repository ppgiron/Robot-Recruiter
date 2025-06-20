# GitHub Talent Intelligence Platform

A comprehensive platform for analyzing GitHub repositories, contributors, and technical talent for AI-powered recruiting applications.

## Features

- **Repository Analysis**: Scrape and analyze GitHub repositories from organizations or users
- **Contributor Intelligence**: Deep analysis of contributor roles, skills, and activity patterns
- **AI-Powered Classification**: ML/NLP-based categorization of repositories and contributors
- **Talent Scoring**: Automated assessment of technical skills and expertise
- **Data Export**: Export analysis results in multiple formats (JSON, CSV)
- **API Integration**: Ready-to-integrate with AI recruiting platforms

## Categories

The platform classifies repositories and contributors into these categories:

- **BlockOps**: Infrastructure, DevOps, CI/CD, Kubernetes, monitoring
- **Staking**: Validator nodes, consensus, delegation management
- **Protocol**: Core blockchain protocols, networking, state management
- **Hardware**: FPGA, ASIC, Verilog, hardware security
- **Security**: Cryptography, vulnerability research, security audits

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up GitHub token**:
   ```bash
   export GITHUB_TOKEN=your_github_token
   # or create a .env file with GITHUB_TOKEN=your_token
   ```

3. **Analyze an organization**:
   ```bash
   python talent_analyzer.py --org ChainSafe --output results
   ```

4. **Analyze specific repositories**:
   ```bash
   python talent_analyzer.py --repos "owner/repo1,owner/repo2" --output results
   ```

## Integration with AI Recruiting

This platform is designed to integrate seamlessly with AI recruiting applications:

- **Talent Discovery**: Find skilled contributors across GitHub
- **Skill Assessment**: Automated evaluation of technical expertise
- **Role Matching**: Match candidates to specific technical roles
- **Activity Analysis**: Understand contributor engagement and patterns

## API Usage

```python
from talent_intelligence import TalentAnalyzer

# Initialize analyzer
analyzer = TalentAnalyzer(github_token="your_token")

# Analyze organization
results = analyzer.analyze_organization("ChainSafe")

# Get contributor insights
contributors = analyzer.get_contributor_insights("owner/repo")

# Export for recruiting platform
recruiting_data = analyzer.export_for_recruiting(results)
```

## Output Formats

- **JSON**: Complete analysis data for programmatic use
- **CSV**: Tabular data for spreadsheet analysis
- **Recruiting Format**: Optimized for AI recruiting platforms

## Configuration

Create a `config.yaml` file to customize:

```yaml
github:
  token: ${GITHUB_TOKEN}
  rate_limit_delay: 0.1

analysis:
  use_nlp: true
  classify_roles: true
  max_commits_per_repo: 100

categories:
  custom_keywords:
    - "your_keyword"
    - "another_keyword"
```

## License

MIT License - see LICENSE file for details. 