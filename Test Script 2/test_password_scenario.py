#!/usr/bin/env python3
"""
Test the password masking scenario
"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_password_scenario():
    """Test the password masking scenario"""
    
    try:
        from securenlpmcp import EnhancedPromptSecurityValidator, SecurityLevel
        
        print("🧪 Testing Password Masking Scenarios")
        print("=" * 50)
        
        # Initialize validator
        validator = EnhancedPromptSecurityValidator(SecurityLevel.MEDIUM)
        
        test_cases = [
            {
                "input": "My password is secret123",
                "expected": "My password is [PASSWORD_MASKED]",
                "description": "Basic password case"
            },
            {
                "input": "The api key is abc123def456",
                "expected": "The api key is [API_KEY_MASKED]",
                "description": "API key case"
            },
            {
                "input": "My username is admin123",
                "expected": "My username is [USERNAME_MASKED]",
                "description": "Username case"
            },
            {
                "input": "The secret token xyz789token",
                "expected": "The secret is [PASSWORD_MASKED]",
                "description": "Secret case"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['description']}")
            print(f"   Input:    {test_case['input']}")
            print(f"   Expected: {test_case['expected']}")
            
            # Run validation
            result = await validator.validate_prompt(test_case['input'])
            print(f"   Actual:   {result.modified_prompt}")
            
            # Check if it matches expected
            if result.modified_prompt == test_case['expected']:
                print("   ✅ SUCCESS")
            else:
                print("   ❌ MISMATCH")
            
            if hasattr(result, 'nlp_analysis') and result.nlp_analysis and 'matches' in result.nlp_analysis:
                print(f"   Matches: {len(result.nlp_analysis['matches'])}")
                for match in result.nlp_analysis['matches']:
                    print(f"     - {match['label']}: '{match['text']}'")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_password_scenario())

