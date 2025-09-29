#!/usr/bin/env python3
"""
Test script for the authenticated Secure Prompt MCP Server
Tests static token authentication with different permission levels
"""

import asyncio
import requests
import json
import time
import os

# Test configuration
SERVER_URL = "http://localhost:8001"
TEST_TOKENS = {
    "admin": "spv-admin-dev-2024-abc123",
    "user": "spv-user-dev-2024-def456", 
    "basic": "spv-basic-dev-2024-ghi789",
    "invalid": "invalid-token-should-fail"
}

def test_endpoint(endpoint: str, token: str, data: dict = None, expected_status: int = 200) -> dict:
    """Test an endpoint with a specific token"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        if data:
            response = requests.post(f"{SERVER_URL}/{endpoint}", headers=headers, json=data, timeout=10)
        else:
            response = requests.get(f"{SERVER_URL}/{endpoint}", headers=headers, timeout=10)
        
        print(f"📍 {endpoint} | Token: {token[:12]}... | Status: {response.status_code}")
        
        if response.status_code == expected_status:
            result = response.json()
            print(f"   ✅ Success: {result.get('success', 'N/A')}")
            if 'client_info' in result:
                client = result['client_info']
                print(f"   👤 Client: {client.get('client_id', 'Unknown')} | Scopes: {len(client.get('scopes', []))}")
            return result
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            try:
                error_result = response.json()
                print(f"   📝 Error: {error_result.get('error', 'Unknown error')}")
                return error_result
            except:
                print(f"   📝 Raw response: {response.text[:100]}...")
                return {"error": "Failed to parse response"}
    
    except requests.exceptions.RequestException as e:
        print(f"   🔌 Connection error: {e}")
        return {"error": f"Connection failed: {e}"}

def run_authentication_tests():
    """Run comprehensive authentication tests"""
    print("🔐 SECURE PROMPT MCP AUTHENTICATION TESTS")
    print("=" * 60)
    
    # Test 1: Basic prompt validation with different tokens
    print("\n1️⃣ TESTING PROMPT VALIDATION (prompt:validate scope)")
    test_prompt = {
        "prompt": "My password is secret123 and my username is test@example.com",
        "context": '{"source": "test_script"}'
    }
    
    # Admin token (should work)
    print("\n🔑 Admin Token:")
    result = test_endpoint("validate_and_secure_prompt", TEST_TOKENS["admin"], test_prompt)
    if result.get("is_safe") is not None:
        print(f"   🛡️ Safe: {result['is_safe']} | Confidence: {result.get('confidence', 0):.2f}")
        print(f"   🔒 Secured: {result.get('secured_prompt', '')[:50]}...")
    
    # User token (should work)
    print("\n🔑 User Token:")
    result = test_endpoint("validate_and_secure_prompt", TEST_TOKENS["user"], test_prompt)
    if result.get("is_safe") is not None:
        print(f"   🛡️ Safe: {result['is_safe']} | Confidence: {result.get('confidence', 0):.2f}")
    
    # Basic token (should work)
    print("\n🔑 Basic Token:")
    result = test_endpoint("validate_and_secure_prompt", TEST_TOKENS["basic"], test_prompt)
    if result.get("is_safe") is not None:
        print(f"   🛡️ Safe: {result['is_safe']} | Confidence: {result.get('confidence', 0):.2f}")
    
    # Invalid token (should fail)
    print("\n🔑 Invalid Token:")
    test_endpoint("validate_and_secure_prompt", TEST_TOKENS["invalid"], test_prompt, expected_status=401)
    
    # Test 2: Semantic analysis (requires prompt:analyze scope)
    print("\n\n2️⃣ TESTING SEMANTIC ANALYSIS (prompt:analyze scope)")
    semantic_data = {"prompt": "What is the weather like today?"}
    
    # Admin token (should work - has prompt:analyze)
    print("\n🔑 Admin Token:")
    result = test_endpoint("analyze_prompt_semantics", TEST_TOKENS["admin"], semantic_data)
    if result.get("success"):
        analysis = result.get("analysis", {})
        print(f"   📊 Sentences: {analysis.get('sentence_count', 0)} | Words: {analysis.get('word_count', 0)}")
    
    # User token (should work - has prompt:analyze)
    print("\n🔑 User Token:")
    result = test_endpoint("analyze_prompt_semantics", TEST_TOKENS["user"], semantic_data)
    if result.get("success"):
        analysis = result.get("analysis", {})
        print(f"   📊 Sentences: {analysis.get('sentence_count', 0)} | Words: {analysis.get('word_count', 0)}")
    
    # Basic token (should fail - no prompt:analyze scope)
    print("\n🔑 Basic Token (should fail):")
    result = test_endpoint("analyze_prompt_semantics", TEST_TOKENS["basic"], semantic_data)
    if not result.get("success"):
        print(f"   🚫 Expected failure: {result.get('error', 'Unknown error')}")
    
    # Test 3: Security statistics (requires security:stats scope)
    print("\n\n3️⃣ TESTING SECURITY STATS (security:stats scope)")
    
    # Admin token (should work - has security:stats)
    print("\n🔑 Admin Token:")
    result = test_endpoint("get_security_stats", TEST_TOKENS["admin"])
    if result.get("success"):
        patterns = result.get("pattern_counts", {})
        print(f"   📈 Total patterns: {patterns.get('total_nlp_patterns', 0)}")
        print(f"   🔒 Security level: {result.get('current_security_level', 'unknown')}")
    
    # User token (should work - has security:stats)
    print("\n🔑 User Token:")
    result = test_endpoint("get_security_stats", TEST_TOKENS["user"])
    if result.get("success"):
        patterns = result.get("pattern_counts", {})
        print(f"   📈 Total patterns: {patterns.get('total_nlp_patterns', 0)}")
    
    # Basic token (should fail - no security:stats scope)
    print("\n🔑 Basic Token (should fail):")
    result = test_endpoint("get_security_stats", TEST_TOKENS["basic"])
    if not result.get("success"):
        print(f"   🚫 Expected failure: {result.get('error', 'Unknown error')}")
    
    # Test 4: Security level update (requires security:admin scope)
    print("\n\n4️⃣ TESTING SECURITY LEVEL UPDATE (security:admin scope)")
    update_data = {"level": "high"}
    
    # Admin token (should work - has security:admin)
    print("\n🔑 Admin Token:")
    result = test_endpoint("update_security_level", TEST_TOKENS["admin"], update_data)
    if result.get("success"):
        print(f"   ⚙️ Updated to: {result.get('new_level', 'unknown')}")
        print(f"   👤 Updated by: {result.get('updated_by', 'unknown')}")
    
    # User token (should fail - no security:admin scope)
    print("\n🔑 User Token (should fail):")
    result = test_endpoint("update_security_level", TEST_TOKENS["user"], update_data)
    if not result.get("success"):
        print(f"   🚫 Expected failure: {result.get('error', 'Unknown error')}")
    
    # Basic token (should fail - no security:admin scope)
    print("\n🔑 Basic Token (should fail):")
    result = test_endpoint("update_security_level", TEST_TOKENS["basic"], update_data)
    if not result.get("success"):
        print(f"   🚫 Expected failure: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 60)
    print("🎉 AUTHENTICATION TESTS COMPLETED")
    print("=" * 60)

def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        return True
    except:
        return False

def print_usage_instructions():
    """Print usage instructions"""
    print("\n" + "=" * 60)
    print("📋 USAGE INSTRUCTIONS")
    print("=" * 60)
    
    print("\n🚀 To start the authenticated server:")
    print("   export FASTMCP_AUTH_MODE=static")
    print("   python securenlpmcp_with_auth.py")
    
    print("\n🔑 Available test tokens:")
    for name, token in TEST_TOKENS.items():
        if name != "invalid":
            print(f"   {name.upper()}: {token}")
    
    print("\n📝 Example curl commands:")
    print(f'   curl -H "Authorization: Bearer {TEST_TOKENS["admin"]}" \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"prompt": "My password is secret123"}\' \\')
    print(f'        {SERVER_URL}/validate_and_secure_prompt')
    
    print("\n🔍 Scope requirements:")
    print("   validate_and_secure_prompt: prompt:validate")
    print("   analyze_prompt_semantics: prompt:analyze") 
    print("   get_security_stats: security:stats")
    print("   update_security_level: security:admin")

if __name__ == "__main__":
    print("🧪 SECURE PROMPT MCP AUTHENTICATION TEST SUITE")
    print("=" * 60)
    
    # Check if server is running
    print("🔍 Checking server status...")
    if not check_server_status():
        print("❌ Server is not running!")
        print("\n💡 Please start the server first:")
        print("   export FASTMCP_AUTH_MODE=static")
        print("   python securenlpmcp_with_auth.py")
        print("\nThen run this test script again.")
        exit(1)
    
    print("✅ Server is running!")
    
    # Run tests
    try:
        run_authentication_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Test error: {e}")
    
    # Print usage instructions
    print_usage_instructions()
