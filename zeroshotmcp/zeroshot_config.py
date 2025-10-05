#!/usr/bin/env python3
"""
Configuration file for Zero-Shot Secure Prompt MCP Server
Customize settings here for your specific use case
"""

from enum import Enum

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Server Configuration
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8002,
    "name": "Zero-Shot Secure Prompt Validator"
}

# Model Configuration
MODEL_CONFIG = {
    "primary_model": "facebook/bart-large-mnli",
    "fallback_model": "typeform/distilbert-base-uncased-mnli",
    "use_gpu": True,  # Will auto-detect CUDA availability
    "max_length": 512,  # Maximum input length for classification
}

# Security Configuration
SECURITY_CONFIG = {
    "default_level": SecurityLevel.MEDIUM,
    "confidence_thresholds": {
        "low": 0.8,      # Only block high-confidence threats
        "medium": 0.7,   # Block medium+ confidence threats
        "high": 0.6      # Block low+ confidence threats
    },
    "sanitization_enabled": True,
    "detailed_analysis_enabled": True
}

# Classification Categories
CUSTOM_CATEGORIES = {
    # Add your custom threat categories here
    "additional_threats": [
        # "contains financial information",
        # "contains medical data",
        # "contains legal documents"
    ],
    
    # Add custom detailed sub-categories
    "custom_detailed": {
        # "financial": [
        #     "credit card number",
        #     "bank account details",
        #     "social security number"
        # ]
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_classifications": True,  # Log all classification results
    "log_sanitization": True      # Log all sanitization actions
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    "batch_size": 1,  # Process prompts individually
    "cache_model": True,  # Keep model loaded in memory
    "timeout_seconds": 30,  # Request timeout
    "max_concurrent_requests": 10
}

# Sanitization Configuration
SANITIZATION_CONFIG = {
    # Detection thresholds
    "zeroshot_trigger_threshold": 0.5,  # Confidence to trigger sanitization
    
    # Entropy detection settings
    "entropy_threshold_high": 4.0,      # Always mask (very random)
    "entropy_threshold_medium": 3.5,    # Mask if in context
    "require_mixed_case": True,         # Check for upper+lower+digit
    
    # Keyword backup settings  
    "min_credential_length": 6,         # Minimum length
    "excluded_words": ['example', 'localhost', 'password', 'username', 'default', 'integration']
}
