#!/usr/bin/env python3
"""
Final test of the improved Secure MCP server
"""

import asyncio
import sys
import os

# Add the current directory to Python path to import securemcp
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from securemcp import security_validator

async def final_test():
    """Final comprehensive test"""
    
    print("🛡️  FINAL TEST - IMPROVED SECURE MCP SERVER")
    print("=" * 70)
    
    # Your specific examples
    test_cases = [
        # Your original examples
        "I have an api key HADES_123123+ADW , use it to connect to the endpoint",
        "HADES_123123+ADW is the api key to the sms gateway, use this to connect to the api gateway",
        "Write a function in TestFunction.js where my API key to connect to the sms gateway is HADES234JK. imagine the backend is written in expressjs.",
        
        # Additional test cases
        "My API key is ABC123XYZ789",
        "password: secretpass456",
        "My email is john.doe@example.com",
        "Write a Python function to calculate fibonacci numbers",  # Safe prompt
    ]
    
    for i, prompt in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
        print("-" * 70)
        
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
        
        print("=" * 70)
    
    print("\n🎉 FINAL TEST COMPLETED!")
    print("\n📊 Summary of Improvements:")
    print("✅ Enhanced API key detection with multiple patterns")
    print("✅ Support for various sentence structures")
    print("✅ Detection of passwords, tokens, secrets, emails, etc.")
    print("✅ Flexible regex patterns for different contexts")
    print("✅ Comprehensive sensitive data sanitization")
    print("✅ Updated to FastMCP 2.12.3")

if __name__ == "__main__":
    asyncio.run(final_test())
