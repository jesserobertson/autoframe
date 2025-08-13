"""Configuration management for autoframe.

This module provides configuration handling using confection for type-safe,
validated configuration management throughout the autoframe library.
"""

from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import os

from confection import Config
from logerr import Result, Ok, Err

from autoframe.types import ConfigResult, ConfigurationError


class AutoFrameConfig:
    """Configuration manager for autoframe settings.
    
    This class provides a centralized way to manage configuration
    for data sources, dataframe creation, and quality assessment.
    """
    
    DEFAULT_CONFIG = {
        "data_sources": {
            "mongodb": {
                "connection_timeout": 5000,  # milliseconds
                "server_selection_timeout": 3000,  # milliseconds
                "socket_timeout": 10000,  # milliseconds
                "max_pool_size": 10,
                "retry_writes": True
            }
        },
        "dataframes": {
            "default_backend": "pandas",
            "max_memory_usage": "1GB",
            "chunk_size": 10000,
            "infer_schema_sample_size": 1000
        },
        "quality": {
            "enable_by_default": True,
            "quality_threshold": 0.8,
            "max_null_percentage": 0.1,
            "enable_duplicate_detection": True,
            "enable_outlier_detection": False
        },
        "logging": {
            "level": "INFO",
            "enable_performance_logging": False,
            "log_query_details": False
        }
    }
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self._config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self._config_path = Path(config_path) if config_path else None
        
        if self._config_path and self._config_path.exists():
            self._load_config_file()
        
        # Override with environment variables
        self._load_environment_overrides()
    
    def _load_config_file(self) -> None:
        """Load configuration from file."""
        try:
            if self._config_path.suffix.lower() == '.json':
                import json
                with open(self._config_path, 'r') as f:
                    file_config = json.load(f)
            elif self._config_path.suffix.lower() in ['.yml', '.yaml']:
                import yaml
                with open(self._config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
            else:
                # Try to use confection for .cfg files
                file_config = Config().from_disk(self._config_path)
            
            # Merge with defaults
            self._deep_merge(self._config, file_config)
            
        except Exception as e:
            # Don't fail on config load errors, just use defaults
            pass
    
    def _load_environment_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        env_mapping = {
            "AUTOFRAME_MONGODB_TIMEOUT": ("data_sources", "mongodb", "connection_timeout"),
            "AUTOFRAME_DEFAULT_BACKEND": ("dataframes", "default_backend"),
            "AUTOFRAME_QUALITY_THRESHOLD": ("quality", "quality_threshold"),
            "AUTOFRAME_LOG_LEVEL": ("logging", "level"),
            "AUTOFRAME_CHUNK_SIZE": ("dataframes", "chunk_size"),
            "AUTOFRAME_MAX_MEMORY": ("dataframes", "max_memory_usage"),
        }
        
        for env_var, config_path in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(self._config, config_path, value)
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge override dict into base dict."""
        for key, value in override.items():
            if (key in base and 
                isinstance(base[key], dict) and 
                isinstance(value, dict)):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _set_nested_value(self, config: Dict[str, Any], path: tuple, value: Any) -> None:
        """Set a nested configuration value."""
        for key in path[:-1]:
            config = config.setdefault(key, {})
        
        # Try to convert to appropriate type
        if isinstance(config.get(path[-1]), bool):
            value = value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(config.get(path[-1]), int):
            try:
                value = int(value)
            except ValueError:
                pass
        elif isinstance(config.get(path[-1]), float):
            try:
                value = float(value)
            except ValueError:
                pass
        
        config[path[-1]] = value
    
    def get(self, *path: str, default: Any = None) -> Any:
        """Get a configuration value by path.
        
        Args:
            *path: Configuration path (e.g., "data_sources", "mongodb", "timeout")
            default: Default value if path not found
            
        Returns:
            Configuration value or default
            
        Examples:
            >>> config = AutoFrameConfig()
            >>> timeout = config.get("data_sources", "mongodb", "connection_timeout")
            >>> backend = config.get("dataframes", "default_backend")
        """
        current = self._config
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def set(self, *path: str, value: Any) -> None:
        """Set a configuration value by path.
        
        Args:
            *path: Configuration path
            value: Value to set
        """
        self._set_nested_value(self._config, path, value)
    
    def get_mongodb_config(self) -> Dict[str, Any]:
        """Get MongoDB-specific configuration.
        
        Returns:
            Dict containing MongoDB configuration
        """
        return self.get("data_sources", "mongodb", default={})
    
    def get_dataframe_config(self) -> Dict[str, Any]:
        """Get dataframe-specific configuration.
        
        Returns:
            Dict containing dataframe configuration
        """
        return self.get("dataframes", default={})
    
    def get_quality_config(self) -> Dict[str, Any]:
        """Get quality assessment configuration.
        
        Returns:
            Dict containing quality configuration
        """
        return self.get("quality", default={})
    
    def validate(self) -> ConfigResult[None]:
        """Validate the current configuration.
        
        Returns:
            Result[None, ConfigurationError]: Success or validation error
        """
        try:
            # Validate MongoDB config
            mongodb_config = self.get_mongodb_config()
            if mongodb_config.get("connection_timeout", 0) <= 0:
                return Err(ConfigurationError("MongoDB connection_timeout must be positive"))
            
            # Validate dataframe config
            df_config = self.get_dataframe_config()
            valid_backends = ["pandas", "polars"]
            if df_config.get("default_backend") not in valid_backends:
                return Err(ConfigurationError(f"Invalid backend. Must be one of: {valid_backends}"))
            
            # Validate quality config
            quality_config = self.get_quality_config()
            threshold = quality_config.get("quality_threshold", 0.8)
            if not (0.0 <= threshold <= 1.0):
                return Err(ConfigurationError("Quality threshold must be between 0.0 and 1.0"))
            
            return Ok(None)
            
        except Exception as e:
            return Err(ConfigurationError(f"Configuration validation failed: {str(e)}"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary.
        
        Returns:
            Dict containing full configuration
        """
        return self._config.copy()


# Global configuration instance
_global_config: Optional[AutoFrameConfig] = None


def get_config() -> AutoFrameConfig:
    """Get the global configuration instance.
    
    Returns:
        AutoFrameConfig: Global configuration instance
    """
    global _global_config
    if _global_config is None:
        _global_config = AutoFrameConfig()
    return _global_config


def set_config(config: AutoFrameConfig) -> None:
    """Set the global configuration instance.
    
    Args:
        config: Configuration instance to use globally
    """
    global _global_config
    _global_config = config


def load_config_from_file(config_path: Union[str, Path]) -> ConfigResult[AutoFrameConfig]:
    """Load configuration from a file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Result[AutoFrameConfig, ConfigurationError]: Loaded configuration or error
    """
    try:
        config = AutoFrameConfig(config_path)
        validation_result = config.validate()
        
        if validation_result.is_err():
            return Err(validation_result.unwrap_err())
        
        return Ok(config)
        
    except Exception as e:
        return Err(ConfigurationError(f"Failed to load config from {config_path}: {str(e)}"))


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _global_config
    _global_config = AutoFrameConfig()