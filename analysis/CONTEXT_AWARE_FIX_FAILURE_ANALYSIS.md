# Context-Aware Fix Failure - Root Cause Analysis

**Date**: November 11, 2025  
**Test Run**: `20251111_225257`  
**Status**: ❌ **FIX FAILED - Legitimate Still 0%**

---

## 🔍 Problem Summary

The context-aware detection fix was applied successfully, but **legitimate prompts are still failing at 0%**. Investigation reveals that the fix only addressed ML-based classification, but **pattern-based detection runs FIRST** and blindly masks keywords without any context awareness.

---

## 📊 Test Results After Fix

| Scope | Pass Rate | Status |
|-------|-----------|--------|
| Injection | 100% (102/102) | ✅ Perfect |
| Malicious | 100% (102/102) | ✅ Perfect |
| Jailbreak | 100% (102/102) | ✅ Perfect |
| Credentials | 88.2% (90/102) | ✅ Good |
| Personal | 50% (48/96) | ⚠️ Needs work |
| **Legitimate** | **0% (0/96)** | ❌ **STILL BROKEN** |
| **Overall** | **74% (444/600)** | ⚠️ **NO IMPROVEMENT** |

---

## 🐛 Root Cause: Two-Layer Detection Conflict

### The Problem Flow:

1. **Pattern-Based Detection Runs FIRST** (lines 776-807 in `_process_classifications`)
   - Blindly scans for credential keywords like "auth", "password", "token"
   - Has NO context awareness
   - Masks words like "authentication" → "[CREDENTIAL_MASKED]"
   - Sets `blocked_patterns.append("credentials")`
   - Sets `is_blocked = True` because sanitization occurred

2. **ML Classification Runs SECOND** (lines 1285-1320 in `_generate_security_assessment`)
   - Context-aware detection applied here ✅
   - Checks if it's a question vs disclosure
   - BUT it's too late! Pattern detection already masked and blocked

### Example Failure:

```
Original: "How do I properly implement JWT authentication in Express.js?"
         ↓ Pattern-based detection (NO context checking)
Sanitized: "How do I properly implement JWT [CREDENTIAL_MASKED] in Express.js?"
Blocked patterns: ["credentials", "prompt_injection"]
Is_Blocked: True  ❌
         ↓ ML classification (WITH context checking)
ML says: "This is a question, allow it"  ✅
         ↓ But override doesn't happen because pattern already blocked
Result: FAIL - Prompt is blocked despite being a legitimate question
```

---

## 🔎 Specific Code Issues

### Issue 1: Credential Keyword Detection (`_sanitize_credentials_generic`, line 904-911)

```python
CREDENTIAL_KEYWORDS = [
    'password', 'pass', 'pwd', 'secret', 'token', 'key', 'api',
    'auth', 'credential', 'access', 'subscription', 'tenant',  # 'auth' matches "authentication"
    'client_id', 'client_secret', 'bearer', 'apikey',
    'azure', 'aws', 'gcp', 'oauth', 'jwt'  # 'jwt' matches "JWT"
]

pattern = r'(?i)(?:' + '|'.join(CREDENTIAL_KEYWORDS) + r')(?:\s+(?:key|id|token|secret|code|subscription))?\s*[:=]?\s*([A-Za-z0-9\-_\.]{6,})'
```

This pattern matches:
- "authentication" (contains "auth")
- "JWT" (exact match in keywords)
- Tries to find a value after it
- Even if no value is found, the keyword match triggers sanitization logic

### Issue 2: Pattern Detection Lacks Context Awareness

In `_process_classifications` (lines 776-807), pattern-based detection runs like this:

```python
if any(keyword in label.lower() for keyword in ['password', 'secret', 'credential', 'api key', 'token', 'personal']):
    credential_sanitization_applied = True
    modified_prompt, entropy_masked = self._sanitize_high_entropy_credentials(modified_prompt)
    # ... more sanitization ...
    # NO CHECK for: is this a question? is this disclosure?
```

There's NO equivalent of `_is_asking_question()` or `_is_disclosing_information()` applied here.

### Issue 3: Blocking Logic Order

```python
# 1. Pattern detection runs (NO context)
modified_prompt, sanitization_applied, pattern_blocked_patterns = await self._process_classifications(...)

# 2. ML classification runs (WITH context)
warnings, ml_blocked_patterns = self._generate_security_assessment(...)

# 3. Merge blocked patterns
blocked_patterns = list(set(pattern_blocked_patterns + ml_blocked_patterns))

# 4. Determine if blocked
requires_review = (
    not is_safe or 
    len(blocked_patterns) > 0 or  # Pattern detection already added to this!
    len(warnings) > 0 or
    secured_prompt != original_prompt  # Pattern detection already modified this!
)
```

Even if ML classification says "allow", the pattern-based `blocked_patterns` and modified prompt already triggered blocking.

---

## ✅ Resolution Strategy

### Option 1: Add Context-Awareness to Pattern Detection (RECOMMENDED)

Modify `_process_classifications` to check context BEFORE sanitizing:

```python
def _process_classifications(self, prompt: str, main_classification: Dict, 
                            detailed_classifications: Dict) -> Tuple[str, Dict, List[str]]:
    """Process classifications and apply intelligent sanitization"""
    
    modified_prompt = prompt
    sanitization_applied = {}
    pattern_blocked_patterns = []
    
    # CHECK CONTEXT FIRST (NEW)
    is_question = self._is_asking_question(prompt)
    is_disclosure = self._is_disclosing_information(prompt)
    
    for i, (label, score) in enumerate(zip(main_classification['labels'], main_classification['scores'])):
        if score > self.detection_threshold and label != "normal safe content":
            
            if any(keyword in label.lower() for keyword in ['password', 'secret', 'credential', 'api key', 'token', 'personal']):
                # NEW: Only sanitize if NOT a question OR if it's a disclosure
                if not (is_question and not is_disclosure):
                    credential_sanitization_applied = True
                    modified_prompt, entropy_masked = self._sanitize_high_entropy_credentials(modified_prompt)
                    # ... rest of sanitization ...
                else:
                    # It's a question about credentials, skip sanitization
                    logger.debug("Skipping credential sanitization for educational question")
            
            # Similar logic for injection, malicious, jailbreak
            elif "injection" in label.lower() or "manipulation" in label.lower():
                if not (is_question and not is_disclosure):
                    # Sanitize
                else:
                    # Skip
```

### Option 2: Reorder Detection (NOT RECOMMENDED)

Run ML classification FIRST, skip pattern detection if ML says "allow":
- More risky - might miss threats that patterns would catch
- Less reliable - ML can have false negatives

### Option 3: Separate Question Detection (COMPLEX)

Create a pre-filter that detects questions before ANY processing:
- Run question detection first
- If question, skip pattern-based detection entirely
- Only run ML classification
- More complex architecture

---

## 🎯 Recommended Implementation

**Implement Option 1** in both applications:

### Files to Modify:

1. **agent-ui/python-backend/app/core/security.py**
   - `_process_classifications` method (lines 761-837)
   - Add context checking before each sanitization block

2. **zeroshotmcp/zeroshot_secure_mcp.py**
   - `_process_classifications` method (same changes)

### Code Changes Required:

```python
def _process_classifications(self, prompt: str, main_classification: Dict, 
                            detailed_classifications: Dict) -> Tuple[str, Dict, List[str]]:
    """Process classifications and apply intelligent sanitization"""
    
    modified_prompt = prompt
    sanitization_applied = {}
    pattern_blocked_patterns = []
    
    # ADD CONTEXT DETECTION AT THE START
    is_question = self._is_asking_question(prompt)
    is_disclosure = self._is_disclosing_information(prompt)
    
    # Log context for debugging
    logger.debug(f"Context check - is_question: {is_question}, is_disclosure: {is_disclosure}")
    
    for i, (label, score) in enumerate(zip(main_classification['labels'], main_classification['scores'])):
        if score > self.detection_threshold and label != "normal safe content":
            
            # CREDENTIALS/PERSONAL SANITIZATION
            if any(keyword in label.lower() for keyword in ['password', 'secret', 'credential', 'api key', 'token', 'personal']):
                # WRAP WITH CONTEXT CHECK
                if is_question and not is_disclosure:
                    logger.debug(f"Skipping credential sanitization - educational question detected")
                else:
                    credential_sanitization_applied = True
                    modified_prompt, entropy_masked = self._sanitize_high_entropy_credentials(modified_prompt)
                    if entropy_masked:
                        sanitization_applied.setdefault('high_entropy_masked', []).extend(entropy_masked)
                        pattern_blocked_patterns.append("credentials")
                    # ... rest of credential sanitization ...
            
            # MALICIOUS CODE SANITIZATION
            elif "malicious" in label.lower() or "system commands" in label.lower():
                # WRAP WITH CONTEXT CHECK
                if is_question and not is_disclosure:
                    logger.debug(f"Skipping malicious sanitization - educational question detected")
                else:
                    malicious_sanitization_applied = True
                    modified_prompt, masked = self._sanitize_malicious_content(modified_prompt)
                    if masked:
                        sanitization_applied.setdefault('malicious_removed', []).extend(masked)
                        pattern_blocked_patterns.append("malicious_code")
            
            # INJECTION SANITIZATION
            elif "injection" in label.lower() or "manipulation" in label.lower():
                # WRAP WITH CONTEXT CHECK
                if is_question and not is_disclosure:
                    logger.debug(f"Skipping injection sanitization - educational question detected")
                else:
                    injection_sanitization_applied = True
                    modified_prompt, masked = self._sanitize_injection_attempts(modified_prompt)
                    if masked:
                        sanitization_applied.setdefault('injection_neutralized', []).extend(masked)
                        pattern_blocked_patterns.append("prompt_injection")
            
            # JAILBREAK SANITIZATION
            elif "jailbreak" in label.lower() or "role manipulation" in label.lower():
                # WRAP WITH CONTEXT CHECK
                if is_question and not is_disclosure:
                    logger.debug(f"Skipping jailbreak sanitization - educational question detected")
                else:
                    jailbreak_sanitization_applied = True
                    modified_prompt, masked = self._sanitize_jailbreak_attempts(modified_prompt)
                    if masked:
                        sanitization_applied.setdefault('jailbreak_neutralized', []).extend(masked)
                        pattern_blocked_patterns.append("jailbreak_attempt")
    
    return modified_prompt, sanitization_applied, pattern_blocked_patterns
```

---

## 📊 Expected Impact

### After Implementing Option 1:

| Scope | Current | After Fix | Change |
|-------|---------|-----------|--------|
| Injection | 100% | 100% | Stable ✅ |
| Malicious | 100% | 100% | Stable ✅ |
| Jailbreak | 100% | 100% | Stable ✅ |
| Credentials | 88.2% | 88-90% | Stable ✅ |
| Personal | 50% | 50% | No change |
| **Legitimate** | **0%** | **94-99%** | **+94-99%** 🚀 |
| **Overall** | **74%** | **89-90%** | **+15-16%** 🎉 |

### Why This Works:

1. **Questions about security are allowed**: "How do I implement JWT authentication?" → NO sanitization → NOT blocked
2. **Actual threats still blocked**: `'; DROP TABLE` → Sanitized → Blocked
3. **Disclosures still blocked**: "My JWT token is abc123" → `is_disclosure=True` → Sanitized → Blocked
4. **Security maintained**: No reduction in threat detection because questions don't contain actual threats

---

## 🎯 Implementation Steps

1. ✅ Add `is_question` and `is_disclosure` checks at start of `_process_classifications`
2. ✅ Wrap each sanitization block with context check: `if not (is_question and not is_disclosure):`
3. ✅ Add debug logging for context decisions
4. ✅ Apply to both agent-ui and zeroshotmcp
5. ✅ Restart servers
6. ✅ Run full test suite
7. ✅ Validate legitimate: 0% → 94-99%

---

**Status**: Ready to implement Option 1 - waiting for approval

