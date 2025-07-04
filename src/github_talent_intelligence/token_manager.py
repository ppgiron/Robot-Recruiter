"""
Secure Token Manager for Robot Recruiter
Integrates with 1Password CLI for secure API key storage and retrieval.
"""

import os
import subprocess
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SecureTokenManager:
    """
    Secure token manager that integrates with 1Password CLI.
    
    Supports multiple API keys and secrets with priority order:
    1. Environment variable
    2. 1Password CLI (op)
    3. GitHub CLI (gh auth token) - for GitHub tokens only
    4. File-based storage (fallback, not recommended)
    """
    
    def __init__(self, vault: Optional[str] = None):
        """
        Initialize the secure token manager.
        
        Args:
            vault: 1Password vault name (optional, uses default if not specified)
        """
        self.vault = vault
        self._token_cache: Dict[str, str] = {}
    
    def get_github_token(self, item_name: str = "GitHub Token") -> str:
        """
        Get GitHub token from the most secure available source.
        
        Args:
            item_name: Name of the 1Password item containing the GitHub token
            
        Returns:
            GitHub token string
            
        Raises:
            ValueError: If no token can be found from any source
        """
        return self._get_secret("GITHUB_TOKEN", item_name, allow_github_cli=True)
    
    def get_openai_api_key(self, item_name: str = "OpenAI API Key") -> str:
        """
        Get OpenAI API key from the most secure available source.
        
        Args:
            item_name: Name of the 1Password item containing the OpenAI API key
            
        Returns:
            OpenAI API key string
            
        Raises:
            ValueError: If no API key can be found from any source
        """
        return self._get_secret("OPENAI_API_KEY", item_name, allow_github_cli=False)
    
    def get_secret(self, env_var_name: str, item_name: str, allow_github_cli: bool = False) -> str:
        """
        Generic method to get any secret from the most secure available source.
        
        Args:
            env_var_name: Environment variable name (e.g., "GITHUB_TOKEN")
            item_name: Name of the 1Password item
            allow_github_cli: Whether to try GitHub CLI (only for GitHub tokens)
            
        Returns:
            Secret string
            
        Raises:
            ValueError: If no secret can be found from any source
        """
        return self._get_secret(env_var_name, item_name, allow_github_cli)
    
    def _get_secret(self, env_var_name: str, item_name: str, allow_github_cli: bool = False) -> str:
        """
        Internal method to get secrets with caching.
        
        Args:
            env_var_name: Environment variable name
            item_name: 1Password item name
            allow_github_cli: Whether to try GitHub CLI
            
        Returns:
            Secret string
        """
        # Check cache first
        cache_key = f"{env_var_name}:{item_name}"
        if cache_key in self._token_cache:
            return self._token_cache[cache_key]
        
        # Try environment variable first (for CI/CD and development)
        secret = os.getenv(env_var_name)
        if secret:
            logger.debug(f"Using {env_var_name} from environment variable")
            self._token_cache[cache_key] = secret
            return secret
        
        # Try 1Password CLI
        secret = self._get_secret_from_1password(item_name)
        if secret:
            logger.debug(f"Using {env_var_name} from 1Password")
            self._token_cache[cache_key] = secret
            return secret
        
        # Try GitHub CLI as fallback (only for GitHub tokens)
        if allow_github_cli and env_var_name == "GITHUB_TOKEN":
            secret = self._get_token_from_github_cli()
            if secret:
                logger.debug("Using GitHub token from GitHub CLI")
                self._token_cache[cache_key] = secret
                return secret
        
        # Last resort: try file-based storage (not recommended)
        secret = self._get_secret_from_file(env_var_name)
        if secret:
            logger.warning(f"Using {env_var_name} from file (not recommended for production)")
            self._token_cache[cache_key] = secret
            return secret
        
        raise ValueError(
            f"{env_var_name} not found. Please set {env_var_name} environment variable, "
            f"store it in 1Password as '{item_name}', or use GitHub CLI (gh auth login) for GitHub tokens."
        )
    
    def _get_secret_from_1password(self, item_name: str) -> Optional[str]:
        """
        Retrieve secret from 1Password CLI.
        
        Args:
            item_name: Name of the 1Password item
            
        Returns:
            Secret if found, None otherwise
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
            
            # Build the command to get the item with --reveal flag
            cmd = ["op", "item", "get", item_name, "--fields", "label=token", "--reveal"]
            if self.vault:
                cmd.extend(["--vault", self.vault])
            
            # Get the secret
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                secret = result.stdout.strip()
                if secret:
                    return secret
                else:
                    logger.debug(f"1Password item '{item_name}' found but token field is empty")
                    return None
            else:
                logger.debug(f"1Password CLI error for '{item_name}': {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.debug("1Password CLI command timed out")
            return None
        except FileNotFoundError:
            logger.debug("1Password CLI (op) not found")
            return None
        except Exception as e:
            logger.debug(f"Error retrieving secret '{item_name}' from 1Password: {e}")
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
    
    def _get_secret_from_file(self, env_var_name: str) -> Optional[str]:
        """
        Retrieve secret from file (fallback method).
        
        Args:
            env_var_name: Environment variable name
            
        Returns:
            Secret if found, None otherwise
        """
        # Try .env file
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{env_var_name}="):
                            secret = line.split("=", 1)[1].strip()
                            if secret:
                                return secret
            except Exception as e:
                logger.debug(f"Error reading .env file: {e}")
        
        # Try specific token file for GitHub tokens
        if env_var_name == "GITHUB_TOKEN":
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
    
    def store_secret_in_1password(self, secret: str, item_name: str, description: str = "") -> bool:
        """
        Store secret in 1Password.
        
        Args:
            secret: Secret to store
            item_name: Name for the 1Password item
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
                "--title", item_name,
                "--vault", self.vault or "Private",
                f"token={secret}",
                f"notes={description}"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"Secret stored in 1Password as '{item_name}'")
                return True
            else:
                logger.error(f"Failed to store secret in 1Password: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("1Password CLI command timed out")
            return False
        except FileNotFoundError:
            logger.error("1Password CLI (op) not found")
            return False
        except Exception as e:
            logger.error(f"Error storing secret in 1Password: {e}")
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
        
        # Check for existing secrets
        secrets_found = []
        
        # Check GitHub token
        try:
            github_token = self.get_github_token()
            secrets_found.append(("GitHub Token", github_token))
        except ValueError:
            pass
        
        # Check OpenAI API key
        try:
            openai_key = self.get_openai_api_key()
            secrets_found.append(("OpenAI API Key", openai_key))
        except ValueError:
            pass
        
        if secrets_found:
            print(f"✅ Found {len(secrets_found)} existing secrets")
            
            for secret_name, secret_value in secrets_found:
                print(f"  - {secret_name}: {secret_value[:10]}...")
            
            # Ask if user wants to store them in 1Password
            response = input("\nWould you like to store these secrets in 1Password? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                success_count = 0
                for secret_name, secret_value in secrets_found:
                    if self.store_secret_in_1password(secret_value, secret_name):
                        success_count += 1
                        print(f"✅ {secret_name} stored in 1Password")
                    else:
                        print(f"❌ Failed to store {secret_name}")
                
                if success_count == len(secrets_found):
                    print("\n✅ All secrets stored in 1Password successfully!")
                    return True
                else:
                    print(f"\n⚠️  {success_count}/{len(secrets_found)} secrets stored successfully")
                    return False
            else:
                print("Secrets will continue to be retrieved from current sources")
                return True
        else:
            print("❌ No secrets found")
            print("Please set up your secrets first:")
            print("  1. Create a GitHub Personal Access Token at https://github.com/settings/tokens")
            print("  2. Create an OpenAI API key at https://platform.openai.com/api-keys")
            print("  3. Set them as environment variables:")
            print("     export GITHUB_TOKEN=your_token_here")
            print("     export OPENAI_API_KEY=your_key_here")
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
    manager = SecureTokenManager(vault)
    return manager.get_github_token(item_name)


def get_openai_api_key(item_name: str = "OpenAI API Key", vault: Optional[str] = None) -> str:
    """
    Convenience function to get OpenAI API key with 1Password integration.
    
    Args:
        item_name: Name of the 1Password item containing the OpenAI API key
        vault: 1Password vault name (optional)
        
    Returns:
        OpenAI API key string
        
    Raises:
        ValueError: If no API key can be found
    """
    manager = SecureTokenManager(vault)
    return manager.get_openai_api_key(item_name) 