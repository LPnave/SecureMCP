#!/usr/bin/env python3
"""
Zero-Shot Secure Prompt MCP Server
A standalone Model Context Protocol server that uses zero-shot classification
to detect sensitive content, prompt injections, and security threats without
relying on predefined patterns.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_access_token
from transformers import pipeline
import torch
import spacy
from spacy.matcher import Matcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class ZeroShotResult:
    is_safe: bool
    modified_prompt: str
    warnings: List[str]
    blocked_patterns: List[str]
    confidence: float
    classifications: Dict[str, Dict]
    sanitization_applied: Dict[str, List[str]]

class ZeroShotSecurityValidator:
    """Zero-shot security validator using transformer models"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        self.security_level = security_level
        self._configure_security_thresholds()
        self.setup_models()
        self.setup_classification_categories()
        self.setup_spacy_matcher()
    
    def _configure_security_thresholds(self):
        """Configure detection and blocking thresholds based on security level"""
        if self.security_level == SecurityLevel.LOW:
            self.detection_threshold = 0.7
            self.blocking_threshold = 0.95
            self.entropy_threshold = 4.2
            self.credential_fallback_threshold = 0.25
        elif self.security_level == SecurityLevel.MEDIUM:
            self.detection_threshold = 0.6
            self.blocking_threshold = 0.8
            self.entropy_threshold = 3.5
            self.credential_fallback_threshold = 0.15
        else:  # HIGH
            self.detection_threshold = 0.4
            self.blocking_threshold = 0.6
            self.entropy_threshold = 3.0
            self.credential_fallback_threshold = 0.1

    def setup_spacy_matcher(self):
        """Initialize spaCy matcher for supplemental pattern recognition"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError("spaCy model 'en_core_web_sm' not found. Please install with: python -m spacy download en_core_web_sm")

        self.matcher = Matcher(self.nlp.vocab)

        connector_tokens = {"is", "was", "equals"}

        password_patterns = [
            [{"LOWER": {"IN": ["this", "the"]}, "OP": "?"},
             {"LOWER": {"IN": ["is"]}, "OP": "?"},
             {"LOWER": {"IN": ["my", "the"]}, "OP": "?"},
             {"LOWER": {"IN": ["password", "pass", "pwd"]}},
             {"TEXT": {"IN": ["=", ":"]}, "OP": "?"},
             {"LOWER": {"IN": list(connector_tokens)}, "OP": "?"},
             {"IS_PUNCT": True, "OP": "*"},
             {"TEXT": {"REGEX": r"(?i)[a-z0-9@#$%^&*_\\-]{4,}"}}],
            [{"LOWER": {"IN": ["password", "pass", "pwd"]}},
             {"TEXT": {"IN": ["=", ":"]}, "OP": "?"},
             {"LOWER": {"IN": list(connector_tokens)}, "OP": "?"},
             {"IS_PUNCT": True, "OP": "*"},
             {"TEXT": {"REGEX": r"(?i)[a-z0-9@#$%^&*_\\-]{4,}"}}]
        ]

        api_patterns = [
            [{"LOWER": {"IN": ["this", "the"]}, "OP": "?"},
             {"LOWER": {"IN": ["is"]}, "OP": "?"},
             {"LOWER": {"IN": ["my", "the"]}, "OP": "?"},
             {"LOWER": "api"},
             {"LOWER": {"IN": ["key", "token"]}},
             {"TEXT": {"IN": ["=", ":"]}, "OP": "?"},
             {"LOWER": {"IN": list(connector_tokens)}, "OP": "?"},
             {"IS_PUNCT": True, "OP": "*"},
             {"TEXT": {"REGEX": r"(?i)[a-z0-9_\\-]{6,}"}}],
            [{"LOWER": "api"},
             {"LOWER": {"IN": ["key", "token"]}},
             {"TEXT": {"IN": ["=", ":"]}, "OP": "?"},
             {"LOWER": {"IN": list(connector_tokens)}, "OP": "?"},
             {"IS_PUNCT": True, "OP": "*"},
             {"TEXT": {"REGEX": r"(?i)[a-z0-9_\\-]{6,}"}}],
            [{"LOWER": {"IN": ["token", "secret"]}},
             {"TEXT": {"IN": ["=", ":"]}, "OP": "?"},
             {"LOWER": {"IN": list(connector_tokens)}, "OP": "?"},
             {"IS_PUNCT": True, "OP": "*"},
             {"TEXT": {"REGEX": r"(?i)[a-z0-9_\\-]{6,}"}}]
        ]

        email_patterns = [
            [{"LIKE_EMAIL": True}],
            [{"LOWER": {"IN": ["this", "the", "my"]}, "OP": "?"},
             {"LOWER": {"IN": ["email", "mail"]}},
             {"LOWER": {"IN": list(connector_tokens)}, "OP": "?"},
             {"LIKE_EMAIL": True}]
        ]

        for idx, pattern in enumerate(password_patterns):
            self.matcher.add(f"PASSWORD_{idx}", [pattern])
        for idx, pattern in enumerate(api_patterns):
            self.matcher.add(f"API_{idx}", [pattern])
        for idx, pattern in enumerate(email_patterns):
            self.matcher.add(f"EMAIL_{idx}", [pattern])

    def _detect_spacy_patterns(self, text: str) -> Dict[str, List[str]]:
        """Detect sensitive patterns using spaCy matcher"""
        if not text:
            return {"password": [], "api_key": [], "email": []}

        doc = self.nlp(text)
        matches = self.matcher(doc)
        detections = {"password": [], "api_key": [], "email": []}
        seen_spans = set()

        for match_id, start, end in matches:
            span = doc[start:end]
            span_key = (span.start_char, span.end_char)
            if span_key in seen_spans:
                continue
            seen_spans.add(span_key)

            label = self.nlp.vocab.strings[match_id]
            if label.startswith("PASSWORD"):
                detections["password"].append(span.text)
            elif label.startswith("API"):
                detections["api_key"].append(span.text)
            elif label.startswith("EMAIL"):
                detections["email"].append(span.text)

        return detections

    def _apply_spacy_sanitization(self, text: str, detections: Dict[str, List[str]]) -> Tuple[str, Dict[str, List[str]]]:
        """Apply sanitization based on spaCy pattern detections"""
        updated_text = text
        sanitization_info: Dict[str, List[str]] = {}

        if detections.get("password"):
            updated_text, masked = self._sanitize_credentials(updated_text, "password")
            if masked:
                sanitization_info.setdefault("passwords_masked", []).extend(masked)

        if detections.get("api_key"):
            updated_text, masked = self._sanitize_credentials(updated_text, "api_key")
            if masked:
                sanitization_info.setdefault("api_keys_masked", []).extend(masked)

        if detections.get("email"):
            updated_text, masked = self._sanitize_credentials(updated_text, "personal")
            if masked:
                sanitization_info.setdefault("personal_info_masked", []).extend(masked)

        return updated_text, sanitization_info

    def _merge_sanitization_records(self, base: Dict[str, List[str]], additions: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Merge sanitization dictionaries without duplicating entries"""
        if not additions:
            return base

        merged: Dict[str, List[str]] = {key: list(values) for key, values in base.items()}
        for key, values in additions.items():
            merged.setdefault(key, [])
            for value in values:
                if value and value not in merged[key]:
                    merged[key].append(value)

        return merged
    
    def setup_models(self):
        """Initialize zero-shot classification models"""
        try:
            # Use a robust zero-shot model
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("Zero-shot classification model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load zero-shot model: {e}")
            # Fallback to a smaller model
            try:
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="typeform/distilbert-base-uncased-mnli",
                    device=-1
                )
                logger.info("Fallback zero-shot model loaded successfully")
            except Exception as e2:
                logger.error(f"Failed to load fallback model: {e2}")
                raise
    
    def setup_classification_categories(self):
        """Define categories for zero-shot classification"""
        
        # Main security categories - MORE SPECIFIC
        self.security_categories = [
            "contains password or secret credentials",
            "contains API key, access token, or authentication credential",
            "contains cloud subscription ID, tenant ID, or service credential",  # NEW - MORE SPECIFIC
            "contains personal information or email address",
            "contains malicious code or system commands",
            "attempts prompt injection or instruction manipulation",
            "attempts jailbreak or role manipulation",
            "contains urgent or manipulative language",
            "requests system access or file operations",
            "contains database credentials or connection strings",
            "normal safe content"
        ]
        
        # Sub-categories for detailed analysis
        self.detailed_categories = {
            "credentials": [
                "password field with actual password value",
                "API key with actual key value",
                "secret token with actual token value",
                "username with actual username value",
                "email address with actual email value"
            ],
            "injection": [
                "ignore previous instructions",
                "forget all previous commands",
                "override system settings",
                "act as different role or character",
                "pretend to be someone else",
                "simulate different behavior"
            ],
            "malicious": [
                "delete files or directories",
                "execute system commands",
                "run malicious scripts",
                "access restricted files",
                "modify system settings",
                "download and execute code"
            ],
            "jailbreak": [
                "hypothetical scenario to bypass rules",
                "urgent request to ignore safety",
                "emotional manipulation attempt",
                "authority claim to override guidelines",
                "emergency situation to bypass restrictions"
            ]
        }
    
    async def validate_prompt(self, prompt: str, context: Optional[Dict] = None, ctx=None) -> ZeroShotResult:
        """Validate prompt using zero-shot classification"""
        
        if ctx:
            await ctx.debug("Starting zero-shot security validation")
            await ctx.info(f"Processing prompt of length {len(prompt)} characters")
        
        warnings = []
        blocked_patterns = []
        modified_prompt = prompt
        confidence = 1.0
        classifications = {}
        sanitization_applied = {}
        
        # Main security classification
        if ctx:
            await ctx.debug("Running main security classification")
        
        main_classification = self._classify_security_threats(prompt)
        classifications['main'] = main_classification
        
        # Detailed classification for each detected threat type
        detailed_classifications = {}
        for category, score in zip(main_classification['labels'], main_classification['scores']):
            # Use configured detection threshold
            if score > self.detection_threshold and category != "normal safe content":
                if ctx:
                    await ctx.debug(f"Detailed analysis for: {category}")
                
                detailed_result = self._detailed_classification(prompt, category)
                detailed_classifications[category] = detailed_result
        
        classifications['detailed'] = detailed_classifications
        
        # Process results and determine actions
        if ctx:
            await ctx.info(f"Found {len([s for s in main_classification['scores'] if s > 0.6])} potential security issues")
        
        # Supplemental spaCy pattern detection
        spacy_detections = self._detect_spacy_patterns(prompt)
        spacy_sanitization = {}
        if any(spacy_detections.values()):
            if ctx:
                await ctx.debug("spaCy matcher detected sensitive patterns; applying additional sanitization")
            sanitized_text, spacy_sanitization = self._apply_spacy_sanitization(modified_prompt, spacy_detections)
            if sanitized_text != modified_prompt:
                modified_prompt = sanitized_text

        # Apply security logic based on classifications
        modified_prompt, sanitization_applied, pattern_blocked_patterns = await self._process_classifications(
            modified_prompt, main_classification, detailed_classifications, ctx
        )
        
        sanitization_applied = self._merge_sanitization_records(sanitization_applied, spacy_sanitization)

        # Generate warnings and blocked patterns from ML
        warnings, ml_blocked_patterns = self._generate_security_assessment(
            main_classification, detailed_classifications
        )
        
        # Merge pattern-based and ML-based threats
        blocked_patterns = list(set(pattern_blocked_patterns + ml_blocked_patterns))
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(main_classification, detailed_classifications)
        
        # Determine if prompt is safe
        is_safe = len(blocked_patterns) == 0
        
        if ctx:
            await ctx.info(f"Final assessment - Safe: {is_safe}, Confidence: {confidence:.2f}")
        
        return ZeroShotResult(
            is_safe=is_safe,
            modified_prompt=modified_prompt,
            warnings=warnings,
            blocked_patterns=blocked_patterns,
            confidence=confidence,
            classifications=classifications,
            sanitization_applied=sanitization_applied
        )
    
    def _is_asking_question(self, text: str) -> bool:
        """Detect if text is asking a question rather than disclosing information"""
        import re
        
        question_indicators = [
            r'(?i)^(how|what|why|when|where|which|who|can|could|should|would|is|are|does)\b',
            r'(?i)\b(how\s+do\s+I|how\s+to|how\s+can|what\'?s\s+the\s+best|what\s+is)',
            r'(?i)\b(explain|describe|tell\s+me\s+about|help\s+me\s+understand)',
            r'(?i)\b(best\s+practice|recommended\s+way|proper\s+method)',
            r'(?i)\b(should\s+I|can\s+I|is\s+it\s+safe|is\s+it\s+okay)',
            r'\?',  # Contains question mark
        ]
        
        for pattern in question_indicators:
            if re.search(pattern, text):
                return True
        return False
    
    def _is_disclosing_information(self, text: str) -> bool:
        """Detect if text is sharing/disclosing sensitive information"""
        import re
        
        disclosure_indicators = [
            r'(?i)\b(my|the|here\'?s|this\s+is)\s+(password|key|token|secret|credential)',
            r'(?i)(password|key|token|secret)\s+(is|:)',
            r'(?i)\b(username|user|login)\s+(is|:)',
            r'(?i)\buse\s+(this|these)\s+(password|key|token|credential)',
        ]
        
        for pattern in disclosure_indicators:
            if re.search(pattern, text):
                return True
        return False
    
    def _classify_security_threats(self, text: str) -> Dict:
        """Classify text for main security threats"""
        try:
            result = self.classifier(text, self.security_categories)
            return {
                'labels': result['labels'],
                'scores': result['scores'],
                'sequence': result['sequence']
            }
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                'labels': ['normal safe content'],
                'scores': [1.0],
                'sequence': text
            }
    
    def _detailed_classification(self, text: str, threat_type: str) -> Dict:
        """Perform detailed classification for specific threat types"""
        
        # Map threat types to detailed categories
        category_mapping = {
            "contains password or secret credentials": "credentials",
            "contains API key or authentication token": "credentials", 
            "contains personal information or email address": "credentials",
            "contains malicious code or system commands": "malicious",
            "attempts prompt injection or instruction manipulation": "injection",
            "attempts jailbreak or role manipulation": "jailbreak",
            "contains urgent or manipulative language": "jailbreak",
            "requests system access or file operations": "malicious"
        }
        
        detailed_category = category_mapping.get(threat_type, "credentials")
        sub_categories = self.detailed_categories.get(detailed_category, [])
        
        if not sub_categories:
            return {'labels': [], 'scores': [], 'sequence': text}
        
        try:
            result = self.classifier(text, sub_categories)
            return {
                'labels': result['labels'],
                'scores': result['scores'],
                'sequence': result['sequence'],
                'category': detailed_category
            }
        except Exception as e:
            logger.error(f"Detailed classification error: {e}")
            return {'labels': [], 'scores': [], 'sequence': text, 'category': detailed_category}
    
    async def _process_classifications(self, prompt: str, main_classification: Dict, 
                                     detailed_classifications: Dict, ctx=None) -> Tuple[str, Dict, List[str]]:
        """Process classifications and apply intelligent sanitization"""
        
        modified_prompt = prompt
        sanitization_applied = {}
        pattern_blocked_patterns = []  # Track pattern-based threat detection
        
        # Track if we applied credential sanitization
        credential_sanitization_applied = False
        
        # Process each high-confidence threat detected by zero-shot
        for i, (label, score) in enumerate(zip(main_classification['labels'], main_classification['scores'])):
            if score > 0.5 and label != "normal safe content":
                
                if ctx:
                    await ctx.debug(f"Zero-shot detected threat: {label} (confidence: {score:.2f})")
            
                # CREDENTIALS/SENSITIVE DATA: Use entropy + keyword backup
                if any(keyword in label.lower() for keyword in ['password', 'secret', 'credential', 'api key', 'token', 'personal']):
                    credential_sanitization_applied = True
                    if ctx:
                        await ctx.info(f"Applying entropy-based sanitization for: {label}")
                    
                    # Step 2: Primary - Entropy-based detection
                    modified_prompt, entropy_masked = self._sanitize_high_entropy_credentials(modified_prompt)
                    if entropy_masked:
                        sanitization_applied.setdefault('entropy_masked_credentials', []).extend(entropy_masked)
                        if 'credentials' not in pattern_blocked_patterns:
                            pattern_blocked_patterns.append('credentials')
                        if ctx:
                            await ctx.debug(f"Entropy detected and masked {len(entropy_masked)} credentials")
                    
                    # Step 3: Backup - Generic keyword matching (catches what entropy missed)
                    modified_prompt, keyword_masked = self._sanitize_credentials_generic(modified_prompt)
                    if keyword_masked:
                        sanitization_applied.setdefault('keyword_masked_credentials', []).extend(keyword_masked)
                        if 'credentials' not in pattern_blocked_patterns:
                            pattern_blocked_patterns.append('credentials')
                        if ctx:
                            await ctx.debug(f"Keyword matching caught {len(keyword_masked)} additional items")
                
                # MALICIOUS CODE: Use pattern matching
                elif "malicious code" in label.lower() or "system commands" in label.lower():
                    modified_prompt, masked = self._sanitize_malicious_content(modified_prompt)
                    if masked:
                        sanitization_applied.setdefault('malicious_removed', []).extend(masked)
                        pattern_blocked_patterns.append('malicious_code')
                
                # INJECTION: Use pattern matching
                elif "injection" in label.lower() or "instruction manipulation" in label.lower():
                    modified_prompt, masked = self._sanitize_injection_attempts(modified_prompt)
                    if masked:
                        sanitization_applied.setdefault('injection_neutralized', []).extend(masked)
                        pattern_blocked_patterns.append('prompt_injection')
                
                # JAILBREAK: Use pattern matching
                elif "jailbreak" in label.lower() or "role manipulation" in label.lower():
                    modified_prompt, masked = self._sanitize_jailbreak_attempts(modified_prompt)
                    if masked:
                        sanitization_applied.setdefault('jailbreak_neutralized', []).extend(masked)
                        pattern_blocked_patterns.append('jailbreak_attempt')
        
        # FALLBACK: If zero-shot had ANY suspicion about credentials (score > 0.15), run sanitization anyway
        if not credential_sanitization_applied:
            credential_labels = [label for label, score in zip(main_classification['labels'], main_classification['scores']) 
                               if score > 0.15 and any(kw in label.lower() for kw in ['password', 'secret', 'credential', 'api', 'token', 'database'])]
            
            if credential_labels:
                if ctx:
                    await ctx.info(f"Fallback: Running sanitization due to medium confidence in credential-related categories")
                
                # Run both entropy and keyword detection
                modified_prompt, entropy_masked = self._sanitize_high_entropy_credentials(modified_prompt)
                if entropy_masked:
                    sanitization_applied.setdefault('entropy_masked_credentials', []).extend(entropy_masked)
                    if 'credentials' not in pattern_blocked_patterns:
                        pattern_blocked_patterns.append('credentials')
                
                modified_prompt, keyword_masked = self._sanitize_credentials_generic(modified_prompt)
                if keyword_masked:
                    sanitization_applied.setdefault('keyword_masked_credentials', []).extend(keyword_masked)
                    if 'credentials' not in pattern_blocked_patterns:
                        pattern_blocked_patterns.append('credentials')
        
        return modified_prompt, sanitization_applied, pattern_blocked_patterns

    def _sanitize_high_entropy_credentials(self, text: str) -> Tuple[str, List[str]]:
        """Primary sanitization: Detect and mask high-entropy strings"""
        import re
        
        modified_text = text
        masked_items = []
        
        # Find potential credentials by entropy
        candidates = re.finditer(r'\b([A-Za-z0-9\-_\.]{8,})\b', text)
        
        for match in candidates:
            value = match.group(1)
            entropy = self._calculate_entropy(value)
            
            # High entropy indicates randomness
            if entropy >= 3.5:
                has_upper = any(c.isupper() for c in value)
                has_lower = any(c.islower() for c in value)
                has_digit = any(c.isdigit() for c in value)
                
                # Check if it's in credential context
                context_start = max(0, match.start() - 30)
                context = text[context_start:match.start()].lower()
                
                credential_indicators = [
                    'key', 'token', 'secret', 'password', 'credential',
                    'auth', 'api', 'subscription', 'tenant', 'client',
                    'azure', 'aws', 'gcp', 'access', 'bearer'
                ]
                
                in_credential_context = any(word in context for word in credential_indicators)
                
                # Mask if: (mixed case + digit) OR (high entropy + context)
                should_mask = (
                    (has_upper and has_lower and has_digit) or 
                    (entropy >= 4.0 and in_credential_context) or
                    (entropy >= 3.8 and in_credential_context)
                )
                
                if should_mask:
                    # Skip common words
                    if value.lower() not in ['example', 'localhost', 'password', 'username', 'integration']:
                        masked_items.append(value)
        
        # Apply masking in reverse order to preserve indices
        for value in reversed(masked_items):
            # Find all occurrences and replace
            pattern = re.escape(value)
            modified_text = re.sub(pattern, '[CREDENTIAL_MASKED]', modified_text)
        
        return modified_text, masked_items

    def _sanitize_credentials_generic(self, text: str) -> Tuple[str, List[str]]:
        """Backup sanitization: Keyword-based credential detection"""
        import re
        
        masked_items = []
        modified_text = text
        
        # Broad credential keywords
        CREDENTIAL_KEYWORDS = [
            'password', 'pass', 'pwd', 'secret', 'token', 'key', 'api',
            'auth', 'credential', 'access', 'subscription', 'tenant',
            'client_id', 'client_secret', 'bearer', 'apikey',
            'azure', 'aws', 'gcp', 'oauth', 'jwt'
        ]
        
        # Pattern: keyword + optional descriptor + value
        pattern = r'(?i)(?:' + '|'.join(CREDENTIAL_KEYWORDS) + r')(?:\s+(?:key|id|token|secret|code|subscription))?\s*[:=]?\s*([A-Za-z0-9\-_\.]{6,})'
        
        matches = re.finditer(pattern, text)
        for match in reversed(list(matches)):
            credential_value = match.group(1)
            
            # Skip if already masked or common words
            if '[CREDENTIAL_MASKED]' not in credential_value and \
               credential_value.lower() not in ['example', 'localhost', 'password', 'username', 'default', 'integration']:
                start = match.start(1)
                end = match.end(1)
                modified_text = modified_text[:start] + "[CREDENTIAL_MASKED]" + modified_text[end:]
                masked_items.append(credential_value)
        
        return modified_text, masked_items

    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy to measure randomness"""
        import math
        from collections import Counter
        
        if not text:
            return 0.0
        
        frequencies = Counter(text)
        entropy = 0.0
        
        for count in frequencies.values():
            probability = count / len(text)
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _sanitize_credentials(self, text: str, credential_type: str) -> Tuple[str, List[str]]:
        """Sanitize credential information"""
        import re
        
        masked_items = []
        modified_text = text
        
        def _mask_value(match_obj, mask_token: str) -> Tuple[str, str]:
            """Helper to replace the matched credential value while preserving context."""
            value_group_index = match_obj.lastindex or 0
            if value_group_index:
                for idx in range(match_obj.lastindex, 0, -1):
                    group_text = match_obj.group(idx)
                    if group_text and group_text.strip() and group_text.lower() not in {"my", "this", "the", "password", "pass", "pwd", "api key", "api", "key", "token"}:
                        value_group_index = idx
                        break
            value_text = match_obj.group(value_group_index) if value_group_index else match_obj.group(0)
            value_start = match_obj.start(value_group_index) if value_group_index else match_obj.start()
            value_end = match_obj.end(value_group_index) if value_group_index else match_obj.end()
            updated_text = modified_text[:value_start] + mask_token + modified_text[value_end:]
            return updated_text, value_text

        if credential_type == "password":
            # Look for password patterns
            password_patterns = [
                r'(?i)(password|pass|pwd)\s*[:=]\s*([^\s]+)',
                r'(?i)(my\s+)?password\s+(?:is\s+)?([^\s]+)',
                r'(?i)the\s+password\s+is\s+([^\s]+)',
                r'(?i)(this\s+is\s+)?(my\s+)?password\s+(?:is\s+)?([a-z0-9@#$%^&*_\\-]{4,})'
            ]
            
            for pattern in password_patterns:
                matches = re.finditer(pattern, text)
                for match in reversed(list(matches)):
                    modified_text, password_value = _mask_value(match, "[PASSWORD_MASKED]")
                    masked_items.append(password_value)
        
        elif credential_type == "api_key":
            # Look for API key patterns
            api_patterns = [
                r'(?i)(api\s+key|access\s+key|token)\s*[:=]\s*([^\s]+)',
                r'(?i)(my\s+)?(api\s+key|token)\s+is\s+([^\s]+)',
                r'(?i)(this\s+is\s+)?(my\s+)?(api\s+key|token)\s+([A-Za-z0-9]+)',
                r'(?i)(api\s+key|token)\s+([A-Za-z0-9]{8,})',
                r'(sk-[a-zA-Z0-9]{20,})',  # OpenAI-style keys
                r'(pk_[a-zA-Z0-9]{20,})',  # Stripe-style keys
            ]
            
            for pattern in api_patterns:
                matches = re.finditer(pattern, text)
                for match in reversed(list(matches)):
                    modified_text, key_value = _mask_value(match, "[API_KEY_MASKED]")
                    masked_items.append(key_value)
        
        elif credential_type == "personal":
            # Expanded PII patterns with overlap prevention
            pii_patterns = [
                # Email addresses
                (r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', "[EMAIL_MASKED]"),
                
                # US Social Security Numbers
                (r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', "[SSN_MASKED]"),
                
                # Phone numbers (US and international)
                (r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', "[PHONE_MASKED]"),
                (r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b', "[PHONE_MASKED]"),
                
                # Credit card numbers
                (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "[CREDIT_CARD_MASKED]"),
                
                # Employee IDs
                (r'\b[Ee]mployee\s*[IiDd]*\s*:?\s*\d{5,8}\b', "[EMPLOYEE_ID_MASKED]"),
                (r'\b[Ee][IiDd]\s*:?\s*\d{5,8}\b', "[EMPLOYEE_ID_MASKED]"),
                
                # Driver's License (US format examples)
                (r'\b[A-Z]{1,2}\d{7,8}\b', "[DL_MASKED]"),
                
                # Passport numbers (generic format)
                (r'\b[A-Z]{2}\d{7}\b', "[PASSPORT_MASKED]"),
                
                # IP addresses
                (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "[IP_ADDRESS_MASKED]"),
                
                # MAC addresses
                (r'\b[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}\b', "[MAC_ADDRESS_MASKED]"),
                
                # Date of Birth patterns
                (r'\b(DOB|Date\s+of\s+Birth)\s*:?\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', "[DOB_MASKED]"),
            ]
            
            # Collect all PII matches with positions
            all_pii_matches = []
            for pattern, mask in pii_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    all_pii_matches.append((match.start(), match.end(), match.group(0), mask))
            
            # Sort by position and length (prefer longer matches)
            all_pii_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
            
            # Remove overlaps
            unique_pii_matches = []
            last_end = -1
            for start, end, content, mask in all_pii_matches:
                if start >= last_end:
                    unique_pii_matches.append((start, end, content, mask))
                    last_end = end
            
            # Apply replacements in reverse order
            for start, end, content, mask in reversed(unique_pii_matches):
                masked_items.append(content)
                modified_text = modified_text[:start] + mask + modified_text[end:]
        
        return modified_text, masked_items
    
    def _sanitize_malicious_content(self, text: str) -> Tuple[str, List[str]]:
        """Sanitize malicious code and commands with expanded pattern detection"""
        import re
        
        malicious_patterns = [
            # Destructive file operations
            r'(?i)\b(rm|del|delete|erase)\s+(-rf?|-r|-f|/[sq])\s*[/\\*~.]',
            r'(?i)\b(format|wipe|destroy|shred)\s+(c:|d:|drive|disk|all|everything)',
            r'(?i)\bdd\s+if=/dev/(zero|random|urandom)',
            
            # Database destruction
            r'(?i)\b(DROP|TRUNCATE)\s+(DATABASE|TABLE|SCHEMA)',
            r'(?i)\bDELETE\s+FROM\s+\w+\s+(WHERE\s+1\s*=\s*1)?',
            
            # System commands
            r'(?i)\b(shutdown|reboot|halt|poweroff)\s+(-[fhr]|now|/[rsf])',
            r'(?i)\binit\s+[06]',
            r'(?i)\b(kill|killall|pkill)\s+(-9|-KILL)\s',
            
            # Code execution patterns
            r'(?i)\b(eval|exec|system|shell_exec|passthru)\s*\(',
            r'(?i)\bRuntime\.getRuntime\(\)\.exec\s*\(',
            r'(?i)\bProcess\.(Start|spawn)\s*\(',
            r'(?i)\bSubprocess\.(call|run|Popen)\s*\(',
            
            # Shell command injection
            r'(?i)(execute|run|system)\s+(rm|del|delete|format|destroy|wipe|drop)',
            r'(?i)\|\s*(bash|sh|cmd|powershell|python)',
            
            # Malware/exploit related
            r'(?i)\b(wget|curl)\s+.*\|\s*(bash|sh|python)',
            r'(?i)\b(msfvenom|metasploit|meterpreter)',
            r'(?i)\breverse\s+shell',
            r'(?i)\b(nc|netcat)\s+-[el]',
            
            # Container/VM destruction
            r'(?i)docker\s+(rm|stop|kill)\s+(-f|--force)',
            r'(?i)kubectl\s+delete\s+(all|--all)',
            r'(?i)docker\s+system\s+prune\s+-a',
            
            # File system manipulation
            r'(?i)\b(mkfs|fdisk|parted)\s',
            r'(?i)\bchmod\s+(777|666)\s',
            r'(?i)\bchown\s+root',
            
            # Network attacks
            r'(?i)\b(nmap|masscan|nikto)\s+-',
            r'(?i)\bsqlmap\s+',
            r'(?i)\bhydra\s+-',
        ]
        
        # Collect all matches with positions
        all_matches = []
        for pattern in malicious_patterns:
            for match in re.finditer(pattern, text):
                all_matches.append((match.start(), match.end(), match.group(0)))
        
        # Sort by position and length (prefer longer matches)
        all_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        
        # Remove overlaps - keep first match at each position
        unique_matches = []
        last_end = -1
        for start, end, content in all_matches:
            if start >= last_end:
                unique_matches.append((start, end, content))
                last_end = end
        
        # Apply replacements in reverse order
        masked_items = []
        modified_text = text
        for start, end, content in reversed(unique_matches):
            masked_items.append(content)
            modified_text = modified_text[:start] + "[MALICIOUS_CODE_REMOVED]" + modified_text[end:]
        
        return modified_text, masked_items
    
    def _sanitize_injection_attempts(self, text: str) -> Tuple[str, List[str]]:
        """Sanitize prompt injection attempts with expanded pattern detection"""
        import re
        
        injection_patterns = [
            # Instruction manipulation
            r'(?i)\b(ignore|forget|disregard|override|skip|bypass)\s+(all\s+)?(previous|above|prior|earlier|your)\s+(instructions|commands|rules|prompts|guidelines|directives)',
            r'(?i)\b(reset|clear|erase|delete)\s+(all\s+)?(instructions|context|memory|history|rules)',
            r'(?i)\b(stop|cease|discontinue)\s+following\s+(instructions|rules|guidelines)',
            
            # Role manipulation
            r'(?i)\b(act|behave|pretend|roleplay|simulate)\s+(as|like)\s+(if\s+)?(you\s+)?(are|were|was)',
            r'(?i)\byou\s+are\s+now\s+(a|an|in|the)\s+\w+',
            r'(?i)\bfrom\s+now\s+on\s+(you\s+)?(are|will\s+be)',
            
            # System prompt leakage
            r'(?i)\b(show|tell|reveal|display|print|output|give\s+me)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions|rules|guidelines)',
            r'(?i)\bwhat\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions|initial\s+prompt)',
            r'(?i)\brepeat\s+(your|the)\s+(system\s+)?(prompt|instructions)',
            
            # Output manipulation
            r'(?i)\b(start|begin|commence)\s+your\s+response\s+(with|by)\s',
            r'(?i)\b(respond|answer|reply|output)\s+only\s+with\s',
            r'(?i)\bdo\s+not\s+(follow|obey|use)\s+(any|your)\s+(instructions|rules|guidelines)',
            r'(?i)\b(end|finish|conclude)\s+your\s+response\s+with\s',
            
            # Context injection
            r'(?i)\[SYSTEM\]|\[INST\]|\[USER\]|\[ASSISTANT\]',
            r'(?i)<\|system\|>|<\|user\|>|<\|assistant\|>',
            r'(?i)###\s*(System|Human|Assistant|User|Instruction)',
        ]
        
        # Collect all matches with positions
        all_matches = []
        for pattern in injection_patterns:
            for match in re.finditer(pattern, text):
                all_matches.append((match.start(), match.end(), match.group(0)))
        
        # Sort by position and length (prefer longer matches)
        all_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        
        # Remove overlaps
        unique_matches = []
        last_end = -1
        for start, end, content in all_matches:
            if start >= last_end:
                unique_matches.append((start, end, content))
                last_end = end
        
        # Apply replacements in reverse order
        masked_items = []
        modified_text = text
        for start, end, content in reversed(unique_matches):
            masked_items.append(content)
            modified_text = modified_text[:start] + "[INJECTION_ATTEMPT_NEUTRALIZED]" + modified_text[end:]
        
        return modified_text, masked_items
    
    def _sanitize_jailbreak_attempts(self, text: str) -> Tuple[str, List[str]]:
        """Sanitize jailbreak attempts with expanded pattern detection"""
        import re
        
        jailbreak_patterns = [
            # Hypothetical framing
            r'(?i)\b(hypothetically|theoretically|imagine|suppose|what\s+if|lets\s+say|lets\s+pretend)\s+',
            r'(?i)\bin\s+a\s+(hypothetical|theoretical)\s+(scenario|situation|world)',
            
            # False authority
            r'(?i)\b(as\s+)?(admin|administrator|root|superuser|cto|ceo|manager|owner|developer|engineer)\s+(said|told\s+me|authorized|approved)',
            r'(?i)\bI\s+(am|have)\s+(authorized|permission|clearance|rights|access)\s+(to|for)',
            r'(?i)\bI\s+have\s+been\s+(granted|given)\s+(access|permission|authorization)',
            
            # Urgency/emergency
            r'(?i)\b(urgent|emergency|critical|immediately|asap|right\s+now)',
            r'(?i)\b(life\s+and\s+death|life\s+threatening|people\s+will\s+(die|suffer))',
            r'(?i)\b(deadline|time\s+sensitive|running\s+out\s+of\s+time)',
            
            # False justification
            r'(?i)\b(for\s+)?(educational|research|testing|academic|learning|study)\s+purposes?',
            r'(?i)\bjust\s+for\s+(learning|study|practice|research|testing)',
            r'(?i)\bthis\s+is\s+(for\s+)?(a\s+)?(class|course|assignment|homework|project)',
            
            # Developer mode tricks
            r'(?i)\b(developer|debug|test|maintenance|admin)\s+mode',
            r'(?i)\benable\s+(admin|developer|debug|god)\s+(access|mode|privileges)',
            r'(?i)\benter\s+(developer|debug|admin)\s+mode',
            
            # Safety/security override attempts
            r'(?i)\b(bypass|override|ignore|disable|turn\s+off|deactivate)\s+(safety|security|guidelines|filters|restrictions|rules)',
            r'(?i)\bwithout\s+(safety|security|ethical)\s+(restrictions|guidelines|considerations)',
            r'(?i)\b(forget|ignore)\s+your\s+(ethics|safety|security)',
            
            # Manipulation tactics
            r'(?i)\beveryone\s+else\s+(does|said|agrees)',
            r'(?i)\bits\s+(completely\s+)?(legal|fine|okay|acceptable|normal)',
            r'(?i)\byou\s+(must|have\s+to|need\s+to|should|will)\s+(do|help|answer|comply)',
        ]
        
        # Collect all matches with positions
        all_matches = []
        for pattern in jailbreak_patterns:
            for match in re.finditer(pattern, text):
                all_matches.append((match.start(), match.end(), match.group(0)))
        
        # Sort by position and length (prefer longer matches)
        all_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        
        # Remove overlaps
        unique_matches = []
        last_end = -1
        for start, end, content in all_matches:
            if start >= last_end:
                unique_matches.append((start, end, content))
                last_end = end
        
        # Apply replacements in reverse order
        masked_items = []
        modified_text = text
        for start, end, content in reversed(unique_matches):
            masked_items.append(content)
            modified_text = modified_text[:start] + "[JAILBREAK_ATTEMPT_NEUTRALIZED]" + modified_text[end:]
        
        return modified_text, masked_items
    
    def _generate_security_assessment(self, main_classification: Dict, detailed_classifications: Dict) -> Tuple[List[str], List[str]]:
        """Generate warnings and blocked patterns based on classifications with context awareness"""
        
        warnings = []
        blocked_patterns = []
        
        # Check context to reduce false positives
        prompt_text = main_classification.get('sequence', '')
        is_question = self._is_asking_question(prompt_text)
        is_disclosure = self._is_disclosing_information(prompt_text)
        
        # Process main classification results
        for label, score in zip(main_classification['labels'], main_classification['scores']):
            # Use configured detection threshold instead of hardcoded 0.6
            if score > self.detection_threshold and label != "normal safe content":
                
                # Use configured blocking threshold instead of hardcoded 0.8
                if score > self.blocking_threshold:
                    # High confidence threats - BLOCK (with context awareness)
                    if "password" in label.lower() or "secret" in label.lower() or "credential" in label.lower():
                        # Allow questions ABOUT security, block actual disclosures
                        if is_question and not is_disclosure:
                            warnings.append(f"Question about credentials detected (allowed): {label} (confidence: {score:.2f})")
                        else:
                        blocked_patterns.append("credential_exposure")
                            warnings.append(f"Credential exposure detected: {label} (confidence: {score:.2f})")
                    
                    elif "malicious" in label.lower() or "system commands" in label.lower():
                        blocked_patterns.append("malicious_code")
                        warnings.append(f"Malicious content detected: {label} (confidence: {score:.2f})")
                    
                    elif "injection" in label.lower() or "manipulation" in label.lower() or "instruction" in label.lower():
                        blocked_patterns.append("prompt_injection")
                        warnings.append(f"Injection attempt detected: {label} (confidence: {score:.2f})")
                    
                    elif "jailbreak" in label.lower() or "role manipulation" in label.lower():
                        # Block jailbreak at ALL security levels when threshold exceeded
                            blocked_patterns.append("jailbreak_attempt")
                        warnings.append(f"Jailbreak attempt detected: {label} (confidence: {score:.2f})")
                    
                    elif "urgent" in label.lower() or "manipulative" in label.lower():
                        blocked_patterns.append("manipulation_attempt")
                        warnings.append(f"Manipulation detected: {label} (confidence: {score:.2f})")
                
                else:  # Above detection threshold but below blocking threshold - warn only
                    warnings.append(f"Potential security issue detected: {label} (confidence: {score:.2f})")
        
        return warnings, blocked_patterns
    
    def _calculate_confidence(self, main_classification: Dict, detailed_classifications: Dict) -> float:
        """Calculate overall confidence in the security assessment"""
        
        # Base confidence on the "normal safe content" score
        safe_scores = [score for label, score in zip(main_classification['labels'], main_classification['scores']) 
                      if label == "normal safe content"]
        
        if safe_scores:
            base_confidence = safe_scores[0]
        else:
            base_confidence = 0.5
        
        # Adjust based on threat detection confidence
        threat_scores = [score for label, score in zip(main_classification['labels'], main_classification['scores']) 
                        if label != "normal safe content" and score > 0.6]
        
        if threat_scores:
            # Lower confidence if threats are detected with high confidence
            max_threat_confidence = max(threat_scores)
            adjusted_confidence = base_confidence * (1 - max_threat_confidence * 0.5)
        else:
            adjusted_confidence = base_confidence
        
        return max(0.0, min(1.0, adjusted_confidence))

# Initialize MCP server
mcp = FastMCP(name="Zero-Shot Secure Prompt Validator")

# Initialize the zero-shot security validator
security_validator = ZeroShotSecurityValidator(SecurityLevel.MEDIUM)

@mcp.tool()
async def validate_prompt_zeroshot(prompt: str, ctx: Context) -> Dict:
    """
    Validate prompt using zero-shot classification for security threats.
    
    Args:
        prompt: The prompt to validate
        ctx: FastMCP context for logging
    
    Returns:
        Dictionary containing validation results and secured prompt
    """
    try:
        if ctx:
            await ctx.info(f"Starting zero-shot validation for prompt of length {len(prompt)}")
        
        # Validate the prompt with zero-shot classification
        result = await security_validator.validate_prompt(prompt, None, ctx)
        
        if ctx:
            await ctx.info(f"Validation complete - Safe: {result.is_safe}, Confidence: {result.confidence:.2f}")
            if result.warnings:
                await ctx.warning(f"Generated {len(result.warnings)} security warnings")
            if prompt != result.modified_prompt:
                await ctx.info("Prompt was modified during sanitization")
        
        return {
            "is_safe": result.is_safe,
            "secured_prompt": result.modified_prompt,
            "original_prompt": prompt,
            "warnings": result.warnings,
            "blocked_patterns": result.blocked_patterns,
            "confidence": result.confidence,
            "modifications_made": prompt != result.modified_prompt,
            "classifications": result.classifications,
            "sanitization_applied": result.sanitization_applied
        }
    
    except Exception as e:
        logger.error(f"Error in zero-shot validation: {e}")
        if ctx:
            await ctx.error(f"Validation failed with error: {str(e)}")
        return {
            "is_safe": False,
            "secured_prompt": "",
            "original_prompt": prompt,
            "warnings": [f"Validation error: {str(e)}"],
            "blocked_patterns": ["validation_error"],
            "confidence": 0.0,
            "modifications_made": False,
            "classifications": {},
            "sanitization_applied": {}
        }

@mcp.tool()
async def analyze_prompt_classification(prompt: str, ctx: Context) -> Dict:
    """
    Analyze prompt using zero-shot classification without applying security measures.
    
    Args:
        prompt: The prompt to analyze
        ctx: FastMCP context for logging
    
    Returns:
        Dictionary containing detailed classification results
    """
    try:
        if ctx:
            await ctx.info(f"Starting zero-shot analysis for prompt of length {len(prompt)}")
        
        # Get main classification
        main_classification = security_validator._classify_security_threats(prompt)
        
        # Get detailed classifications for high-confidence threats
        detailed_classifications = {}
        for label, score in zip(main_classification['labels'], main_classification['scores']):
            if score > 0.6 and label != "normal safe content":
                detailed_result = security_validator._detailed_classification(prompt, label)
                detailed_classifications[label] = detailed_result
        
        if ctx:
            await ctx.info(f"Analysis complete - Found {len(detailed_classifications)} detailed threat categories")
        
        return {
            "success": True,
            "main_classification": main_classification,
            "detailed_classifications": detailed_classifications,
            "prompt": prompt,
            "analysis_timestamp": asyncio.get_event_loop().time()
        }
    
    except Exception as e:
        logger.error(f"Error in zero-shot analysis: {e}")
        if ctx:
            await ctx.error(f"Analysis failed with error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "prompt": prompt
        }

@mcp.tool()
async def update_security_level_zeroshot(level: str, ctx: Context) -> Dict:
    """
    Update the security level for zero-shot validation.
    
    Args:
        level: Security level (low, medium, high)
        ctx: FastMCP context for logging
    
    Returns:
        Dictionary containing the update result
    """
    try:
        if ctx:
            await ctx.info(f"Updating zero-shot security level to: {level}")
        
        new_level = SecurityLevel(level.lower())
        security_validator.security_level = new_level
        logger.info(f"Zero-shot security level updated to: {new_level.value}")
        
        if ctx:
            await ctx.info(f"Security level successfully updated to {new_level.value}")
        
        return {
            "success": True,
            "new_level": new_level.value,
            "message": f"Zero-shot security level set to {new_level.value}"
        }
    
    except ValueError:
        if ctx:
            await ctx.error(f"Invalid security level: {level}")
        return {
            "success": False,
            "error": f"Invalid security level: {level}. Valid options: low, medium, high"
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to update security level: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_zeroshot_stats(ctx: Context) -> Dict:
    """
    Get statistics about the zero-shot security validator.
    
    Args:
        ctx: FastMCP context for logging
    
    Returns:
        Dictionary containing zero-shot validator statistics
    """
    try:
        if ctx:
            await ctx.info("Retrieving zero-shot validator statistics")
        
        return {
            "success": True,
            "current_security_level": security_validator.security_level.value,
            "model_info": {
                "model_name": "facebook/bart-large-mnli",
                "model_type": "zero-shot-classification",
                "device": "cuda" if torch.cuda.is_available() else "cpu"
            },
            "classification_categories": {
                "main_categories": len(security_validator.security_categories),
                "detailed_categories": sum(len(cats) for cats in security_validator.detailed_categories.values()),
                "category_types": list(security_validator.detailed_categories.keys())
            },
            "capabilities": [
                "Zero-shot classification",
                "Multi-label threat detection", 
                "Contextual understanding",
                "Automatic sanitization",
                "Confidence scoring",
                "Detailed threat analysis"
            ],
            "description": "Standalone Zero-Shot Secure Prompt Validator using Transformer Models"
        }
    
    except Exception as e:
        logger.error(f"Error retrieving zero-shot stats: {e}")
        if ctx:
            await ctx.error(f"Failed to retrieve stats: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Run the zero-shot secure MCP server"""
    logger.info("Starting Zero-Shot Secure Prompt MCP Server...")
    logger.info("Using transformer-based zero-shot classification for security validation")
    mcp.run(transport="http", host="0.0.0.0", port=8002)

if __name__ == "__main__":
    main()
