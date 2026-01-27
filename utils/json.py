"""JSON utilities for structured output parsing and validation."""

import json
from typing import Any, Optional
from pydantic import BaseModel, ValidationError


def parse_json_safely(text: str) -> Optional[dict]:
    """Parse JSON from text, handling markdown code blocks.
    
    Args:
        text: Text that may contain JSON (possibly in code blocks)
    
    Returns:
        Parsed dict or None if parsing fails
    """
    # Try to extract JSON from markdown code blocks
    json_match = None
    
    # Look for ```json ... ``` or ``` ... ```
    import re
    code_block_pattern = r'```(?:json)?\s*\n(.*?)\n```'
    match = re.search(code_block_pattern, text, re.DOTALL)
    if match:
        json_match = match.group(1)
    else:
        # Look for { ... } directly
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            json_match = brace_match.group(0)
    
    if json_match:
        text = json_match
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def validate_with_pydantic(data: dict, model_class: type[BaseModel]) -> tuple[Optional[BaseModel], Optional[str]]:
    """Validate data against a Pydantic model.
    
    Args:
        data: Data dict to validate
        model_class: Pydantic model class
    
    Returns:
        Tuple of (validated_model, error_message)
        If validation succeeds, returns (model, None)
        If validation fails, returns (None, error_message)
    """
    try:
        model = model_class(**data)
        return model, None
    except ValidationError as e:
        error_msg = f"Validation error: {e.json()}"
        return None, error_msg

