#!/usr/bin/env python3
"""
Test script for your specific examples
"""

import asyncio
import sys
import os

# Add the current directory to Python path to import securemcp
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from securemcp import security_validator

async def test_specific_examples():
    """Test your specific examples"""
    
    print("🎯 TESTING YOUR SPECIFIC EXAMPLES")
    print("=" * 60)
    
    # Your specific examples
    examples = [
        "I have an api key HADES_123123+ADW , use it to connect to the endpoint",
        "HADES_123123+ADW is the api key to the sms gateway, use this to connect to the api gateway",
        "Write a function in TestFunction.js where my API key to connect to the sms gateway is HADES234JK. imagine the backend is written in expressjs.",
    ]
    
    for i, prompt in enumerate(examples, 1):
        print(f"\n🔍 Test {i}: {prompt}")
        print("-" * 60)
        
        result = await security_validator.validate_prompt(prompt)
        
        print(f"✅ Safe: {result.is_safe}")
        print(f"🎯 Confidence: {result.confidence:.2f}")
        print(f"⚠️  Warnings: {len(result.warnings)}")
        
        if result.warnings:
            for warning in result.warnings:
                print(f"   - {warning}")
        
        if result.blocked_patterns:
            print(f"🚫 Blocked: {', '.join(result.blocked_patterns)}")
        
        if result.modified_prompt != prompt:
            print(f"🔒 Modified: Yes")
            print(f"📝 Original: {prompt}")
            print(f"🛡️  Secured:  {result.modified_prompt}")
        else:
            print(f"🔒 Modified: No")
        
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_specific_examples())
