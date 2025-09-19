#!/usr/bin/env python3
"""
Test simple patterns directly
"""

import re

# Simple patterns
patterns = [
    r'(?i)api[_-]?key\s+([A-Z0-9_+\-]{8,})',  # api key HADES_123123+ADW
    r'(?i)([A-Z0-9_+\-]{8,})\s+is\s+(?:the\s+)?api[_-]?key',  # HADES_123123+ADW is the api key
    r'(?i)([A-Z0-9_+\-]{8,})\s+is\s+(?:the\s+)?api[_-]?key\s+to\s+(?:the\s+)?(?:sms\s+)?gateway',  # HADES_123123+ADW is the api key to the sms gateway
]

test_strings = [
    "I have an api key HADES_123123+ADW , use it to connect to the endpoint",
    "HADES_123123+ADW is the api key to the sms gateway, use this to connect to the api gateway",
    "Write a function in TestFunction.js where my API key to connect to the sms gateway is HADES234JK. imagine the backend is written in expressjs.",
]

print("🔍 TESTING SIMPLE PATTERNS")
print("=" * 60)

for i, test_string in enumerate(test_strings, 1):
    print(f"\nTest {i}: {test_string}")
    print("-" * 60)
    
    for j, pattern in enumerate(patterns, 1):
        match = re.search(pattern, test_string, re.IGNORECASE)
        if match:
            print(f"✅ Pattern {j} MATCHED: {match.group(0)}")
            if match.groups():
                print(f"   Captured: {match.group(1)}")
        else:
            print(f"❌ Pattern {j} NO MATCH")
    
    print("=" * 60)

# Test even simpler patterns
print("\n🔧 TESTING EVEN SIMPLER PATTERNS")
print("=" * 60)

simple_patterns = [
    r'([A-Z0-9_+\-]{8,})',  # Just capture any key-like string
    r'(?i)api[_-]?key',  # Just find "api key"
    r'(?i)gateway',  # Just find "gateway"
]

for i, test_string in enumerate(test_strings, 1):
    print(f"\nTest {i}: {test_string}")
    print("-" * 60)
    
    for j, pattern in enumerate(simple_patterns, 1):
        matches = re.findall(pattern, test_string, re.IGNORECASE)
        if matches:
            print(f"✅ Pattern {j} MATCHED: {matches}")
        else:
            print(f"❌ Pattern {j} NO MATCH")
    
    print("=" * 60)
