"""
OpenSky Network API Configuration Management

This module provides secure credential handling and environment-based configuration
for the OpenSky Network API integration.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class Environment(str, Enum):
    """Environment types for configuration"""
    DEVELOPMENT = "dev"
    PRODUCTION = "prod"
    TESTING = "test"


@dataclass
class OpenSkyCredentials:
    """OpenSky API credentials"""
    username: str
    password: str
    
    def __post_init__(self):
        if not self.username or not self.password:
            raise ValueError("Both username and password are required")


@dataclass
class OpenSkyAPIConfig:
    """OpenSky API configuration settings"""
    base_url: str = "https://opensky-network.org/api"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_authenticated: float = 0.1  # seconds between requests
    rate_limit_unauthenticated: float = 10.0  # seconds between requests
    cache_ttl: int = 300  # 5 minutes
    max_cache_size: int = 128


class OpenSkyConfig:
    """
    OpenSky Network API Configuration Manager
    
    Handles loading credentials from credentials.json and provides
    environment-based configuration with secure credential management.
    """
    
    def __init__(self, 
                 credentials_path: Optional[str] = None,
                 environment: Environment = Environment.DEVELOPMENT):
        """
        Initialize OpenSky configuration
        
        Args:
            credentials_path: Path to credentials.json file
            environment: Environment type (dev/prod/test)
        """
        self.environment = environment
        self.logger = self._setup_logging()
        
        # Set default credentials path
        if credentials_path is None:
            project_root = Path(__file__).parent.parent
            credentials_path = project_root / "credentials.json"
        
        self.credentials_path = Path(credentials_path)
        
        # Load configuration
        self._credentials: Optional[OpenSkyCredentials] = None
        self._api_config = OpenSkyAPIConfig()
        
        self._load_credentials()
        self._apply_environment_config()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(f"opensky_config.{self.environment}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _load_credentials(self) -> None:
        """
        Load credentials from credentials.json file
        
        Raises:
            FileNotFoundError: If credentials file doesn't exist
            ValueError: If credentials are invalid or missing
            json.JSONDecodeError: If credentials file is malformed
        """
        """
        Load credentials with the following precedence:
        1. Environment variables OPENSKY_USERNAME / OPENSKY_PASSWORD
        2. credentials.json file (existing behavior)

        This keeps backward compatibility while encouraging env-based secrets.
        """
        try:
            # 1) Try environment variables first (preferred)
            env_user = os.environ.get('OPENSKY_USERNAME') or os.environ.get('OPENSKY_USER')
            env_pass = os.environ.get('OPENSKY_PASSWORD') or os.environ.get('OPENSKY_PASS')

            if env_user and env_pass:
                env_user = env_user.strip()
                env_pass = env_pass.strip()
                self._credentials = OpenSkyCredentials(username=env_user, password=env_pass)
                self.logger.info("Loaded OpenSky credentials from environment variables")
                return

            # 2) Fallback to credentials.json (preserves current behavior)
            if self.credentials_path and self.credentials_path.exists():
                self.logger.info(f"Loading credentials from {self.credentials_path}")
                with open(self.credentials_path, 'r', encoding='utf-8') as f:
                    credentials_data = json.load(f)

                # Extract OpenSky credentials
                opensky_creds = credentials_data.get('opensky', {})

                if not opensky_creds:
                    self.logger.warning("No OpenSky credentials found in credentials.json")
                    return

                username = opensky_creds.get('username', '').strip()
                password = opensky_creds.get('password', '').strip()

                if username and password:
                    self._credentials = OpenSkyCredentials(username=username, password=password)
                    self.logger.info(f"Successfully loaded credentials for user: {username}")
                else:
                    self.logger.warning("OpenSky username or password is empty in credentials.json")
            else:
                self.logger.info("No environment credentials and credentials.json not found; running unauthenticated")

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in credentials file: {e}")
            raise
        except Exception as e:
            # Do not expose secrets in exception messages
            self.logger.error(f"Error loading credentials: {type(e).__name__}: {e}")
            raise ValueError("Failed to load OpenSky credentials")
    
    def _apply_environment_config(self) -> None:
        """Apply environment-specific configuration"""
        if self.environment == Environment.DEVELOPMENT:
            self._api_config.timeout = 60
            self._api_config.max_retries = 5
            self._api_config.cache_ttl = 60  # Shorter cache for development
        
        elif self.environment == Environment.PRODUCTION:
            self._api_config.timeout = 30
            self._api_config.max_retries = 3
            self._api_config.cache_ttl = 300  # Longer cache for production
            
        elif self.environment == Environment.TESTING:
            self._api_config.timeout = 10
            self._api_config.max_retries = 1
            self._api_config.cache_ttl = 10  # Very short cache for testing
        
        self.logger.info(f"Applied {self.environment} environment configuration")
    
    @property
    def credentials(self) -> Optional[OpenSkyCredentials]:
        """Get OpenSky credentials"""
        return self._credentials
    
    @property
    def api_config(self) -> OpenSkyAPIConfig:
        """Get API configuration"""
        return self._api_config
    
    @property
    def is_authenticated(self) -> bool:
        """Check if valid credentials are available"""
        return self._credentials is not None
    
    def get_auth_tuple(self) -> Optional[tuple[str, str]]:
        """
        Get authentication tuple for requests
        
        Returns:
            Tuple of (username, password) or None if not authenticated
        """
        if self._credentials:
            return (self._credentials.username, self._credentials.password)
        return None
    
    def get_rate_limit(self) -> float:
        """
        Get appropriate rate limit based on authentication status
        
        Returns:
            Rate limit in seconds between requests
        """
        if self.is_authenticated:
            return self._api_config.rate_limit_authenticated
        else:
            return self._api_config.rate_limit_unauthenticated
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate current configuration
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'credentials_file_exists': self.credentials_path.exists(),
            'has_credentials': self.is_authenticated,
            'environment': self.environment,
            'rate_limit': self.get_rate_limit(),
            'api_timeout': self._api_config.timeout,
        }
        
        if self.is_authenticated:
            validation['username'] = self._credentials.username
            validation['auth_status'] = 'authenticated'
        else:
            validation['auth_status'] = 'unauthenticated'
        
        return validation
    
    def reload_credentials(self) -> None:
        """Reload credentials from file"""
        self.logger.info("Reloading credentials...")
        self._credentials = None
        self._load_credentials()
    
    def __repr__(self) -> str:
        """String representation of config"""
        auth_status = "authenticated" if self.is_authenticated else "unauthenticated"
        return f"OpenSkyConfig(env={self.environment}, auth={auth_status})"


# Global configuration instance
_config_instance: Optional[OpenSkyConfig] = None


def get_config(credentials_path: Optional[str] = None,
               environment: Optional[Environment] = None,
               reload: bool = False) -> OpenSkyConfig:
    """
    Get global OpenSky configuration instance
    
    Args:
        credentials_path: Path to credentials file
        environment: Environment type
        reload: Force reload of configuration
        
    Returns:
        OpenSkyConfig instance
    """
    global _config_instance
    
    if _config_instance is None or reload:
        env = environment or Environment.DEVELOPMENT
        _config_instance = OpenSkyConfig(
            credentials_path=credentials_path,
            environment=env
        )
    
    return _config_instance


def reset_config() -> None:
    """Reset global configuration instance"""
    global _config_instance
    _config_instance = None


if __name__ == "__main__":
    # Example usage and testing
    config = get_config()
    print(f"Configuration: {config}")
    print(f"Validation: {config.validate_config()}")