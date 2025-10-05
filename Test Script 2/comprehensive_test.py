#!/usr/bin/env python3
"""
Comprehensive test of all credential masking patterns
"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_comprehensive_scenarios():
    """Test comprehensive credential masking scenarios"""
    
    try:
        from securenlpmcp import EnhancedPromptSecurityValidator, SecurityLevel
        
        print("🧪 Comprehensive Credential Masking Test")
        print("=" * 60)
        
        # Initialize validator
        validator = EnhancedPromptSecurityValidator(SecurityLevel.MEDIUM)
        
        test_cases = [
            # Password scenarios
            {"input": "My password is secret123", "description": "Password with 'is'"},
            {"input": "The password secret456", "description": "Password without 'is'"},
            
            # API Key scenarios  
            {"input": "The api key is abc123def456", "description": "API key with 'is'"},
            {"input": "this is my api key adawd12123123", "description": "API key without 'is'"},
            {"input": "My access token xyz789", "description": "Access token"},
            
            # Username scenarios
            {"input": "My username is admin123", "description": "Username with 'is'"},
            {"input": "The username admin456", "description": "Username without 'is'"},
            
            # Email scenarios
            {"input": "My email is test@example.com", "description": "Email with 'is'"},
            {"input": "Contact email user@domain.org", "description": "Email without 'is'"},
            
            # Secret scenarios
            {"input": "The secret is mysecret789", "description": "Secret with 'is'"},
            {"input": "Database secret dbpass123", "description": "Secret without 'is'"},
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['description']}")
            print(f"   Input:  {test_case['input']}")
            
            # Run validation
            result = await validator.validate_prompt(test_case['input'])
            print(f"   Output: {result.modified_prompt}")
            
            # Show if anything was sanitized
            if result.modified_prompt != test_case['input']:
                print("   ✅ SANITIZED")
            else:
                print("   ⚪ NO CHANGE")
            
            if hasattr(result, 'nlp_analysis') and result.nlp_analysis and 'matches' in result.nlp_analysis:
                matches = result.nlp_analysis['matches']
                if matches:
                    print(f"   Matches ({len(matches)}):")
                    for match in matches:
                        print(f"     - {match['label']}: '{match['text']}'")
                        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_comprehensive_scenarios())

