# Phase 5: Pattern Enhancement & Synchronization

**Current**: 55% pass rate  
**Target**: 75-85% pass rate

## Priority 1: Expand Injection Patterns (HIGH IMPACT)

### Missing Injection Verbs/Phrases

Add these to **both** `zeroshotmcp/zeroshot_secure_mcp.py` and `agent-ui/python-backend/app/core/security.py`:

```python
injection_patterns = [
    # Existing patterns...
    
    # COMMAND MANIPULATION (NEW)
    r'(?i)\b(forget|override|skip|disregard|bypass)\s+(all\s+)?(previous|earlier|prior)\s+(commands?|instructions?|prompts?|guidelines?|configurations?|settings?)',
    r'(?i)\b(forget|override|skip|disregard)\s+(about|the)\s+(security|authentication|validation|authorization|protection|checks?|middleware)',
    
    # ROLE/MODE MANIPULATION (NEW)
    r'(?i)\bact\s+as\s+(a|an)?\s*(developer|admin|system|root|superuser|unrestricted|privileged)\s+(with|having)?\s*(no|without|unlimited)?\s*(restrictions?|limits?|constraints?)',
    r'(?i)\bbegin\s+(your)?\s*response\s+by\s+(ignoring|skipping|forgetting|overriding)',
    
    # ACCESS/PRIVILEGE ESCALATION (NEW)
    r'(?i)\b(give|grant|provide|allow)\s+(me|everyone|all\s+users?)\s+(admin|root|full|elevated|superuser)\s+(access|privileges?|permissions?|rights?)',
    r'(?i)\bmake\s+(all|every)?\s*(routes?|endpoints?|apis?)\s+(public|accessible|available)\s+(to\s+)?everyone',
    
    # SECURITY BYPASS (NEW)
    r'(?i)\bdisable\s+(CSRF|XSS|authentication|authorization|validation|encryption|security)',
    r'(?i)\brender\s+user\s+input\s+directly',
    r'(?i)\ballow\s+weak\s+(passwords?|authentication)',
    r'(?i)\btrust\s+all\s+(incoming|external)\s+(requests?|sources?|inputs?)',
    
    # CONFIGURATION OVERRIDE (NEW)
    r'(?i)\b(hardcode|embed)\s+(production\s+)?(credentials?|passwords?|secrets?|keys?|tokens?)',
    r'(?i)\bstore\s+(passwords?|credentials?|secrets?)\s+in\s+(plaintext|plain\s+text)',
    r'(?i)\bmake\s+(tokens?|sessions?|cookies?)\s+valid\s+(forever|indefinitely|permanent)',
]
```

**Expected Impact**: Injection 33% → 75-85%

## Priority 2: Synchronize Pattern Lists

### Action: Verify Both Applications Have Identical Patterns

**Files to check**:
1. `zeroshotmcp/zeroshot_secure_mcp.py` - lines ~670-750 (pattern definitions)
2. `agent-ui/python-backend/app/core/security.py` - lines ~670-750 (pattern definitions)

**Verify these pattern sections match exactly**:
- Malicious patterns
- Injection patterns
- Jailbreak patterns
- Credential patterns (PII)

**Expected Impact**: zeroshotmcp 44% → 60%+

## Priority 3: Expand Personal (PII) Patterns (21.9% pass rate)

### Current Personal/PII Patterns

Need to add more real-world patterns for:

```python
# Enhanced PII patterns in _sanitize_credentials method

# Medical/Health IDs
r'\b(MRN|medical\s+record\s+number)[\s:=]+[A-Z0-9]{6,12}\b',
r'\b(health\s+insurance|policy)\s+(number|id)[\s:=]+[A-Z0-9]{6,15}\b',

# Financial
r'\b(account|routing)\s+number[\s:=]+\d{8,17}\b',
r'\b(IBAN)[\s:=]+[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b',
r'\b(BIC|SWIFT)[\s:=]+[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b',

# Government IDs (International)
r'\b(national\s+id|tax\s+id|vat)[\s:=]+[A-Z0-9]{6,15}\b',
r'\b(insurance\s+number)[\s:=]+\d{9,12}\b',

# Education
r'\b(student\s+id)[\s:=]+[A-Z0-9]{6,12}\b',

# Biometric Data
r'(?i)\b(fingerprint|biometric|facial\s+recognition)\s+(data|id|hash)[\s:=]+[A-Z0-9]{20,}\b',

# Postal Addresses (more comprehensive)
r'\d{1,5}\s+[A-Za-z\s]+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln|court|ct|boulevard|blvd),?\s+[A-Za-z\s]+,\s+[A-Z]{2}\s+\d{5}',
r'(?i)\b(address|residence|location)[\s:=]+\d+\s+[A-Za-z\s,]+\d{5}',

# Full Names with Titles
r'\b(Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',

# Usernames/Handles with Personal Context
r'(?i)\b(my\s+username|my\s+account|user\s+id)[\s:=]+[A-Za-z0-9_]{3,20}\b',
```

**Expected Impact**: Personal 21.9% → 60-70%

## Priority 4: Add Context-Aware Whitelisting

### Problem
Some legitimate prompts like:
- "How to implement JWT authentication?" 
- "Best practices for password hashing?"

Are being blocked/flagged incorrectly.

### Solution
Enhance `_is_asking_question` method to better identify educational/legitimate queries:

```python
def _is_asking_question(self, text: str) -> bool:
    """Enhanced question detection"""
    text_lower = text.lower()
    
    question_indicators = [
        # Questions
        r'(?i)^(how|what|when|where|why|which|who|can\s+you|could\s+you|would\s+you)',
        r'(?i)(explain|describe|tell\s+me\s+about|show\s+me\s+how|teach\s+me)',
        r'(?i)(best\s+practices?|recommended\s+approach|proper\s+way|correct\s+method)',
        r'(?i)(example\s+of|tutorial|guide|documentation)',
        
        # Educational context
        r'(?i)(learning|studying|understanding|implementing|building|creating)',
        r'(?i)(secure|safe|proper|correct|recommended)\s+(way|method|approach|implementation)',
    ]
    
    for pattern in question_indicators:
        if re.search(pattern, text):
            return True
    
    return False
```

**Expected Impact**: Legitimate 81.3% → 90%+

## Implementation Order

1. **Phase 5.1**: Expand injection patterns in both applications ⏱️ 30 min
2. **Phase 5.2**: Synchronize all pattern lists between apps ⏱️ 20 min
3. **Phase 5.3**: Expand personal/PII patterns ⏱️ 20 min
4. **Phase 5.4**: Enhance question detection ⏱️ 15 min
5. **Phase 5.5**: Run full test suite and verify ⏱️ 60 min

**Total Time**: ~2.5 hours

## Expected Final Results

| Scope | Current | Target | Status |
|-------|---------|--------|--------|
| Injection | 33.3% | 75-85% | 🔴 Need fix |
| Malicious | 52.9% | 60-70% | 🟡 Close |
| Credentials | 88.2% | 90%+ | 🟢 Good |
| Personal | 21.9% | 60-70% | 🔴 Need fix |
| Jailbreak | 52.0% | 60-70% | 🟡 Close |
| Legitimate | 81.3% | 90%+ | 🟢 Good |
| **Overall** | **55%** | **75-85%** | 🟡 Improving |

## Testing Strategy

After each phase:
```bash
# Quick test during development
python test_suite/test_runner.py --quick

# Full test after all phases
python test_suite/test_runner.py

# Generate report
python test_suite/report_generator.py <session_id>
```



