#!/usr/bin/env python3
"""
Secure Prompt MCP Server
A Model Context Protocol server that vets and secures prompts before they reach the AI model.
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class SecurityResult:
    is_safe: bool
    modified_prompt: str
    warnings: List[str]
    blocked_patterns: List[str]
    confidence: float

class PromptSecurityValidator:
    """Main class for validating and securing prompts"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        self.security_level = security_level
        self.setup_patterns()
    
    def setup_patterns(self):
        """Initialize security patterns and rules"""
        
        # Prompt injection patterns
        self.injection_patterns = [
            r"ignore\s+(?:all\s+)?(?:previous|above|all)\s+instructions",
            r"forget\s+(?:(?:everything|all)\s+)?(?:above|before|previous)",
            r"disregard\s+(?:all\s+)?(?:previous|above|prior)\s+(?:instructions|commands|prompts)",
            r"act\s+as\s+(?:if|though)\s+you\s+are",
            r"pretend\s+(?:to\s+be|you\s+are)",
            r"simulate\s+(?:being|a)",
            r"role\s*play\s+(?:as|being)",
            r"begin\s+your\s+response\s+with",
            r"respond\s+(?:only\s+)?with",
            r"output\s+(?:only\s+)?the\s+(?:word|phrase)",
            r"repeat\s+(?:after\s+me|the\s+following)",
        ]
        
        # Sensitive data patterns - Enhanced to catch various formats and contexts
        self.sensitive_patterns = {
            # API Keys - Multiple formats and contexts
            'api_key': [
                r'(?i)(?:api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_+\-]{8,})["\']?', 
                r'(?i)(?:my\s+)?api[_-]?key\s+(?:is\s+)?["\']?([a-zA-Z0-9_+\-]{8,})["\']?',  
                r'(?i)["\']?([a-zA-Z0-9_+\-]{8,})["\']?\s+(?:is\s+)?(?:the\s+)?api[_-]?key',  
                r'(?i)(?:use\s+)?["\']?([a-zA-Z0-9_+\-]{8,})["\']?\s+(?:to\s+)?(?:connect|access)',
                r'(?i)(?:connect|access)\s+(?:to\s+)?(?:the\s+)?(?:endpoint|api|gateway)\s+(?:with\s+)?["\']?([a-zA-Z0-9_+\-]{8,})["\']?', 
                r'(?i)(?:i\s+have\s+an?\s+)?api[_-]?key\s+([a-zA-Z0-9_+\-]{8,})',
                r'(?i)([a-zA-Z0-9_+\-]{8,})\s+(?:is\s+)?(?:the\s+)?api[_-]?key', 
                r'(?i)(?:my\s+)?api[_-]?key\s+(?:to\s+)?(?:connect\s+to\s+)?(?:the\s+)?(?:sms\s+)?gateway\s+(?:is\s+)?([a-zA-Z0-9_+\-]{8,})',
                r'(?i)([A-Z0-9_+\-]{8,})\s+(?:is\s+)?(?:the\s+)?api[_-]?key\s+(?:to\s+)?(?:the\s+)?(?:sms\s+)?gateway', 
                # Simple patterns for common cases
                r'(?i)api\s*[_-]?\s*key\s+([A-Z0-9_+\-]{8,})', 
                r'(?i)([A-Z0-9_+\-]{8,})\s+is\s+(?:the\s+)?api\s*[_-]?\s*key', 
                r'(?i)([A-Z0-9_+\-]{8,})\s+is\s+(?:the\s+)?api\s*[_-]?\s*key\s+to\s+(?:the\s+)?(?:sms\s+)?gateway', 
            ],
            
            # Passwords - Various contexts
            'password': [
                r'(?i)password\s*[:=]\s*["\']?([^\s"\']{6,})["\']?',  
                r'(?i)(?:my\s+)?password\s+(?:is\s+)?["\']?([^\s"\']{6,})["\']?',  
                r'(?i)["\']?([^\s"\']{6,})["\']?\s+(?:is\s+)?(?:the\s+)?password', 
                r'(?i)(?:login|authenticate)\s+(?:with\s+)?(?:password\s+)?["\']?([^\s"\']{6,})["\']?',  
                r'(?i)(?:database|db)\s+password\s+(?:is\s+)?["\']?([^\s"\']{6,})["\']?', 
            ],
            
            # Tokens - Bearer tokens, access tokens, etc.
            'token': [
                r'(?i)(?:bearer\s+)?token\s*[:=]\s*["\']?([a-zA-Z0-9._+\-]{15,})["\']?', 
                r'(?i)(?:my\s+)?(?:access\s+)?token\s+(?:is\s+)?["\']?([a-zA-Z0-9._+\-]{15,})["\']?',  
                r'(?i)["\']?([a-zA-Z0-9._+\-]{15,})["\']?\s+(?:is\s+)?(?:the\s+)?(?:access\s+)?token', 
                r'(?i)(?:authorization|auth)\s+(?:header\s+)?["\']?([a-zA-Z0-9._+\-]{15,})["\']?', 
            ],
            
            # Secrets - API secrets, client secrets, etc.
            'secret': [
                r'(?i)(?:api\s+)?secret\s*[:=]\s*["\']?([a-zA-Z0-9_+\-]{12,})["\']?',  
                r'(?i)(?:my\s+)?(?:api\s+)?secret\s+(?:is\s+)?["\']?([a-zA-Z0-9_+\-]{12,})["\']?',  
                r'(?i)["\']?([a-zA-Z0-9_+\-]{12,})["\']?\s+(?:is\s+)?(?:the\s+)?(?:api\s+)?secret',  
                r'(?i)(?:client\s+)?secret\s+(?:for\s+)?(?:the\s+)?(?:api|service)\s+["\']?([a-zA-Z0-9_+\-]{12,})["\']?',  
            ],
            
            # Private Keys
            'private_key': [
                r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
                r'(?i)(?:private\s+)?key\s*[:=]\s*["\']?([a-zA-Z0-9_+\-=\/]{50,})["\']?',  
                r'(?i)(?:my\s+)?(?:private\s+)?key\s+(?:is\s+)?["\']?([a-zA-Z0-9_+\-=\/]{50,})["\']?',  
            ],
            
            # Database credentials
            'db_credentials': [
                r'(?i)(?:database|db)\s+(?:password|pass)\s*[:=]\s*["\']?([^\s"\']{6,})["\']?',  
                r'(?i)(?:db|database)\s+(?:user|username)\s*[:=]\s*["\']?([a-zA-Z0-9_]{3,})["\']?', 
                r'(?i)(?:connection\s+)?string\s*[:=]\s*["\']?([a-zA-Z0-9_+\-=\/\.:]{20,})["\']?', 
            ],
            
            # Email addresses
            'email': [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  
                r'(?i)(?:email|e-mail)\s*[:=]\s*["\']?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']?', 
                r'(?i)(?:my\s+)?email\s+(?:is\s+)?["\']?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']?', 
            ],
            
            # Credit card numbers
            'credit_card': [
                r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',  
                r'(?i)(?:credit\s+card|card\s+number)\s*[:=]\s*["\']?([0-9\s\-]{13,19})["\']?',
                r'(?i)(?:my\s+)?(?:credit\s+)?card\s+(?:number\s+)?(?:is\s+)?["\']?([0-9\s\-]{13,19})["\']?',
            ],
            
            # SSH Keys
            'ssh_key': [
                r'(?i)(?:ssh|rsa)\s+(?:key|private\s+key)\s*[:=]\s*["\']?([a-zA-Z0-9_+\-=\/]{50,})["\']?',  
                r'(?i)(?:my\s+)?(?:ssh|rsa)\s+(?:key|private\s+key)\s+(?:is\s+)?["\']?([a-zA-Z0-9_+\-=\/]{50,})["\']?', 
                r'ssh-rsa\s+[a-zA-Z0-9_+\-=\/]{50,}',
            ],
            
            # JWT Tokens
            'jwt_token': [
                r'(?i)(?:jwt|json\s+web\s+token)\s*[:=]\s*["\']?([a-zA-Z0-9_+\-=\/\.]{50,})["\']?', 
                r'(?i)(?:my\s+)?(?:jwt|json\s+web\s+token)\s+(?:is\s+)?["\']?([a-zA-Z0-9_+\-=\/\.]{50,})["\']?',
                r'["\']?([a-zA-Z0-9_+\-=\/\.]{50,})["\']?\s+(?:is\s+)?(?:the\s+)?(?:jwt|json\s+web\s+token)',  
            ],
            
            # AWS/GCP/Azure credentials
            'cloud_credentials': [
                r'(?i)(?:aws|amazon)\s+(?:access\s+)?(?:key|secret)\s*[:=]\s*["\']?([a-zA-Z0-9_+\-]{15,})["\']?',  
                r'(?i)(?:gcp|google)\s+(?:service\s+)?(?:account\s+)?(?:key|secret)\s*[:=]\s*["\']?([a-zA-Z0-9_+\-]{15,})["\']?', 
                r'(?i)(?:azure)\s+(?:client\s+)?(?:secret|key)\s*[:=]\s*["\']?([a-zA-Z0-9_+\-]{15,})["\']?',
            ]
        }
        
        # Malicious code patterns
        self.malicious_patterns = [
            r'(?i)(?:rm\s+-rf|del\s+/[sq])',  # Destructive commands
            r'(?i)(?:wget|curl).*(?:\.sh|\.py).*\|\s*(?:bash|sh|python)',  # Download and execute
            r'(?i)(?:nc|netcat).*-[el].*\d+',  # Netcat backdoors
            r'(?i)eval\s*\(',  # Code evaluation
            r'(?i)exec\s*\(',  # Code execution
            r'(?i)system\s*\(',  # System calls
            r'(?i)subprocess\.(?:call|run|Popen)',  # Subprocess execution
            r'(?i)os\.(?:system|popen|spawn)',  # OS system calls
            r'(?i)__import__\s*\(',  # Dynamic imports
        ]
        
        # Jailbreak attempt patterns
        self.jailbreak_patterns = [
            r"(?i)you\s+(?:must|should|will)\s+(?:help|assist|comply)",
            r"(?i)it'?s\s+(?:important|urgent|critical)",
            r"(?i)(?:bypass|override|ignore)\s+(?:safety|security|guidelines)",
            r"(?i)hypothetically\s+speaking",
            r"(?i)in\s+(?:theory|a\s+fictional\s+scenario)",
            r"(?i)what\s+(?:would|could)\s+happen\s+if",
        ]
    
    async def validate_prompt(self, prompt: str, context: Optional[Dict] = None) -> SecurityResult:
        """Main validation method"""
        warnings = []
        blocked_patterns = []
        modified_prompt = prompt
        confidence = 1.0
        
        # Check for prompt injection
        injection_score = self._check_injection_patterns(prompt)
        if injection_score > 0.0:
            warnings.append("Potential prompt injection detected")
            if self.security_level == SecurityLevel.HIGH:
                blocked_patterns.append("prompt_injection")
                return SecurityResult(
                    is_safe=False,
                    modified_prompt=prompt,
                    warnings=warnings,
                    blocked_patterns=blocked_patterns,
                    confidence=injection_score
                )
        
        # Sanitize sensitive data
        modified_prompt, sensitive_found = self._sanitize_sensitive_data(modified_prompt)
        if sensitive_found:
            warnings.extend([f"Sanitized {pattern}" for pattern in sensitive_found])
        
        # Check for malicious patterns
        malicious_found = self._check_malicious_patterns(modified_prompt)
        if malicious_found:
            if self.security_level in [SecurityLevel.MEDIUM, SecurityLevel.HIGH]:
                blocked_patterns.extend(malicious_found)
                return SecurityResult(
                    is_safe=False,
                    modified_prompt=prompt,
                    warnings=warnings,
                    blocked_patterns=blocked_patterns,
                    confidence=0.9
                )
        
        # Check for jailbreak attempts
        jailbreak_score = self._check_jailbreak_patterns(modified_prompt)
        if jailbreak_score > 0.6:
            warnings.append("Potential jailbreak attempt detected")
            if self.security_level == SecurityLevel.HIGH:
                blocked_patterns.append("jailbreak_attempt")
                confidence = min(confidence, 1 - jailbreak_score)
        
        # Additional context-based checks
        if context:
            context_warnings = self._check_context_security(modified_prompt, context)
            warnings.extend(context_warnings)
        
        is_safe = len(blocked_patterns) == 0
        
        return SecurityResult(
            is_safe=is_safe,
            modified_prompt=modified_prompt,
            warnings=warnings,
            blocked_patterns=blocked_patterns,
            confidence=confidence
        )
    
    def _check_injection_patterns(self, prompt: str) -> float:
        """Check for prompt injection patterns"""
        matches = 0
        total_patterns = len(self.injection_patterns)
        
        for pattern in self.injection_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                matches += 1
        
        return matches / total_patterns if total_patterns > 0 else 0.0
    
    def _sanitize_sensitive_data(self, prompt: str) -> Tuple[str, List[str]]:
        """Remove or mask sensitive information"""
        modified = prompt
        found_patterns = []
        
        for pattern_name, patterns in self.sensitive_patterns.items():
            # Handle both single patterns and lists of patterns
            pattern_list = patterns if isinstance(patterns, list) else [patterns]
            
            for pattern in pattern_list:
                matches = re.finditer(pattern, modified, re.IGNORECASE)
                for match in matches:
                    if pattern_name == 'email':
                        # Partially mask email
                        email = match.group(0)
                        if '@' in email:
                            username, domain = email.split('@', 1)
                            masked_email = f"{username[:2]}***@{domain}"
                            modified = modified.replace(email, masked_email)
                    elif pattern_name in ['api_key', 'token', 'secret', 'password', 'db_credentials', 'ssh_key', 'jwt_token', 'cloud_credentials']:
                        # Replace with placeholder
                        modified = re.sub(pattern, f'[{pattern_name.upper()}_REMOVED]', modified, flags=re.IGNORECASE)
                    elif pattern_name == 'private_key':
                        modified = re.sub(pattern, '[PRIVATE_KEY_REMOVED]', modified, flags=re.IGNORECASE)
                    elif pattern_name == 'credit_card':
                        # Mask credit card number
                        cc_num = match.group(0)
                        # Remove spaces and dashes for masking
                        clean_cc = re.sub(r'[\s\-]', '', cc_num)
                        if len(clean_cc) >= 8:
                            masked = f"{clean_cc[:4]}****{clean_cc[-4:]}"
                            modified = modified.replace(cc_num, masked)
                    
                    if pattern_name not in found_patterns:
                        found_patterns.append(pattern_name)
        
        return modified, found_patterns
    
    def _check_malicious_patterns(self, prompt: str) -> List[str]:
        """Check for potentially malicious code patterns"""
        found_patterns = []
        
        for pattern in self.malicious_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                found_patterns.append("malicious_code")
                break
        
        return found_patterns
    
    def _check_jailbreak_patterns(self, prompt: str) -> float:
        """Check for jailbreak attempt patterns"""
        matches = 0
        total_patterns = len(self.jailbreak_patterns)
        
        for pattern in self.jailbreak_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                matches += 1
        
        return matches / total_patterns if total_patterns > 0 else 0.0
    
    def _check_context_security(self, prompt: str, context: Dict) -> List[str]:
        """Additional security checks based on context"""
        warnings = []
        
        # Check if context contains file paths that might be sensitive
        if 'file_paths' in context:
            for path in context['file_paths']:
                if any(sensitive in path.lower() for sensitive in ['.env', 'config', 'secret', 'key']):
                    warnings.append(f"Potentially sensitive file in context: {path}")
        
        # Check for excessive context size (potential DoS)
        if 'context_size' in context and context['context_size'] > 100000:
            warnings.append("Large context size detected - potential resource exhaustion")
        
        return warnings

# Initialize the MCP server
mcp = FastMCP("Secure Prompt Validator")

# Initialize the security validator
security_validator = PromptSecurityValidator(SecurityLevel.MEDIUM)

@mcp.tool()
async def validate_and_secure_prompt(prompt: str, context: Optional[str] = None) -> Dict:
    """
    Validate and secure a prompt before sending it to the AI model.
    
    Args:
        prompt: The prompt to validate and secure
        context: Optional JSON string containing additional context
    
    Returns:
        Dictionary containing validation results and secured prompt
    """
    try:
        # Parse context if provided
        parsed_context = None
        if context:
            try:
                parsed_context = json.loads(context)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in context parameter")
        
        # Validate the prompt
        result = await security_validator.validate_prompt(prompt, parsed_context)
        
        # Log the security check
        logger.info(f"Security check - Safe: {result.is_safe}, Warnings: {len(result.warnings)}")
        
        return {
            "is_safe": result.is_safe,
            "secured_prompt": result.modified_prompt,
            "original_prompt": prompt,
            "warnings": result.warnings,
            "blocked_patterns": result.blocked_patterns,
            "confidence": result.confidence,
            "modifications_made": prompt != result.modified_prompt
        }
    
    except Exception as e:
        logger.error(f"Error validating prompt: {e}")
        return {
            "is_safe": False,
            "secured_prompt": "",
            "original_prompt": prompt,
            "warnings": [f"Validation error: {str(e)}"],
            "blocked_patterns": ["validation_error"],
            "confidence": 0.0,
            "modifications_made": False
        }

@mcp.tool()
async def update_security_level(level: str) -> Dict:
    """
    Update the security level for prompt validation.
    
    Args:
        level: Security level (low, medium, high)
    
    Returns:
        Dictionary containing the update result
    """
    try:
        new_level = SecurityLevel(level.lower())
        security_validator.security_level = new_level
        logger.info(f"Security level updated to: {new_level.value}")
        
        return {
            "success": True,
            "new_level": new_level.value,
            "message": f"Security level set to {new_level.value}"
        }
    
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid security level: {level}. Valid options: low, medium, high"
        }

@mcp.tool()
async def get_security_stats() -> Dict:
    """
    Get statistics about the security validator configuration.
    
    Returns:
        Dictionary containing security configuration stats
    """
    return {
        "current_security_level": security_validator.security_level.value,
        "pattern_counts": {
            "injection_patterns": len(security_validator.injection_patterns),
            "sensitive_patterns": len(security_validator.sensitive_patterns),
            "malicious_patterns": len(security_validator.malicious_patterns),
            "jailbreak_patterns": len(security_validator.jailbreak_patterns)
        },
        "description": "Secure Prompt Validator MCP Server"
    }

def main():
    """Run the MCP server"""
    logger.info("Starting Secure Prompt MCP Server...")
    mcp.run(transport="http", host="0.0.0.0", port=8000);

if __name__ == "__main__":
    main()