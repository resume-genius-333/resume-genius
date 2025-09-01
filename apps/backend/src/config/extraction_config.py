"""Configuration for extraction system."""

from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ModelConfig(BaseModel):
    """Configuration for LLM model."""
    
    name: str = Field(
        default="gpt-5-nano",
        description="Model name to use for extraction"
    )
    
    max_retries: int = Field(
        default=2,
        description="Maximum retries for failed extractions"
    )
    
    timeout: int = Field(
        default=60,
        description="Timeout in seconds for model calls"
    )
    
    temperature: float = Field(
        default=0.1,
        description="Temperature for model responses (lower = more deterministic)"
    )


class ExtractionStrategy(BaseModel):
    """Configuration for extraction strategy."""
    
    use_progressive: bool = Field(
        default=True,
        description="Use progressive extraction (extract then refine sections)"
    )
    
    validate_sections: bool = Field(
        default=True,
        description="Validate each section after extraction"
    )
    
    extract_confidence: bool = Field(
        default=True,
        description="Calculate confidence scores for extracted data"
    )
    
    max_concurrent_sections: int = Field(
        default=4,
        description="Maximum sections to extract concurrently in progressive mode"
    )


class PromptConfig(BaseModel):
    """Configuration for extraction prompts."""
    
    include_examples: bool = Field(
        default=True,
        description="Include examples in extraction prompts"
    )
    
    strict_mode: bool = Field(
        default=False,
        description="Use strict extraction (only extract explicitly mentioned info)"
    )
    
    language: str = Field(
        default="en",
        description="Language for prompts and extraction"
    )
    
    custom_instructions: Optional[str] = Field(
        default=None,
        description="Custom instructions to append to all prompts"
    )


class BatchConfig(BaseModel):
    """Configuration for batch processing."""
    
    max_concurrent: int = Field(
        default=5,
        description="Maximum concurrent extractions in batch mode"
    )
    
    deduplicate: bool = Field(
        default=True,
        description="Deduplicate files before batch processing"
    )
    
    continue_on_error: bool = Field(
        default=True,
        description="Continue batch processing even if some files fail"
    )
    
    save_intermediate: bool = Field(
        default=False,
        description="Save intermediate results during batch processing"
    )


class StorageConfig(BaseModel):
    """Configuration for file storage."""
    
    temp_dir: Optional[Path] = Field(
        default=None,
        description="Directory for temporary files"
    )
    
    output_dir: Optional[Path] = Field(
        default=None,
        description="Directory for output files"
    )
    
    cleanup_temp: bool = Field(
        default=True,
        description="Automatically cleanup temporary files"
    )
    
    max_file_size_mb: int = Field(
        default=10,
        description="Maximum file size in MB"
    )


class LiteLLMConfig(BaseModel):
    """Configuration for LiteLLM connection."""
    
    base_url: str = Field(
        default_factory=lambda: os.environ.get("LITELLM_BASE_URL", "http://127.0.0.1:4000"),
        description="LiteLLM base URL"
    )
    
    api_key: str = Field(
        default_factory=lambda: os.environ.get("LITELLM_API_KEY", ""),
        description="LiteLLM API key"
    )
    
    use_proxy: bool = Field(
        default=False,
        description="Whether to use proxy for LiteLLM"
    )


class ExtractionConfig(BaseModel):
    """Main configuration for extraction system."""
    
    model: ModelConfig = Field(
        default_factory=ModelConfig,
        description="Model configuration"
    )
    
    strategy: ExtractionStrategy = Field(
        default_factory=ExtractionStrategy,
        description="Extraction strategy configuration"
    )
    
    prompts: PromptConfig = Field(
        default_factory=PromptConfig,
        description="Prompt configuration"
    )
    
    batch: BatchConfig = Field(
        default_factory=BatchConfig,
        description="Batch processing configuration"
    )
    
    storage: StorageConfig = Field(
        default_factory=StorageConfig,
        description="Storage configuration"
    )
    
    litellm: LiteLLMConfig = Field(
        default_factory=LiteLLMConfig,
        description="LiteLLM configuration"
    )
    
    @classmethod
    def from_env(cls) -> "ExtractionConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables if present
        if model_name := os.environ.get("EXTRACTION_MODEL"):
            config.model.name = model_name
        
        if max_retries := os.environ.get("EXTRACTION_MAX_RETRIES"):
            config.model.max_retries = int(max_retries)
        
        if use_progressive := os.environ.get("EXTRACTION_USE_PROGRESSIVE"):
            config.strategy.use_progressive = use_progressive.lower() == "true"
        
        if max_concurrent := os.environ.get("EXTRACTION_MAX_CONCURRENT"):
            config.batch.max_concurrent = int(max_concurrent)
        
        return config
    
    @classmethod
    def from_file(cls, config_path: Path) -> "ExtractionConfig":
        """Load configuration from JSON or YAML file."""
        import json
        
        if config_path.suffix == ".json":
            with open(config_path) as f:
                data = json.load(f)
        elif config_path.suffix in [".yaml", ".yml"]:
            try:
                import yaml
                with open(config_path) as f:
                    data = yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML required for YAML config files")
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        return cls(**data)
    
    def to_file(self, config_path: Path) -> None:
        """Save configuration to JSON or YAML file."""
        import json
        
        data = self.model_dump(exclude_none=True)
        
        if config_path.suffix == ".json":
            with open(config_path, "w") as f:
                json.dump(data, f, indent=2)
        elif config_path.suffix in [".yaml", ".yml"]:
            try:
                import yaml
                with open(config_path, "w") as f:
                    yaml.safe_dump(data, f, default_flow_style=False)
            except ImportError:
                raise ImportError("PyYAML required for YAML config files")
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")


# Default configuration instance
default_config = ExtractionConfig()

# Load from environment
env_config = ExtractionConfig.from_env()


def get_config(
    config_path: Optional[Path] = None,
    use_env: bool = True,
) -> ExtractionConfig:
    """Get extraction configuration.
    
    Args:
        config_path: Optional path to configuration file.
        use_env: Whether to use environment variables.
        
    Returns:
        ExtractionConfig instance.
    """
    if config_path and config_path.exists():
        config = ExtractionConfig.from_file(config_path)
    elif use_env:
        config = env_config
    else:
        config = default_config
    
    return config