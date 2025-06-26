"""
Secure Token Manager for Robot Recruiter
Integrates with 1Password CLI for secure GitHub token storage and retrieval.
"""

import os
import subprocess
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SecureTokenManager:
    """
    Secure token manager that integrates with 1Password CLI.
    
    Supports multiple token sources in order of preference:
    1. Environment variable (GITHUB_TOKEN)
    2. 1Password CLI (op)
    3. GitHub CLI (gh auth token)
    4. File-based storage (fallback, not recommended)
    """
    
    def __init__(self, item_name: str = "GitHub Token", vault: Optional[str] = None):
        """
        Initialize the secure token manager.
        
        Args:
            item_name: Name of the 1Password item containing the GitHub token
            vault: 1Password vault name (optional, uses default if not specified)
        """
        self.item_name = item_name
        self.vault = vault
        self._token_cache = None
    
    def get_github_token(self) -> str:
        """
        Get GitHub token from the most secure available source.
        
        Returns:
            GitHub token string
            
        Raises:
            ValueError: If no token can be found from any source
        """
        # Try environment variable first (for CI/CD and development)
        token = os.getenv("GITHUB_TOKEN")
        if token:
            logger.debug("Using GitHub token from environment variable")
            return token
        
        # Try 1Password CLI
        token = self._get_token_from_1password()
        if token:
            logger.debug("Using GitHub token from 1Password")
            return token
        
        # Try GitHub CLI as fallback
        token = self._get_token_from_github_cli()
        if token:
            logger.debug("Using GitHub token from GitHub CLI")
            return token
        
        # Last resort: try file-based storage (not recommended)
        token = self._get_token_from_file()
        if token:
            logger.warning("Using GitHub token from file (not recommended for production)")
            return token
        
        raise ValueError(
            "GitHub token not found. Please set GITHUB_TOKEN environment variable, "
            "store it in 1Password, or use GitHub CLI (gh auth login)."
        )
    
    def _get_token_from_1password(self) -> Optional[str]:
        """
        Retrieve GitHub token from 1Password CLI.
        
        Returns:
            GitHub token if found, None otherwise
        """
        try:
            # Check if 1Password CLI is available
            result = subprocess.run(
                ["op", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode != 0:
                logger.debug("1Password CLI not available or not authenticated")
                return None
            
            # Build the command to get the item
            cmd = ["op", "item", "get", self.item_name, "--fields", "label=token"]
            if self.vault:
                cmd.extend(["--vault", self.vault])
            
            # Get the token
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                token = result.stdout.strip()
                if token:
                    return token
                else:
                    logger.debug("1Password item found but token field is empty")
                    return None
            else:
                logger.debug(f"1Password CLI error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.debug("1Password CLI command timed out")
            return None
        except FileNotFoundError:
            logger.debug("1Password CLI (op) not found")
            return None
        except Exception as e:
            logger.debug(f"Error retrieving token from 1Password: {e}")
            return None
    
    def _get_token_from_github_cli(self) -> Optional[str]:
        """
        Retrieve GitHub token from GitHub CLI.
        
        Returns:
            GitHub token if found, None otherwise
        """
        try:
            result = subprocess.run(
                ["gh", "auth", "token"], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                token = result.stdout.strip()
                if token:
                    return token
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.debug("GitHub CLI not available or timed out")
        except Exception as e:
            logger.debug(f"Error retrieving token from GitHub CLI: {e}")
        
        return None
    
    def _get_token_from_file(self) -> Optional[str]:
        """
        Retrieve GitHub token from file (fallback method).
        
        Returns:
            GitHub token if found, None otherwise
        """
        # Try .github_token file
        token_file = Path(".github_token")
        if token_file.exists():
            try:
                with open(token_file, "r") as f:
                    token = f.read().strip()
                    if token:
                        return token
            except Exception as e:
                logger.debug(f"Error reading token file: {e}")
        
        return None
    
    def store_token_in_1password(self, token: str, description: str = "GitHub Personal Access Token") -> bool:
        """
        Store GitHub token in 1Password.
        
        Args:
            token: GitHub token to store
            description: Description for the 1Password item
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if 1Password CLI is available
            result = subprocess.run(
                ["op", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode != 0:
                logger.error("1Password CLI not available or not authenticated")
                return False
            
            # Create the item in 1Password
            cmd = [
                "op", "item", "create",
                "--category", "password",
                "--title", self.item_name,
                "--vault", self.vault or "Private",
                f"token={token}",
                f"notes={description}"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"GitHub token stored in 1Password as '{self.item_name}'")
                return True
            else:
                logger.error(f"Failed to store token in 1Password: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("1Password CLI command timed out")
            return False
        except FileNotFoundError:
            logger.error("1Password CLI (op) not found")
            return False
        except Exception as e:
            logger.error(f"Error storing token in 1Password: {e}")
            return False
    
    def setup_1password_integration(self) -> bool:
        """
        Interactive setup for 1Password integration.
        
        Returns:
            True if setup was successful, False otherwise
        """
        print("🔐 1Password Integration Setup")
        print("=" * 40)
        
        # Check if 1Password CLI is available
        try:
            result = subprocess.run(
                ["op", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode != 0:
                print("❌ 1Password CLI not available or not authenticated")
                print("Please install and authenticate with 1Password CLI first:")
                print("  https://developer.1password.com/docs/cli/get-started/")
                return False
        except FileNotFoundError:
            print("❌ 1Password CLI (op) not found")
            print("Please install 1Password CLI first:")
            print("  https://developer.1password.com/docs/cli/get-started/")
            return False
        
        print("✅ 1Password CLI is available")
        
        # Get current token
        current_token = self.get_github_token()
        if current_token:
            print(f"✅ Found existing GitHub token")
            
            # Ask if user wants to store it in 1Password
            response = input("Would you like to store this token in 1Password? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                if self.store_token_in_1password(current_token):
                    print("✅ Token stored in 1Password successfully!")
                    return True
                else:
                    print("❌ Failed to store token in 1Password")
                    return False
            else:
                print("Token will continue to be retrieved from current source")
                return True
        else:
            print("❌ No GitHub token found")
            print("Please set up a GitHub token first:")
            print("  1. Create a Personal Access Token at https://github.com/settings/tokens")
            print("  2. Set it as GITHUB_TOKEN environment variable")
            print("  3. Or use GitHub CLI: gh auth login")
            return False


def get_github_token(item_name: str = "GitHub Token", vault: Optional[str] = None) -> str:
    """
    Convenience function to get GitHub token with 1Password integration.
    
    Args:
        item_name: Name of the 1Password item containing the GitHub token
        vault: 1Password vault name (optional)
        
    Returns:
        GitHub token string
        
    Raises:
        ValueError: If no token can be found
    """
    manager = SecureTokenManager(item_name, vault)
    return manager.get_github_token() 