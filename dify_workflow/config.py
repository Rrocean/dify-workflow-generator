"""
Configuration management for Dify Workflow Generator.

Supports loading from environment variables and config files.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class Config:
    """Configuration for Dify Workflow Generator."""
    
    # OpenAI API settings
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_default_model: str = "gpt-4"
    
    # Default workflow settings
    default_model_provider: str = "openai"
    default_model_name: str = "gpt-4"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    
    # Layout settings
    default_layout_spacing_x: int = 300
    default_layout_spacing_y: int = 200
    default_layout_start_x: int = 100
    default_layout_start_y: int = 300
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Export settings
    default_export_format: str = "yaml"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL"),
            openai_default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4"),
            default_model_provider=os.getenv("DIFY_DEFAULT_PROVIDER", "openai"),
            default_model_name=os.getenv("DIFY_DEFAULT_MODEL", "gpt-4"),
            default_temperature=float(os.getenv("DIFY_DEFAULT_TEMPERATURE", "0.7")),
            default_max_tokens=int(os.getenv("DIFY_DEFAULT_MAX_TOKENS", "4096")),
            log_level=os.getenv("DIFY_LOG_LEVEL", "INFO"),
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Load configuration from a dictionary."""
        # Filter only valid fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


# Global config instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config.from_env()
    return _global_config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _global_config
    _global_config = config


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _global_config
    _global_config = Config.from_env()
