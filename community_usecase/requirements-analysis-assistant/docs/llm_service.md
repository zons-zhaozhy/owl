# LLM Service Documentation

## Overview
The LLM (Language Learning Model) service provides a unified interface for interacting with different LLM providers. Currently supported providers include:
- Deepseek
- OpenAI (planned)

## Configuration
LLM service configuration can be provided through environment variables or configuration files:

```bash
# Provider selection
LLM_PROVIDER=deepseek  # or openai
LLM_MODEL=deepseek-chat  # model name

# Generation parameters
LLM_TEMPERATURE=0.1  # Controls randomness (0-1)
LLM_MAX_TOKENS=4000  # Maximum tokens to generate

# API authentication
DEEPSEEK_API_KEY=your_api_key  # For Deepseek
OPENAI_API_KEY=your_api_key    # For OpenAI (planned)
```

## Supported Parameters

### Core Parameters
These parameters are supported by all providers:

| Parameter    | Type  | Range | Default | Description |
|-------------|-------|--------|---------|-------------|
| temperature | float | 0-1    | 0.1     | Controls randomness in generation. Lower values make output more focused and deterministic. |
| max_tokens  | int   | > 0    | 4000    | Maximum number of tokens to generate. |

### Optional Parameters
Support for these parameters varies by provider:

| Parameter         | Type   | Range | Default | Support          | Description |
|------------------|--------|--------|---------|------------------|-------------|
| top_p            | float  | 0-1    | 0.1     | OpenAI only     | Controls diversity via nucleus sampling |
| frequency_penalty| float  | -2 to 2| 0.1     | OpenAI only     | Reduces repetition of token sequences |
| presence_penalty | float  | -2 to 2| 0.1     | OpenAI only     | Reduces repetition of topics |
| stop_sequences   | list   | -      | None    | All providers   | Sequences that will stop generation |

## Usage Examples

### Basic Generation
```python
from owl_requirements.services.llm import create_llm_service

# Create service instance
config = {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "temperature": 0.1,
    "max_tokens": 4000
}
llm_service = create_llm_service(config)

# Generate text
response = await llm_service.generate(
    prompt="Analyze the following requirements...",
    temperature=0.1,
    max_tokens=4000
)
```

### Conversation History
```python
# Generate with conversation history
messages = [
    {"role": "user", "content": "What are the requirements?"},
    {"role": "assistant", "content": "Let me analyze them..."},
    {"role": "user", "content": "Can you provide more details?"}
]

response = await llm_service.generate_with_history(
    messages=messages,
    temperature=0.1,
    max_tokens=4000
)
```

## Error Handling

The service defines two main exception types:

1. `LLMServiceError`: Base exception for all LLM service errors
2. `InvalidParameterError`: Raised when invalid parameters are provided

Example error handling:
```python
from owl_requirements.services.base import LLMServiceError, InvalidParameterError

try:
    response = await llm_service.generate(
        prompt="...",
        temperature=1.5  # Invalid: must be between 0 and 1
    )
except InvalidParameterError as e:
    print(f"Invalid parameter: {e}")
except LLMServiceError as e:
    print(f"LLM service error: {e}")
```

## Best Practices

1. Parameter Selection:
   - Use lower temperature (0.1-0.3) for analytical tasks
   - Use higher temperature (0.7-0.9) for creative tasks
   - Set appropriate max_tokens based on expected response length

2. Error Handling:
   - Always handle potential exceptions
   - Implement retry logic for transient failures
   - Log errors with sufficient context

3. Resource Management:
   - Reuse service instances when possible
   - Implement rate limiting for API calls
   - Monitor token usage

4. Security:
   - Never hardcode API keys
   - Use environment variables or secure configuration
   - Validate and sanitize all inputs 