#!/usr/bin/env python3
"""
Quick test to validate the specific API key masking scenario
"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_api_key_scenario():
    """Test the specific API key scenario"""
    
    try:
        from securenlpmcp import EnhancedPromptSecurityValidator, SecurityLevel
        
        print("🧪 Testing API Key Masking Scenario")
        print("=" * 50)
        
        # Initialize validator
        validator = EnhancedPromptSecurityValidator(SecurityLevel.MEDIUM)
        
        # The specific test case
        test_prompt = "this is my api key adawd12123123. can we use this?"
        expected_result = "this is my api [API_KEY_MASKED]. can we use this?"
        
        print(f"Input:    {test_prompt}")
        print(f"Expected: {expected_result}")
        print()
        
        # Run validation
        result = await validator.validate_prompt(test_prompt)
        
        print(f"Actual:   {result.modified_prompt}")
        print()
        
        # Check if it matches expected
        if result.modified_prompt == expected_result:
            print("✅ SUCCESS: Output matches expected result!")
        else:
            print("❌ MISMATCH: Output doesn't match expected result")
            print(f"   Expected: {expected_result}")
            print(f"   Got:      {result.modified_prompt}")
        
        print(f"\nSafe: {result.is_safe}")
        print(f"Confidence: {result.confidence:.2f}")
        
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        if hasattr(result, 'nlp_analysis') and result.nlp_analysis:
            nlp = result.nlp_analysis
            if 'matches' in nlp:
                print(f"\nMatches found: {len(nlp['matches'])}")
                for match in nlp['matches']:
                    print(f"  - {match['label']}: '{match['text']}' (pos: {match['start']}-{match['end']})")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_key_scenario())
