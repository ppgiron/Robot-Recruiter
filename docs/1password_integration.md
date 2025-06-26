# 1Password Integration for Robot Recruiter

Robot Recruiter now supports secure GitHub token storage using 1Password CLI, providing enterprise-grade security for your GitHub Personal Access Tokens.

## 🔐 Why Use 1Password Integration?

- **Secure Storage**: Tokens are encrypted and stored in 1Password vaults
- **No Plain Text Files**: Eliminates the security risk of storing tokens in files
- **Access Control**: Leverage 1Password's team sharing and access controls
- **Audit Trail**: Track who accessed tokens and when
- **Automatic Rotation**: Easy token rotation and management

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
- Detect existing GitHub tokens
- Offer to store them securely in 1Password
- Test the integration

### Option 2: Manual Setup

1. **Create a GitHub Personal Access Token**:
   - Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
   - Create a new token with `repo` and `user` scopes
   - Copy the token

2. **Store in 1Password**:
   ```bash
   # Create the item in 1Password
   op item create \
     --category password \
     --title "GitHub Token" \
     --vault Private \
     token=your_github_token_here \
     notes="GitHub Personal Access Token for Robot Recruiter"
   ```

3. **Test the integration**:
   ```bash
   # Test that the token can be retrieved
   python -c "
   from src.github_talent_intelligence.token_manager import get_github_token
   token = get_github_token()
   print('✅ Token retrieved successfully')
   "
   ```

## 🔧 Configuration Options

### Custom Item Names

If you want to use a different name for your 1Password item:

```python
from src.github_talent_intelligence.token_manager import SecureTokenManager

# Use custom item name
manager = SecureTokenManager(item_name="Robot Recruiter GitHub Token")
token = manager.get_github_token()
```

### Custom Vaults

If you want to store the token in a specific vault:

```python
# Use custom vault
manager = SecureTokenManager(vault="Work Vault")
token = manager.get_github_token()
```

### Environment Variable Override

For CI/CD or development, you can still use environment variables (they take precedence):

```bash
export GITHUB_TOKEN=your_token_here
```

## 🔄 Token Priority Order

The application checks for tokens in this order:

1. **Environment Variable** (`GITHUB_TOKEN`) - Highest priority
2. **1Password CLI** (`op item get`) - Recommended for production
3. **GitHub CLI** (`gh auth token`) - Fallback option
4. **File Storage** (`.github_token`) - Not recommended

## 🛠️ Usage Examples

### Basic Usage

```python
from src.github_talent_intelligence import TalentAnalyzer

# Token will be automatically retrieved from 1Password
analyzer = TalentAnalyzer()
repositories = analyzer.analyze_organization("ChainSafe")
```

### Programmatic Token Retrieval

```python
from src.github_talent_intelligence.token_manager import get_github_token

# Get token directly
token = get_github_token()
print(f"Token retrieved: {token[:10]}...")
```

### Custom Configuration

```python
from src.github_talent_intelligence.token_manager import SecureTokenManager

# Custom configuration
manager = SecureTokenManager(
    item_name="Work GitHub Token",
    vault="Company Vault"
)
token = manager.get_github_token()
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

# Check if the item exists
op item get "GitHub Token" --vault Private
```

### Permission Issues

```bash
# Check vault permissions
op vault list

# Ensure you have access to the vault
op vault get "Private"
```

## 🔒 Security Best Practices

1. **Use Strong Tokens**: Create tokens with minimal required permissions
2. **Regular Rotation**: Rotate tokens periodically
3. **Vault Access**: Limit vault access to authorized users only
4. **Audit Logs**: Monitor token access through 1Password audit logs
5. **Environment Separation**: Use different tokens for different environments

## 🚨 Error Messages

### Common Error Messages and Solutions

| Error | Solution |
|-------|----------|
| `1Password CLI not available` | Install and authenticate with 1Password CLI |
| `Item not found` | Create the item in 1Password or check the item name |
| `Authentication failed` | Run `op signin` to authenticate |
| `Vault access denied` | Check vault permissions and access |

## 📚 Integration with Existing Workflows

### CI/CD Integration

For CI/CD environments, continue using environment variables:

```yaml
# GitHub Actions example
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
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

For team environments, share the 1Password item:

```bash
# Share the item with team members
op item share "GitHub Token" --vault "Team Vault" --email teammate@company.com
```

## 🎯 Migration from File-Based Storage

If you're currently using `.github_token` files:

1. **Backup your token**:
   ```bash
   cat .github_token
   ```

2. **Set up 1Password integration**:
   ```bash
   python -m src.github_talent_intelligence.cli setup-1password
   ```

3. **Remove the file**:
   ```bash
   rm .github_token
   ```

4. **Test the integration**:
   ```bash
   python -m src.github_talent_intelligence.cli analyze --org ChainSafe
   ```

## 📞 Support

If you encounter issues with 1Password integration:

1. Check the [1Password CLI documentation](https://developer.1password.com/docs/cli/)
2. Verify your 1Password account and vault permissions
3. Test with a simple 1Password CLI command: `op item list`
4. Check the application logs for detailed error messages

---

**Note**: 1Password integration is optional. The application will fall back to other token sources if 1Password is not available. 