"""
LLM Security Module.

Protects against:
- Prompt injection attacks
- Data exfiltration via AI
- Jailbreak attempts
- Output manipulation

Features:
- Input sanitization for prompts
- Prompt injection detection
- Output filtering for PII
- Context isolation
"""

import re
import logging
from typing import Any, Dict

import bleach


logger = logging.getLogger(__name__)


# Prompt injection patterns to detect
INJECTION_PATTERNS = [
    # System override attempts
    r"(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|rules)",
    r"(?i)system\s+(override|prompt|instructions?)",
    r"(?i)new\s+(instructions?|directive|role|character)",
    
    # Information extraction attempts
    r"(?i)(print|show|display|list|dump|export)\s+(all|the|user|database|table)",
    r"(?i)SELECT\s+\*\s+FROM",
    r"(?i)(reveal|disclose|expose)\s+(data|information|secrets?)",
    
    # Role manipulation
    r"(?i)you\s+are\s+(now|currently|no\s+longer)",
    r"(?i)pretend\s+(you|to\s+be)",
    r"(?i)act\s+as\s+(a|an)\s+",
    
    # Delimiter attacks
    r"(?i)(#|\*\*\*|---)\s*(end|stop|ignore)",
    r"(?i)>\s*assistant:",
    r"(?i)>\s*system:",
    
    # Unicode/encoding tricks
    r"[\u200B-\u200D\uFEFF]",  # Zero-width characters
    r"&#\d+;",  # HTML entities
]

COMPILED_INJECTION_PATTERNS = [re.compile(pattern) for pattern in INJECTION_PATTERNS]


# PII patterns to detect in outputs
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "uuid": r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
}

COMPILED_PII_PATTERNS = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in PII_PATTERNS.items()
}


def sanitize_llm_input(text: str, max_length: int = 2000) -> str:
    """
    Sanitize user input before sending to LLM.
    
    Args:
        text: User input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
        
    Raises:
        ValueError: If input contains potential injection
    """
    if not text:
        return ""
    
    # Trim to max length
    text = text[:max_length]
    
    # Remove HTML/script tags
    text = bleach.clean(text, tags=[], strip=True)
    
    # Normalize whitespace
    text = " ".join(text.split())
    
    # Detect prompt injection attempts
    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(
                f"Potential prompt injection detected",
                extra={"input_preview": text[:100]}
            )
            raise ValueError(
                "Your input contains potentially unsafe content. Please rephrase your question."
            )
    
    return text


def detect_prompt_injection(prompt: str) -> bool:
    """
    Check if prompt contains injection attempts.
    
    Args:
        prompt: Full prompt to check
        
    Returns:
        True if injection detected, False otherwise
    """
    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(prompt):
            return True
    return False


def filter_pii_from_output(text: str, redact_with: str = "[REDACTED]") -> str:
    """
    Remove PII from LLM output before returning to user.
    
    Args:
        text: LLM output text
        redact_with: Replacement string for PII
        
    Returns:
        Text with PII redacted
    """
    if not text:
        return ""
    
    filtered = text
    
    # Redact each type of PII
    for pii_type, pattern in COMPILED_PII_PATTERNS.items():
        if pii_type != "uuid":  # Don't redact all UUIDs, too broad
            filtered = pattern.sub(redact_with, filtered)
    
    return filtered


def validate_context_isolation(context: Dict[str, Any], user_id: str) -> bool:
    """
    Ensure context only contains data for the requesting user.
    
    Args:
        context: Profile context being passed to LLM
        user_id: ID of requesting user
        
    Returns:
        True if context is properly isolated, False otherwise
    """
    # Check profile user_id matches
    profile = context.get("profile", {})
    if profile and str(profile.get("id")) != str(user_id):
        logger.error(
            "Context isolation violation detected",
            extra={"expected_user": user_id, "context_user": profile.get("id")}
        )
        return False
    
    # Check all sub-entities belong to user
    for key in ["skills", "education", "experience", "projects"]:
        items = context.get(key, [])
        for item in items:
            if str(item.get("user_id")) != str(user_id):
                logger.error(
                    f"Context isolation violation in {key}",
                    extra={"expected_user": user_id, "found_user": item.get("user_id")}
                )
                return False
    
    return True


def create_safe_prompt(template: str, user_input: str, **kwargs) -> str:
    """
    Create a safe prompt by sanitizing inputs and using delimited sections.
    
    Args:
        template: Prompt template with {user_input} placeholder
        user_input: Unsanitized user input
        **kwargs: Other template variables
        
    Returns:
        Safe prompt string
    """
    # Sanitize user input
    safe_input = sanitize_llm_input(user_input)
    
    # Use XML-style delimiters for clear separation
    delimited_input = f"<user_query>\n{safe_input}\n</user_query>"
    
    # Format template
    prompt = template.format(user_input=delimited_input, **kwargs)
    
    return prompt


def enforce_output_constraints(output: str, max_length: int = 5000) -> str:
    """
    Enforce constraints on LLM output.
    
    Args:
        output: Raw LLM output
        max_length: Maximum allowed output length
        
    Returns:
        Constrained output
    """
    # Trim length
    if len(output) > max_length:
        output = output[:max_length] + "... [truncated]"
    
    # Filter PII
    output = filter_pii_from_output(output)
    
    # Remove any code blocks that might execute
    output = output.replace("<script>", "").replace("</script>", "")
    output = output.replace("javascript:", "")
    
    return output
