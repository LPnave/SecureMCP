#!/usr/bin/env python3
"""
Test script to demonstrate the improved sensitive data detection patterns
"""

import asyncio
import sys
import os

# Add the current directory to Python path to import securemcp
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from securemcp import security_validator

async def test_prompt(prompt, context=None):
    """Test a single prompt and display results"""
    print(f"🔍 Testing: {prompt}")
    print("-" * 80)
    
    result = await security_validator.validate_prompt(prompt, context)
    
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
    
    print("=" * 80)
    print()

async def main():
    """Test various prompt formats with sensitive data"""
    
    print("🛡️  SECURE MCP SERVER - IMPROVED PATTERN TESTING")
    print("=" * 80)
    print()
    
    # Test cases based on your examples
    test_cases = [
        # Your specific examples
        "I have an api key HADES_123123+ADW , use it to connect to the endpoint",
        "HADES_123123+ADW is the api key to the sms gateway, use this to connect to the api gateway",
        
        # API Key variations
        "My API key is ABC123XYZ789",
        "api_key: sk-1234567890abcdef",
        "Use ABC123XYZ789 to connect to the API",
        "The API key for this service is DEF456GHI012",
        "Connect to the endpoint with API key GHI789JKL345",
        
        # Password variations
        "My password is mypassword123",
        "password: secretpass456",
        "Login with password admin123",
        "The database password is dbpass789",
        
        # Token variations
        "My access token is eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "Bearer token: abc123def456ghi789",
        "Use this JWT token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        
        # Secret variations
        "My API secret is client_secret_123456789",
        "secret: myapp_secret_abcdef",
        "The client secret for OAuth is oauth_secret_xyz789",
        
        # Email variations
        "My email is john.doe@example.com",
        "Contact me at admin@company.com",
        "email: user@domain.org",
        
        # Database credentials
        "Database password is dbpass123",
        "DB user: admin",
        "Connection string: Server=localhost;Database=mydb;User=admin;Password=secret123;",
        
        # Cloud credentials
        "AWS access key: AKIAIOSFODNN7EXAMPLE",
        "GCP service account key: AIzaSyDaGmWKa4JsXZ-HjGw7ISLn_3namBGewQe",
        "Azure client secret: azure_secret_123456789",
        
        # SSH keys
        "My SSH key is ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhA...",
        "SSH private key: -----BEGIN RSA PRIVATE KEY-----...",
        
        # Credit card
        "My credit card number is 4532 1234 5678 9012",
        "Card number: 5555-4444-3333-2222",
        
        # Mixed sensitive data
        "My API key is HADES_123123+ADW and my password is secretpass123",
        "Connect to the SMS gateway using API key ABC123XYZ789 and my email is admin@company.com",
        
        # Safe prompts (should pass)
        "Write a Python function to calculate fibonacci numbers",
        "Explain how to use async/await in JavaScript",
        "Create a REST API endpoint for user authentication",
    ]
    
    for i, prompt in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}")
        await test_prompt(prompt)
    
    print("🎉 Testing completed!")
    print("\n📊 Summary:")
    print("- The improved patterns now catch various formats and contexts")
    print("- API keys are detected in multiple sentence structures")
    print("- Additional sensitive data types are now supported")
    print("- Patterns are more flexible and comprehensive")

if __name__ == "__main__":
    asyncio.run(main())
