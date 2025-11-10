"""
MCP Client for zeroshotmcp application
Directly imports and uses the validator since it's Python code
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

# Add zeroshotmcp to path
zeroshotmcp_path = Path(__file__).parent.parent / "zeroshotmcp"
if str(zeroshotmcp_path) not in sys.path:
    sys.path.insert(0, str(zeroshotmcp_path))

try:
    from zeroshot_secure_mcp import ZeroShotSecurityValidator, SecurityLevel
    HAS_ZEROSHOT = True
except ImportError:
    HAS_ZEROSHOT = False
    print("Warning: Could not import zeroshotmcp. Make sure it's in the correct location.")


class MCPClient:
    """Client for interacting with the zeroshotmcp validator"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url  # Not used, kept for compatibility
        if HAS_ZEROSHOT:
            self.validator = ZeroShotSecurityValidator(SecurityLevel.MEDIUM)
        else:
            self.validator = None
        
    async def validate_prompt(self, prompt: str, security_level: str = "medium") -> Dict[str, Any]:
        """
        Validate a prompt using the zeroshotmcp validator directly
        
        Args:
            prompt: The prompt to validate
            security_level: Security level (low, medium, high)
            
        Returns:
            Dictionary with validation results
        """
        start_time = datetime.now()
        
        if not HAS_ZEROSHOT or self.validator is None:
            return self._error_response(prompt, "zeroshotmcp validator not available", 0)
        
        try:
            # Update security level
            await self._update_security_level(security_level)
            
            # Call the validator directly
            result = await self.validator.validate_prompt(prompt, None, None)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Convert to dict format
            result_dict = {
                "is_safe": result.is_safe,
                "secured_prompt": result.modified_prompt,
                "original_prompt": prompt,
                "warnings": result.warnings,
                "blocked_patterns": result.blocked_patterns,
                "confidence": result.confidence,
                "modifications_made": prompt != result.modified_prompt,
                "classifications": result.classifications,
                "sanitization_applied": result.sanitization_applied
            }
            
            return self._parse_mcp_response(result_dict, prompt, execution_time)
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return self._error_response(prompt, f"Validation error: {str(e)}", execution_time)
    
    async def _update_security_level(self, level: str) -> bool:
        """Update the security level on the validator"""
        if not HAS_ZEROSHOT or self.validator is None:
            return False
        
        try:
            level_map = {
                "low": SecurityLevel.LOW,
                "medium": SecurityLevel.MEDIUM,
                "high": SecurityLevel.HIGH
            }
            new_level = level_map.get(level.lower(), SecurityLevel.MEDIUM)
            self.validator.security_level = new_level
            # Reinitialize with new security level
            if hasattr(self.validator, '_configure_security_thresholds'):
                self.validator._configure_security_thresholds()
            return True
        except Exception as e:
            print(f"Warning: Failed to update security level: {e}")
            return False
    
    def _parse_mcp_response(self, result: Dict, original_prompt: str, execution_time: float) -> Dict[str, Any]:
        """Parse the MCP tool response into a standardized format"""
        
        # Extract data from MCP response
        is_safe = result.get("is_safe", True)
        secured_prompt = result.get("secured_prompt", original_prompt)
        warnings = result.get("warnings", [])
        blocked_patterns = result.get("blocked_patterns", [])
        confidence = result.get("confidence", 0.0)
        sanitization_applied = result.get("sanitization_applied", {})
        
        # Determine threats detected
        threats = []
        if blocked_patterns:
            threats.extend(blocked_patterns)
        if warnings:
            # Extract threat types from warnings
            for warning in warnings:
                if "credential" in warning.lower():
                    threats.append("credentials")
                elif "malicious" in warning.lower():
                    threats.append("malicious_code")
                elif "injection" in warning.lower():
                    threats.append("injection")
                elif "jailbreak" in warning.lower():
                    threats.append("jailbreak")
        
        # Determine if blocked (aligned with agentui logic)
        # Consider: explicit safety flag, detected patterns, warnings, or sanitization changes
        requires_review = (
            not is_safe or 
            len(blocked_patterns) > 0 or 
            len(warnings) > 0 or
            secured_prompt != original_prompt
        )
        is_blocked = requires_review
        
        # Determine actual behavior
        if is_blocked:
            actual_behavior = "Block"
        elif secured_prompt != original_prompt:
            actual_behavior = "Sanitize"
        else:
            actual_behavior = "Allow"
        
        return {
            "success": True,
            "original_prompt": original_prompt,
            "sanitized_prompt": secured_prompt,
            "threats_detected": list(set(threats)),
            "confidence_score": confidence,
            "is_blocked": is_blocked,
            "execution_time_ms": execution_time,
            "test_status": "Pass",  # Will be determined by results_manager
            "actual_behavior": actual_behavior,
            "error_message": None,
            "sanitization_details": json.dumps(sanitization_applied),
            "warnings": warnings,
            "blocked_patterns": blocked_patterns
        }
    
    def _error_response(self, original_prompt: str, error_message: str, execution_time: float) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "success": False,
            "original_prompt": original_prompt,
            "sanitized_prompt": original_prompt,
            "threats_detected": [],
            "confidence_score": 0.0,
            "is_blocked": False,
            "execution_time_ms": execution_time,
            "test_status": "Error",
            "actual_behavior": "Error",
            "error_message": error_message,
            "sanitization_details": "{}",
            "warnings": [],
            "blocked_patterns": []
        }
    
    async def health_check(self) -> bool:
        """Check if the validator is available and functioning"""
        if not HAS_ZEROSHOT or self.validator is None:
            return False
        
        try:
            # Try a simple validation to ensure everything is loaded
            test_result = await self.validator.validate_prompt("test", None, None)
            return test_result is not None
        except Exception:
            return False

