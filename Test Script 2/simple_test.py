#!/usr/bin/env python3
"""
Simple test using requests to test the fixed sanitization
"""

import requests
import json

def test_mcp_server():
    """Test MCP server using HTTP requests"""
    
    base_url = "http://localhost:8001/mcp"
    
    # First, let's get the list of tools
    print("🔍 Getting available tools...")
    
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/list"
    }
    
    # Add required headers for MCP protocol
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    try:
        response = requests.post(base_url, json=payload, headers=headers)
        print(f"Tools response status: {response.status_code}")
        
        if response.status_code == 200:
            tools_result = response.json()
            print("✅ Available tools:")
            if 'result' in tools_result and 'tools' in tools_result['result']:
                for tool in tools_result['result']['tools']:
                    print(f"   - {tool['name']}")
        
        # Now test the validation tool
        print("\n🧪 Testing prompt validation...")
        
        validate_payload = {
            "jsonrpc": "2.0", 
            "id": "2",
            "method": "tools/call",
            "params": {
                "name": "validate_and_secure_prompt",
                "arguments": {
                    "prompt": "this is my api key 123123adawdadwaw. can we use it?"
                }
            }
        }
        
        response = requests.post(base_url, json=validate_payload, headers=headers)
        print(f"Validation response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("📋 Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_mcp_server()
