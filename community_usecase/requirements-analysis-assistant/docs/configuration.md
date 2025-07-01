# Configuration Guide

## Overview

The OWL Requirements Analysis Assistant can be configured through multiple methods:
1. Environment variables
2. Configuration files
3. Command-line arguments

This guide explains each configuration method and available options.

## Environment Variables

Create a `.env` file in the project root:

```bash
# Application settings
APP_NAME=OWL Requirements Analysis Assistant
DEBUG=false

# Web server settings
WEB_HOST=127.0.0.1
WEB_PORT=7860

# LLM settings
LLM_PROVIDER=deepseek
LLM_API_KEY=your-api-key-here
LLM_API_BASE=https://api.deepseek.com/v1

# Output settings
OUTPUT_DIR=output
```

## Configuration Files

### Settings Module

The `src/config/settings.py` file defines all configuration options:

```python
class Settings(BaseSettings):
    # Project paths
    project_root: Path
    output_dir: Path
    
    # Web server settings
    web_host: str
    web_port: int
    
    # LLM settings
    llm_provider: str
    llm_api_key: Optional[str]
    llm_api_base: Optional[str]
    
    # Agent settings
    agent_config: Dict[str, Any]
```

### Agent Configuration

Agent-specific settings in `src/config/agents.py`:

```python
REQUIREMENTS_EXTRACTOR_CONFIG = {
    "name": "RequirementsExtractor",
    "model": "deepseek-chat",
    "temperature": 0.1,
    "max_tokens": 2000
}

REQUIREMENTS_ANALYZER_CONFIG = {
    "name": "RequirementsAnalyzer",
    "model": "deepseek-chat",
    "temperature": 0.2,
    "max_tokens": 3000
}

DOCUMENTATION_GENERATOR_CONFIG = {
    "name": "DocumentationGenerator",
    "model": "deepseek-chat",
    "temperature": 0.3,
    "max_tokens": 4000
}

QUALITY_CHECKER_CONFIG = {
    "name": "QualityChecker",
    "model": "deepseek-chat",
    "temperature": 0.1,
    "max_tokens": 2000
}
```

## Command-line Arguments

Available command-line arguments:

```bash
# Mode selection
--mode {cli,web,once}    # Operating mode (default: web)

# Web server options
--host TEXT             # Web server host (default: 127.0.0.1)
--port INTEGER         # Web server port (default: 7860)

# Output options
--output-dir TEXT      # Output directory (default: output)

# Logging options
--log-level TEXT       # Log level (default: INFO)
--log-file TEXT       # Log file path

# LLM options
--llm-provider TEXT    # LLM provider (default: deepseek)
--llm-api-key TEXT    # LLM API key
--llm-api-base TEXT   # LLM API base URL
```

## Configuration Precedence

Configuration values are loaded in the following order (later values override earlier ones):

1. Default values in code
2. Configuration files
3. Environment variables
4. Command-line arguments

## Validation

The system validates configuration on startup:

1. Required paths exist
2. API keys are provided when needed
3. Port numbers are valid
4. Required agent configurations exist

## Security

Security-related configuration:

1. API keys should be stored in environment variables
2. Use HTTPS for production deployments
3. Set appropriate CORS policies
4. Configure allowed hosts

## Examples

### Development Configuration

```bash
# .env
DEBUG=true
WEB_PORT=7860
LLM_PROVIDER=deepseek
```

### Production Configuration

```bash
# .env
DEBUG=false
WEB_HOST=0.0.0.0
WEB_PORT=80
LLM_PROVIDER=deepseek
ALLOWED_HOSTS=["example.com"]
```

### Custom Agent Configuration

```python
# config/agents.py
CUSTOM_AGENT_CONFIG = {
    "name": "CustomAgent",
    "model": "deepseek-chat",
    "temperature": 0.5,
    "max_tokens": 3000,
    "custom_param": "value"
}
``` 