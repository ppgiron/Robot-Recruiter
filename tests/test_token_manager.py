"""Test file for SecureTokenManager with 1Password integration."""

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from src.github_talent_intelligence.token_manager import SecureTokenManager


@pytest.fixture
def token_manager():
    """Create a SecureTokenManager instance for testing."""
    return SecureTokenManager()


def test_get_github_token_from_env():
    """Test getting GitHub token from environment variable."""
    with patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token_123'}):
        manager = SecureTokenManager()
        token = manager.get_github_token()
        assert token == 'test_token_123'


def test_get_openai_api_key_from_env():
    """Test getting OpenAI API key from environment variable."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_openai_key_456'}):
        manager = SecureTokenManager()
        api_key = manager.get_openai_api_key()
        assert api_key == 'test_openai_key_456'


def test_get_github_token_from_1password():
    """Test getting GitHub token from 1Password CLI."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('subprocess.run') as mock_run:
            # Mock 1Password CLI version check
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "1.15.0"
            
            # Mock 1Password item get
            mock_run.return_value.stdout = "test_token_456"
            
            manager = SecureTokenManager()
            token = manager.get_github_token()
            assert token == 'test_token_456'


def test_get_openai_api_key_from_1password():
    """Test getting OpenAI API key from 1Password CLI."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('subprocess.run') as mock_run:
            # Mock 1Password CLI version check
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "1.15.0"
            
            # Mock 1Password item get
            mock_run.return_value.stdout = "test_openai_key_789"
            
            manager = SecureTokenManager()
            api_key = manager.get_openai_api_key()
            assert api_key == 'test_openai_key_789'


def test_get_github_token_from_github_cli():
    """Test getting GitHub token from GitHub CLI."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('subprocess.run') as mock_run:
            # Mock 1Password CLI not available
            mock_run.side_effect = [
                MagicMock(returncode=1),  # 1Password not available
                MagicMock(returncode=0, stdout="test_token_789")  # GitHub CLI
            ]
            
            manager = SecureTokenManager()
            token = manager.get_github_token()
            assert token == 'test_token_789'


def test_get_openai_api_key_no_github_cli_fallback():
    """Test that OpenAI API key doesn't fall back to GitHub CLI."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('subprocess.run') as mock_run:
            # Mock 1Password CLI not available
            mock_run.return_value.returncode = 1
            
            # Mock no .env file exists
            with patch('pathlib.Path.exists', return_value=False):
                manager = SecureTokenManager()
                with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
                    manager.get_openai_api_key()


def test_get_github_token_no_sources():
    """Test error when no token sources are available."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('subprocess.run') as mock_run:
            # Mock all CLI tools as unavailable
            mock_run.return_value.returncode = 1
            
            # Mock no .env file exists
            with patch('pathlib.Path.exists', return_value=False):
                manager = SecureTokenManager()
                with pytest.raises(ValueError, match="GITHUB_TOKEN not found"):
                    manager.get_github_token()


def test_get_openai_api_key_no_sources():
    """Test error when no OpenAI API key sources are available."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('subprocess.run') as mock_run:
            # Mock all CLI tools as unavailable
            mock_run.return_value.returncode = 1
            
            # Mock no .env file exists
            with patch('pathlib.Path.exists', return_value=False):
                manager = SecureTokenManager()
                with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
                    manager.get_openai_api_key()


def test_store_secret_in_1password():
    """Test storing secret in 1Password."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "1.15.0"
        
        manager = SecureTokenManager()
        success = manager.store_secret_in_1password("test_secret_123", "Test Secret")
        assert success is True


def test_store_secret_in_1password_failure():
    """Test storing secret in 1Password when it fails."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Authentication failed"
        
        manager = SecureTokenManager()
        success = manager.store_secret_in_1password("test_secret_123", "Test Secret")
        assert success is False


def test_1password_cli_not_found():
    """Test behavior when 1Password CLI is not installed."""
    with patch('subprocess.run', side_effect=FileNotFoundError):
        manager = SecureTokenManager()
        secret = manager._get_secret_from_1password("Test Secret")
        assert secret is None


def test_convenience_function_github():
    """Test the convenience function get_github_token."""
    with patch.dict(os.environ, {'GITHUB_TOKEN': 'convenience_token'}):
        from src.github_talent_intelligence.token_manager import get_github_token
        token = get_github_token()
        assert token == 'convenience_token'


def test_convenience_function_openai():
    """Test the convenience function get_openai_api_key."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'convenience_openai_key'}):
        from src.github_talent_intelligence.token_manager import get_openai_api_key
        api_key = get_openai_api_key()
        assert api_key == 'convenience_openai_key'


def test_custom_vault():
    """Test using custom 1Password vault."""
    manager = SecureTokenManager(vault="Work Vault")
    assert manager.vault == "Work Vault"


def test_custom_item_names():
    """Test using custom item names for different secrets."""
    manager = SecureTokenManager()
    
    # Test custom GitHub token item name
    with patch.dict(os.environ, {'GITHUB_TOKEN': 'custom_github_token'}):
        token = manager.get_github_token("Custom GitHub Token")
        assert token == 'custom_github_token'
    
    # Test custom OpenAI API key item name
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'custom_openai_key'}):
        api_key = manager.get_openai_api_key("Custom OpenAI Key")
        assert api_key == 'custom_openai_key'


def test_secret_caching():
    """Test that secrets are cached after first retrieval."""
    with patch.dict(os.environ, {'GITHUB_TOKEN': 'cached_token'}):
        manager = SecureTokenManager()
        
        # First call should cache the token
        token1 = manager.get_github_token()
        assert token1 == 'cached_token'
        
        # Second call should use cache
        token2 = manager.get_github_token()
        assert token2 == 'cached_token'
        
        # Cache should be populated
        assert len(manager._token_cache) > 0


def test_generic_get_secret():
    """Test the generic get_secret method."""
    with patch.dict(os.environ, {'CUSTOM_SECRET': 'custom_secret_value'}):
        manager = SecureTokenManager()
        secret = manager.get_secret("CUSTOM_SECRET", "Custom Secret Item")
        assert secret == 'custom_secret_value'


def test_get_secret_from_env_file():
    """Test getting secret from .env file."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="OPENAI_API_KEY=env_file_key\n")):
                manager = SecureTokenManager()
                api_key = manager.get_openai_api_key()
                assert api_key == 'env_file_key' 