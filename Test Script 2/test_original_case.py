#!/usr/bin/env python3
"""
Test the original problematic case
"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_original_case():
    """Test the original problematic case"""
    
    try:
        from securenlpmcp import EnhancedPromptSecurityValidator, SecurityLevel
        
        print("🧪 Testing Original Problematic Case")
        print("=" * 50)
        
        # Initialize validator
        validator = EnhancedPromptSecurityValidator(SecurityLevel.MEDIUM)
        
        original_prompt = "My password is secret123 and my username is Lahirun@mitesp.com. can we use these for the integration?"
        
        print(f"Original: {original_prompt}")
        
        # Run validation
        result = await validator.validate_prompt(original_prompt)
        
        print(f"Secured:  {result.modified_prompt}")
        print()
        
        # Check what was sanitized
        print("✅ Analysis:")
        print(f"   Safe: {result.is_safe}")
        print(f"   Confidence: {result.confidence:.2f}")
        
        if result.warnings:
            print("   Warnings:")
            for warning in result.warnings:
                print(f"     - {warning}")
        
        if hasattr(result, 'nlp_analysis') and result.nlp_analysis:
            nlp = result.nlp_analysis
            if 'matches' in nlp and nlp['matches']:
                print(f"   Pattern Matches ({len(nlp['matches'])}):")
                for match in nlp['matches']:
                    print(f"     - {match['label']}: '{match['text']}'")
            
            if 'sanitization_applied' in nlp and nlp['sanitization_applied']:
                print("   Sanitization Applied:")
                for category, items in nlp['sanitization_applied'].items():
                    print(f"     - {category}: {items}")
        
        # Verify email is masked
        if "@" in original_prompt and "@" not in result.modified_prompt:
            print("\n🎉 SUCCESS: Email has been properly masked!")
        elif "@" in original_prompt and "@" in result.modified_prompt:
            print("\n❌ ISSUE: Email is still visible in output!")
        else:
            print("\n⚪ No email detected in input")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_original_case())

