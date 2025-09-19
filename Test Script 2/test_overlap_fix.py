#!/usr/bin/env python3
"""
Quick test for the overlap resolution fix
"""

import asyncio
import aiohttp
import json

async def test_api_key_sanitization():
    """Test the API key sanitization with overlap resolution"""
    
    test_prompt = "this is my api key 123123adawdadwaw. can we use it?"
    
    print("🧪 Testing Overlap Resolution Fix")
    print("=" * 50)
    print(f"Input: {test_prompt}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"prompt": test_prompt}
            
            async with session.post(
                "http://localhost:8001/mcp/tools/validate_and_secure_prompt", 
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"✅ Safe: {result.get('is_safe')}")
                    print(f"📊 Confidence: {result.get('confidence', 0):.2f}")
                    print(f"🔧 Original: {result.get('original_prompt')}")
                    print(f"🛡️  Secured:  {result.get('secured_prompt')}")
                    print()
                    
                    if result.get('warnings'):
                        print("⚠️  Warnings:")
                        for warning in result['warnings']:
                            print(f"   - {warning}")
                        print()
                    
                    if result.get('nlp_analysis'):
                        nlp = result['nlp_analysis']
                        print(f"🧠 NLP Analysis:")
                        print(f"   - Total matches: {nlp.get('total_matches', 0)}")
                        print(f"   - Injection score: {nlp.get('injection_score', 0):.2f}")
                        print(f"   - Sensitive score: {nlp.get('sensitive_score', 0):.2f}")
                        print()
                        
                        if nlp.get('matches'):
                            print("🎯 Pattern Matches:")
                            for match in nlp['matches']:
                                print(f"   - {match['label']}: '{match['text']}'")
                            print()
                        
                        if nlp.get('sanitization_applied'):
                            print("🔄 Sanitization Applied:")
                            for category, items in nlp['sanitization_applied'].items():
                                print(f"   - {category}: {items}")
                
                else:
                    print(f"❌ Error: HTTP {response.status}")
                    print(await response.text())
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_key_sanitization())
