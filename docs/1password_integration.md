# 1Password Integration for Robot Recruiter

Robot Recruiter now supports secure API key storage using 1Password CLI, providing enterprise-grade security for your GitHub Personal Access Tokens and OpenAI API keys.

## 🔐 Why Use 1Password Integration?

- **Secure Storage**: API keys are encrypted and stored in 1Password vaults
- **No Plain Text Files**: Eliminates the security risk of storing keys in files
- **Access Control**: Leverage 1Password's team sharing and access controls
- **Audit Trail**: Track who accessed keys and when
- **Automatic Rotation**: Easy key rotation and management
- **Multiple Keys**: Securely manage both GitHub tokens and OpenAI API keys

## 📋 Prerequisites

1. **1Password CLI installed**: [Installation Guide](https://developer.1password.com/docs/cli/get-started/)
2. **1Password account**: Personal or team account
3. **Authenticated CLI**: Run `op signin` to authenticate

## 🚀 Quick Setup

### Option 1: Interactive Setup (Recommended)

```bash
# Run the interactive setup
python -m src.github_talent_intelligence.cli setup-1password
```

This will:
- Check if 1Password CLI is available
- Detect existing GitHub tokens and OpenAI API keys
- Offer to store them securely in 1Password
- Test the integration

### Option 2: Manual Setup

1. **Create a GitHub Personal Access Token**:
   - Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
   - Create a new token with `repo` and `user` scopes
   - Copy the token

2. **Create an OpenAI API Key**:
   - Go to [OpenAI Platform > API Keys](https://platform.openai.com/api-keys)
   - Create a new API key
   - Copy the key

3. **Store in 1Password**:
   ```bash
   # Create the GitHub token item in 1Password
   op item create \
     --category password \
     --title "GitHub Token" \
     --vault Private \
     token=your_github_token_here \
     notes="GitHub Personal Access Token for Robot Recruiter"

   # Create the OpenAI API key item in 1Password
   op item create \
     --category password \
     --title "OpenAI API Key" \
     --vault Private \
     token=your_openai_api_key_here \
     notes="OpenAI API Key for Robot Recruiter"
   ```

4. **Test the integration**:
   ```bash
   # Test that the keys can be retrieved
   python -c "
   from src.github_talent_intelligence.token_manager import get_github_token, get_openai_api_key
   github_token = get_github_token()
   openai_key = get_openai_api_key()
   print('✅ Both keys retrieved successfully')
   "
   ```

## 🔧 Configuration Options

### Custom Item Names

If you want to use different names for your 1Password items:

```python
from src.github_talent_intelligence.token_manager import SecureTokenManager

# Use custom item names
manager = SecureTokenManager()
github_token = manager.get_github_token("Robot Recruiter GitHub Token")
openai_key = manager.get_openai_api_key("Robot Recruiter OpenAI Key")
```

### Custom Vaults

If you want to store the keys in a specific vault:

```python
# Use custom vault
manager = SecureTokenManager(vault="Work Vault")
github_token = manager.get_github_token()
openai_key = manager.get_openai_api_key()
```

### Environment Variable Override

For CI/CD or development, you can still use environment variables (they take precedence):

```bash
export GITHUB_TOKEN=your_token_here
export OPENAI_API_KEY=your_key_here
```

## 🔄 Key Priority Order

The application checks for keys in this order:

1. **Environment Variable** (`GITHUB_TOKEN`, `OPENAI_API_KEY`) - Highest priority
2. **1Password CLI** (`op item get`) - Recommended for production
3. **GitHub CLI** (`gh auth token`) - Fallback option for GitHub tokens only
4. **File Storage** (`.env`, `.github_token`) - Not recommended

## 🛠️ Usage Examples

### Basic Usage

```python
from src.github_talent_intelligence import TalentAnalyzer

# Keys will be automatically retrieved from 1Password
analyzer = TalentAnalyzer()
repositories = analyzer.analyze_organization("ChainSafe")
```

### Programmatic Key Retrieval

```python
from src.github_talent_intelligence.token_manager import get_github_token, get_openai_api_key

# Get keys directly
github_token = get_github_token()
openai_key = get_openai_api_key()
print(f"GitHub Token: {github_token[:10]}...")
print(f"OpenAI Key: {openai_key[:10]}...")
```

### Custom Configuration

```python
from src.github_talent_intelligence.token_manager import SecureTokenManager

# Custom configuration
manager = SecureTokenManager(
    vault="Company Vault"
)
github_token = manager.get_github_token("Work GitHub Token")
openai_key = manager.get_openai_api_key("Work OpenAI Key")
```

### Generic Secret Management

```python
from src.github_talent_intelligence.token_manager import SecureTokenManager

# For any custom secret
manager = SecureTokenManager()
custom_secret = manager.get_secret("CUSTOM_SECRET", "Custom Secret Item")
```

## 🔍 Troubleshooting

### 1Password CLI Not Found

```bash
# Install 1Password CLI
brew install 1password-cli  # macOS
# or
# Follow installation guide for your platform
```

### Authentication Issues

```bash
# Sign in to 1Password
op signin

# Check authentication
op whoami
```

### Item Not Found

```bash
# List items in your vault
op item list --vault Private

# Check if the items exist
op item get "GitHub Token" --vault Private
op item get "OpenAI API Key" --vault Private
```

### Permission Issues

```bash
# Check vault permissions
op vault list

# Ensure you have access to the vault
op vault get "Private"
```

## 🔒 Security Best Practices

1. **Use Strong Keys**: Create keys with minimal required permissions
2. **Regular Rotation**: Rotate keys periodically
3. **Vault Access**: Limit vault access to authorized users only
4. **Audit Logs**: Monitor key access through 1Password audit logs
5. **Environment Separation**: Use different keys for different environments
6. **Key Naming**: Use descriptive names for your 1Password items

## 🚨 Error Messages

### Common Error Messages and Solutions

| Error | Solution |
|-------|----------|
| `1Password CLI not available` | Install and authenticate with 1Password CLI |
| `Item not found` | Create the item in 1Password or check the item name |
| `Authentication failed` | Run `op signin` to authenticate |
| `Vault access denied` | Check vault permissions and access |
| `OPENAI_API_KEY not found` | Store OpenAI API key in 1Password or set environment variable |

## 📚 Integration with Existing Workflows

### CI/CD Integration

For CI/CD environments, continue using environment variables:

```yaml
# GitHub Actions example
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Development Environment

For local development, use 1Password integration:

```bash
# Set up once
python -m src.github_talent_intelligence.cli setup-1password

# Use normally
python -m src.github_talent_intelligence.cli analyze --org ChainSafe
```

### Team Environments

For team environments, share the 1Password items:

```bash
# Share the items with team members
op item share "GitHub Token" --vault "Team Vault" --email teammate@company.com
op item share "OpenAI API Key" --vault "Team Vault" --email teammate@company.com
```

## 🎯 Migration from File-Based Storage

If you're currently using `.env` or `.github_token` files:

1. **Backup your keys** (if needed):
   ```bash
   cat .env
   cat .github_token
   ```

2. **Set up 1Password integration**:
   ```bash
   python -m src.github_talent_intelligence.cli setup-1password
   ```

3. **Remove the files**:
   ```bash
   rm .env .github_token
   ```

4. **Test the integration**:
   ```bash
   python -m src.github_talent_intelligence.cli analyze --org ChainSafe
   ```

## 🔒 Security Cleanup

### Remove Plain Text Secrets

After setting up 1Password integration, **immediately remove any plain text secrets**:

```bash
# Remove .env file containing API keys
rm .env

# Remove .github_token file if it exists
rm -f .github_token

# Verify keys are still accessible from 1Password
python -c "
from src.github_talent_intelligence.token_manager import get_github_token, get_openai_api_key
print('✅ GitHub Token:', get_github_token()[:10] + '...')
print('✅ OpenAI Key:', get_openai_api_key()[:10] + '...')
"
```

### Environment Template

Use the provided template for non-sensitive configuration:

```bash
# Copy the template
cp env.template .env

# Edit for your environment (no sensitive data)
nano .env
```

Example `.env` file (no secrets):
```bash
# Robot Recruiter Configuration
# Note: API keys are now securely stored in 1Password

# Database configuration
ROBOT_RECRUITER_DB_URL=sqlite:///robot_recruiter.db

# Optional: Override 1Password settings (for CI/CD only)
# GITHUB_TOKEN=your_token_here  # Only for CI/CD
# OPENAI_API_KEY=your_key_here  # Only for CI/CD
```

### Git Security

Ensure sensitive files are ignored:

```bash
# Check .gitignore includes
cat .gitignore | grep -E "\.(env|github_token)"

# Should show:
# .env
# .env.local
# .github_token
```

## 🔄 Key Management

### Adding New Keys

To add new API keys to 1Password:

```bash
# Store a new key
op item create \
  --category password \
  --title "New API Key" \
  --vault Private \
  token=your_new_key_here \
  notes="Description of the key"
```

### Rotating Keys

1. **Create new keys** in GitHub/OpenAI
2. **Update 1Password items**:
   ```bash
   op item edit "GitHub Token" --vault Private
   # Update the token field with the new key
   ```
3. **Test the new keys** with the application

### Listing Stored Keys

```bash
# List all items in your vault
op item list --vault Private

# Get details of a specific item
op item get "GitHub Token" --vault Private
```

## 📞 Support

If you encounter issues with 1Password integration:

1. Check the [1Password CLI documentation](https://developer.1password.com/docs/cli/)
2. Verify your 1Password account and vault permissions
3. Test with a simple 1Password CLI command: `op item list`
4. Check the application logs for detailed error messages

---

**Note**: 1Password integration is optional. The application will fall back to other key sources if 1Password is not available. 