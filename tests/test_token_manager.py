"""Test file for SecureTokenManager with 1Password integration."""

import os
import pytest
from unittest.mock import patch, MagicMock
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


def test_get_github_token_no_sources():
    """Test error when no token sources are available."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('subprocess.run') as mock_run:
            # Mock all CLI tools as unavailable
            mock_run.return_value.returncode = 1
            
            manager = SecureTokenManager()
            with pytest.raises(ValueError, match="GitHub token not found"):
                manager.get_github_token()


def test_store_token_in_1password():
    """Test storing token in 1Password."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "1.15.0"
        
        manager = SecureTokenManager()
        success = manager.store_token_in_1password("test_token_123")
        assert success is True


def test_store_token_in_1password_failure():
    """Test storing token in 1Password when it fails."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Authentication failed"
        
        manager = SecureTokenManager()
        success = manager.store_token_in_1password("test_token_123")
        assert success is False


def test_1password_cli_not_found():
    """Test behavior when 1Password CLI is not installed."""
    with patch('subprocess.run', side_effect=FileNotFoundError):
        manager = SecureTokenManager()
        token = manager._get_token_from_1password()
        assert token is None


def test_convenience_function():
    """Test the convenience function get_github_token."""
    with patch.dict(os.environ, {'GITHUB_TOKEN': 'convenience_token'}):
        from src.github_talent_intelligence.token_manager import get_github_token
        token = get_github_token()
        assert token == 'convenience_token'


def test_custom_item_name():
    """Test using custom 1Password item name."""
    manager = SecureTokenManager(item_name="Custom GitHub Token")
    assert manager.item_name == "Custom GitHub Token"


def test_custom_vault():
    """Test using custom 1Password vault."""
    manager = SecureTokenManager(vault="Work Vault")
    assert manager.vault == "Work Vault" 