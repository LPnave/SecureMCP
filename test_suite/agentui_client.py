"""
Agent-UI Client for the REST API backend
Handles communication with the agent-ui sanitization API
"""

import httpx
import json
import sys
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from test_suite.config import AGENTUI_URL, REQUEST_TIMEOUT, RETRY_ATTEMPTS, RETRY_DELAY
except ImportError:
    from config import AGENTUI_URL, REQUEST_TIMEOUT, RETRY_ATTEMPTS, RETRY_DELAY


class AgentUIClient:
    """Client for interacting with the agent-ui backend API"""
    
    def __init__(self, base_url: str = AGENTUI_URL):
        self.base_url = base_url
        self.timeout = REQUEST_TIMEOUT
        
    async def sanitize_prompt(self, prompt: str, security_level: str = "medium") -> Dict[str, Any]:
        """
        Sanitize a prompt using the agent-ui backend API
        
        Args:
            prompt: The prompt to sanitize
            security_level: Security level (low, medium, high)
            
        Returns:
            Dictionary with sanitization results
        """
        start_time = datetime.now()
        
        # First, update security level
        await self._update_security_level(security_level)
        
        # Call the sanitize endpoint
        url = f"{self.base_url}/api/sanitize"
        
        payload = {
            "prompt": prompt,
            "context": {}
        }
        
        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    
                    result = response.json()
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Parse the REST API response
                    return self._parse_api_response(result, prompt, execution_time)
                    
            except httpx.TimeoutException:
                if attempt < RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                return self._error_response(prompt, "Request timeout", execution_time=(datetime.now() - start_time).total_seconds() * 1000)
                
            except httpx.HTTPStatusError as e:
                if attempt < RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                return self._error_response(prompt, f"HTTP {e.response.status_code}: {e.response.text}", execution_time=(datetime.now() - start_time).total_seconds() * 1000)
                
            except Exception as e:
                if attempt < RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                return self._error_response(prompt, str(e), execution_time=(datetime.now() - start_time).total_seconds() * 1000)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        return self._error_response(prompt, "Max retries exceeded", execution_time)
    
    async def _update_security_level(self, level: str) -> bool:
        """Update the security level on the agent-ui backend"""
        url = f"{self.base_url}/api/security/level"
        
        payload = {
            "level": level
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.put(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("success", False)
        except Exception as e:
            print(f"Warning: Failed to update security level: {e}")
            return False
    
    def _parse_api_response(self, result: Dict, original_prompt: str, execution_time: float) -> Dict[str, Any]:
        """Parse the REST API response into a standardized format"""
        
        # Extract data from API response
        sanitized_prompt = result.get("sanitized_prompt", original_prompt)
        is_safe = result.get("is_safe", True)
        threats_detected = result.get("blocked_patterns", [])  # Fixed: API returns blocked_patterns, not threats_detected
        confidence = result.get("confidence", 0.0)
        requires_review = result.get("requires_review", False)
        sanitization_applied = result.get("sanitization_applied", {})
        
        # Determine if blocked
        is_blocked = not is_safe or requires_review
        
        # Determine actual behavior
        if is_blocked:
            actual_behavior = "Block"
        elif sanitized_prompt != original_prompt:
            actual_behavior = "Sanitize"
        else:
            actual_behavior = "Allow"
        
        return {
            "success": True,
            "original_prompt": original_prompt,
            "sanitized_prompt": sanitized_prompt,
            "threats_detected": threats_detected if isinstance(threats_detected, list) else [],
            "confidence_score": confidence,
            "is_blocked": is_blocked,
            "execution_time_ms": execution_time,
            "test_status": "Pass",  # Will be determined by results_manager
            "actual_behavior": actual_behavior,
            "error_message": None,
            "sanitization_details": json.dumps(sanitization_applied),
            "requires_review": requires_review
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
            "requires_review": False
        }
    
    async def health_check(self) -> bool:
        """Check if the agent-ui backend is running and responsive"""
        url = f"{self.base_url}/api/health"
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                response.raise_for_status()
                result = response.json()
                return result.get("status") == "healthy"
        except Exception:
            return False

