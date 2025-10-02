#!/usr/bin/env python3
"""
Authentication Configuration for Secure Prompt MCP Server
Handles JWT token verification, static tokens, and HMAC authentication
"""

import os
import logging
from typing import Dict, List, Optional
from fastmcp.server.auth.providers.jwt import JWTVerifier, StaticTokenVerifier

logger = logging.getLogger(__name__)

# Authentication mode configuration
AUTH_MODE = os.getenv("FASTMCP_AUTH_MODE", "static")  # static, jwt, hmac

# Static API Keys for Development/Testing
STATIC_TOKENS = {
    # Admin tokens - full access
    "spv-admin-dev-2024-abc123": {
        "client_id": "admin@company.com",
        "name": "Development Admin",
        "scopes": [
            "prompt:validate",
            "prompt:analyze", 
            "security:admin",
            "security:stats",
            "security:update"
        ]
    },
    
    # Standard user tokens - validation and analysis
    "spv-user-dev-2024-def456": {
        "client_id": "user@company.com",
        "name": "Development User",
        "scopes": [
            "prompt:validate",
            "prompt:analyze",
            "security:stats"
        ]
    },
    
    # Basic tokens - validation only
    "spv-basic-dev-2024-ghi789": {
        "client_id": "basic@company.com", 
        "name": "Basic User",
        "scopes": [
            "prompt:validate"
        ]
    },
    
    # Production-like tokens for testing
    "spv-prod-test-2024-jkl012": {
        "client_id": "production-client@company.com",
        "name": "Production Test Client",
        "scopes": [
            "prompt:validate",
            "prompt:analyze"
        ]
    },
    
    # Service account token
    "spv-service-2024-mno345": {
        "client_id": "service-account@company.com",
        "name": "Service Account",
        "scopes": [
            "prompt:validate",
            "prompt:analyze",
            "security:stats"
        ]
    }
}

# JWT Configuration for Production
JWT_CONFIG = {
    "jwks_uri": os.getenv("JWT_JWKS_URI", "https://your-auth-provider.com/.well-known/jwks.json"),
    "issuer": os.getenv("JWT_ISSUER", "https://your-auth-provider.com"),
    "audience": os.getenv("JWT_AUDIENCE", "secure-prompt-mcp-api"),
    "required_scopes": ["prompt:validate"]
}

# HMAC Configuration for Internal Services
HMAC_CONFIG = {
    "shared_secret": os.getenv("JWT_SHARED_SECRET", "your-32-character-minimum-shared-secret-key-here"),
    "issuer": os.getenv("JWT_ISSUER", "internal-auth-service"),
    "audience": os.getenv("JWT_AUDIENCE", "secure-prompt-mcp-internal"),
    "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
    "required_scopes": ["prompt:validate"]
}

# Scope definitions and descriptions
SCOPE_DEFINITIONS = {
    "prompt:validate": "Validate and sanitize prompts for security threats",
    "prompt:analyze": "Analyze semantic features of prompts",
    "security:admin": "Administrative access to security settings",
    "security:stats": "Access to security statistics and metrics",
    "security:update": "Update security configuration and levels"
}

def get_auth_verifier():
    """
    Get the appropriate authentication verifier based on environment configuration
    
    Returns:
        Authentication verifier instance (JWTVerifier or StaticTokenVerifier)
    """
    
    if AUTH_MODE == "jwt":
        logger.info("Initializing JWT token verification for production")
        
        # Validate required JWT configuration
        if not JWT_CONFIG["jwks_uri"] or JWT_CONFIG["jwks_uri"] == "https://your-auth-provider.com/.well-known/jwks.json":
            logger.warning("JWT_JWKS_URI not properly configured, using default")
        
        verifier = JWTVerifier(
            jwks_uri=JWT_CONFIG["jwks_uri"],
            issuer=JWT_CONFIG["issuer"],
            audience=JWT_CONFIG["audience"],
            required_scopes=JWT_CONFIG["required_scopes"]
        )
        
        logger.info(f"JWT verification configured - Issuer: {JWT_CONFIG['issuer']}, Audience: {JWT_CONFIG['audience']}")
        return verifier
    
    elif AUTH_MODE == "hmac":
        logger.info("Initializing HMAC token verification for internal services")
        
        # Validate shared secret
        if len(HMAC_CONFIG["shared_secret"]) < 32:
            logger.error("HMAC shared secret must be at least 32 characters long")
            raise ValueError("HMAC shared secret too short - minimum 32 characters required")
        
        verifier = JWTVerifier(
            public_key=HMAC_CONFIG["shared_secret"],  # For HMAC, this is the shared secret
            issuer=HMAC_CONFIG["issuer"],
            audience=HMAC_CONFIG["audience"],
            algorithm=HMAC_CONFIG["algorithm"],
            required_scopes=HMAC_CONFIG["required_scopes"]
        )
        
        logger.info(f"HMAC verification configured - Issuer: {HMAC_CONFIG['issuer']}, Algorithm: {HMAC_CONFIG['algorithm']}")
        return verifier
    
    else:  # static mode (default for development)
        logger.info("Initializing static token verification for development")
        
        verifier = StaticTokenVerifier(
            tokens=STATIC_TOKENS,
            required_scopes=["prompt:validate"]
        )
        
        logger.info(f"Static token verification configured with {len(STATIC_TOKENS)} tokens")
        
        # Log available tokens for development (mask the actual tokens)
        for token, info in STATIC_TOKENS.items():
            masked_token = f"{token[:12]}...{token[-6:]}"
            logger.debug(f"Available token: {masked_token} - {info['name']} ({info['client_id']})")
        
        return verifier

def check_scope_permission(token_claims: Dict, required_scope: str) -> bool:
    """
    Check if token has required scope permission
    
    Args:
        token_claims: Token claims dictionary
        required_scope: Required scope string
    
    Returns:
        True if token has required scope, False otherwise
    """
    # Handle both direct scopes and nested claims structure
    scopes = token_claims.get('scopes', [])
    if not scopes and 'claims' in token_claims:
        scopes = token_claims['claims'].get('scopes', [])
    return required_scope in scopes

def get_client_info(token_claims: Dict) -> Dict:
    """
    Extract client information from token claims
    
    Args:
        token_claims: Token claims dictionary
    
    Returns:
        Dictionary with client information
    """
    return {
        "client_id": token_claims.get('client_id', 'unknown'),
        "name": token_claims.get('name', 'Unknown Client'),
        "scopes": token_claims.get('scopes', []),
        "authenticated": True
    }

def log_authentication_config():
    """Log current authentication configuration"""
    logger.info("=" * 50)
    logger.info("SECURE PROMPT MCP AUTHENTICATION CONFIG")
    logger.info("=" * 50)
    logger.info(f"Authentication Mode: {AUTH_MODE.upper()}")
    
    if AUTH_MODE == "jwt":
        logger.info(f"JWT Issuer: {JWT_CONFIG['issuer']}")
        logger.info(f"JWT Audience: {JWT_CONFIG['audience']}")
        logger.info(f"JWKS URI: {JWT_CONFIG['jwks_uri']}")
        logger.info(f"Required Scopes: {JWT_CONFIG['required_scopes']}")
    
    elif AUTH_MODE == "hmac":
        logger.info(f"HMAC Issuer: {HMAC_CONFIG['issuer']}")
        logger.info(f"HMAC Audience: {HMAC_CONFIG['audience']}")
        logger.info(f"HMAC Algorithm: {HMAC_CONFIG['algorithm']}")
        logger.info(f"Required Scopes: {HMAC_CONFIG['required_scopes']}")
        logger.info(f"Shared Secret Length: {len(HMAC_CONFIG['shared_secret'])} characters")
    
    else:  # static
        logger.info(f"Static Tokens: {len(STATIC_TOKENS)} configured")
        logger.info("Available Client IDs:")
        for token, info in STATIC_TOKENS.items():
            logger.info(f"  - {info['client_id']} ({info['name']}) - Scopes: {len(info['scopes'])}")
    
    logger.info(f"Available Scopes: {len(SCOPE_DEFINITIONS)}")
    for scope, description in SCOPE_DEFINITIONS.items():
        logger.info(f"  - {scope}: {description}")
    
    logger.info("=" * 50)

# Environment configuration examples
def print_environment_examples():
    """Print environment configuration examples"""
    print("\n" + "=" * 60)
    print("ENVIRONMENT CONFIGURATION EXAMPLES")
    print("=" * 60)
    
    print("\n🔧 DEVELOPMENT (Static Tokens):")
    print("export FASTMCP_AUTH_MODE=static")
    print("# No additional configuration needed")
    
    print("\n🔧 PRODUCTION (JWT with JWKS):")
    print("export FASTMCP_AUTH_MODE=jwt")
    print("export JWT_JWKS_URI=https://your-auth.com/.well-known/jwks.json")
    print("export JWT_ISSUER=https://your-auth.com")
    print("export JWT_AUDIENCE=secure-prompt-mcp-api")
    
    print("\n🔧 INTERNAL SERVICES (HMAC):")
    print("export FASTMCP_AUTH_MODE=hmac")
    print("export JWT_SHARED_SECRET=your-32-character-minimum-shared-secret")
    print("export JWT_ISSUER=internal-auth-service")
    print("export JWT_AUDIENCE=secure-prompt-mcp-internal")
    print("export JWT_ALGORITHM=HS256")
    
    print("\n📋 USAGE EXAMPLES:")
    print("\n# Development with static token:")
    print('curl -H "Authorization: Bearer spv-admin-dev-2024-abc123" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"prompt": "My password is secret123"}\' \\')
    print('     http://localhost:8001/validate_and_secure_prompt')
    
    print("\n# Production with JWT:")
    print('curl -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"prompt": "My password is secret123"}\' \\')
    print('     http://localhost:8001/validate_and_secure_prompt')
    
    print("=" * 60)

if __name__ == "__main__":
    # When run directly, show configuration examples
    print_environment_examples()
    
    # Test verifier creation
    try:
        verifier = get_auth_verifier()
        log_authentication_config()
        print(f"\n✅ Authentication verifier created successfully: {type(verifier).__name__}")
    except Exception as e:
        print(f"\n❌ Error creating authentication verifier: {e}")
