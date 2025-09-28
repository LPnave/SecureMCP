#!/usr/bin/env python3
"""
Debug script to test regex patterns directly
"""

import re

# Test patterns
patterns = [
    r'(?i)(?:i\s+have\s+an?\s+)?api[_-]?key\s+([a-zA-Z0-9_+\-]{8,})',  # I have an api key HADES_123123+ADW
    r'(?i)([a-zA-Z0-9_+\-]{8,})\s+(?:is\s+)?(?:the\s+)?api[_-]?key\s+(?:to\s+)?(?:the\s+)?',  # HADES_123123+ADW is the api key
    r'(?i)(?:my\s+)?api[_-]?key\s+(?:to\s+)?(?:connect\s+to\s+)?(?:the\s+)?(?:sms\s+)?gateway\s+(?:is\s+)?([a-zA-Z0-9_+\-]{8,})',  # my API key to connect to the sms gateway is HADES234JK
]

test_strings = [
    "I have an api key HADES_123123+ADW , use it to connect to the endpoint",
    "HADES_123123+ADW is the api key to the sms gateway, use this to connect to the api gateway",
    "Write a function in TestFunction.js where my API key to connect to the sms gateway is HADES234JK. imagine the backend is written in expressjs.",
]

print("🔍 DEBUGGING REGEX PATTERNS")
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

# Test individual components
print("\n🔧 TESTING INDIVIDUAL COMPONENTS")
print("=" * 60)

test_string = "I have an api key HADES_123123+ADW , use it to connect to the endpoint"

# Test the key part
key_pattern = r'([a-zA-Z0-9_+\-]{8,})'
key_match = re.search(key_pattern, test_string)
if key_match:
    print(f"✅ Key pattern matched: {key_match.group(1)}")

# Test the context part
context_pattern = r'(?i)(?:i\s+have\s+an?\s+)?api[_-]?key\s+'
context_match = re.search(context_pattern, test_string)
if context_match:
    print(f"✅ Context pattern matched: '{context_match.group(0)}'")

# Test combined
combined_pattern = r'(?i)(?:i\s+have\s+an?\s+)?api[_-]?key\s+([a-zA-Z0-9_+\-]{8,})'
combined_match = re.search(combined_pattern, test_string)
if combined_match:
    print(f"✅ Combined pattern matched: {combined_match.group(0)}")
    print(f"   Captured key: {combined_match.group(1)}")
else:
    print("❌ Combined pattern failed")
