#!/usr/bin/env python3
"""
Test the email masking issue
"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_email_issue():
    """Test the email masking issue"""
    
    try:
        from securenlpmcp import EnhancedPromptSecurityValidator, SecurityLevel
        
        print("🧪 Testing Email Masking Issue")
        print("=" * 50)
        
        # Initialize validator
        validator = EnhancedPromptSecurityValidator(SecurityLevel.MEDIUM)
        
        test_cases = [
            "My password is secret123 and my username is Lahirun@mitesp.com. can we use these for the integration?",
            "My email is john@example.com please use it",
            "Contact me at test@domain.org for more info",
            "Username: admin@company.com",
            "Login with user@site.net"
        ]
        
        for i, test_prompt in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test_prompt}")
            
            # Run validation
            result = await validator.validate_prompt(test_prompt)
            print(f"   Original: {test_prompt}")
            print(f"   Secured:  {result.modified_prompt}")
            
            # Check for email in original vs secured
            if "@" in test_prompt and "@" in result.modified_prompt:
                print("   ❌ EMAIL NOT MASKED!")
            elif "@" in test_prompt and "@" not in result.modified_prompt:
                print("   ✅ EMAIL PROPERLY MASKED")
            else:
                print("   ⚪ NO EMAIL DETECTED")
            
            if hasattr(result, 'nlp_analysis') and result.nlp_analysis and 'matches' in result.nlp_analysis:
                matches = result.nlp_analysis['matches']
                print(f"   Matches ({len(matches)}):")
                for match in matches:
                    print(f"     - {match['label']}: '{match['text']}'")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_issue())

