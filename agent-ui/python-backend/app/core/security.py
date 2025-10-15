"""
Zero-Shot Security Validator
Extracted and adapted from zeroshot_secure_mcp.py
"""

import math
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

from transformers import pipeline
import torch
import spacy
from spacy.matcher import Matcher

from app.core.config import SecurityLevel
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ValidationResult:
    """Result of prompt validation"""
    is_safe: bool
    modified_prompt: str
    warnings: List[str]
    blocked_patterns: List[str]
    confidence: float
    classifications: Dict[str, Dict]
    sanitization_applied: Dict[str, List[str]]
    processing_time_ms: float = 0.0


class ZeroShotSecurityValidator:
    """Zero-shot security validator using transformer models"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        self.security_level = security_level
        self.setup_models()
        self.setup_classification_categories()
        self.setup_spacy_matcher()
        logger.info(f"Security validator initialized with level: {security_level.value}")

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

    def setup_classification_categories(self):
        """Define categories for zero-shot classification"""
        
        self.security_categories = [
            "contains password or secret credentials",
            "contains API key, access token, or authentication credential",
            "contains cloud subscription ID, tenant ID, or service credential",
            "contains personal information or email address",
            "contains malicious code or system commands",
            "attempts prompt injection or instruction manipulation",
            "attempts jailbreak or role manipulation",
            "contains urgent or manipulative language",
            "requests system access or file operations",
            "contains database credentials or connection strings",
            "normal safe content"
        ]
        
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
    
    def validate_prompt(self, prompt: str) -> ValidationResult:
        """
        Validate prompt using zero-shot classification
        
        Args:
            prompt: The prompt to validate
        
        Returns:
            ValidationResult with sanitization details
        """
        import time
        start_time = time.time()
        
        logger.info(f"Validating prompt of length {len(prompt)}")
        
        warnings = []
        blocked_patterns = []
        modified_prompt = prompt
        confidence = 1.0
        classifications = {}
        sanitization_applied = {}
        
        # Main security classification
        main_classification = self._classify_security_threats(prompt)
        classifications['main'] = main_classification
        
        # Detailed classification for each detected threat type
        detailed_classifications = {}
        for category, score in zip(main_classification['labels'], main_classification['scores']):
            if score > 0.6 and category != "normal safe content":
                detailed_result = self._detailed_classification(prompt, category)
                detailed_classifications[category] = detailed_result
        
        classifications['detailed'] = detailed_classifications
        
        # Supplemental spaCy pattern detection
        spacy_detections = self._detect_spacy_patterns(prompt)
        spacy_sanitization = {}
        if any(spacy_detections.values()):
            logger.debug("spaCy matcher detected sensitive patterns")
            sanitized_text, spacy_sanitization = self._apply_spacy_sanitization(modified_prompt, spacy_detections)
            if sanitized_text != modified_prompt:
                modified_prompt = sanitized_text
        
        # Apply security logic based on classifications
        modified_prompt, sanitization_applied = self._process_classifications(
            modified_prompt, main_classification, detailed_classifications
        )
        
        sanitization_applied = self._merge_sanitization_records(sanitization_applied, spacy_sanitization)
        
        # Generate warnings and blocked patterns
        warnings, blocked_patterns = self._generate_security_assessment(
            main_classification, detailed_classifications
        )
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(main_classification, detailed_classifications)
        
        # Determine if prompt is safe
        is_safe = len(blocked_patterns) == 0
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Validation complete - Safe: {is_safe}, Confidence: {confidence:.2f}, Time: {processing_time:.2f}ms")
        
        return ValidationResult(
            is_safe=is_safe,
            modified_prompt=modified_prompt,
            warnings=warnings,
            blocked_patterns=blocked_patterns,
            confidence=confidence,
            classifications=classifications,
            sanitization_applied=sanitization_applied,
            processing_time_ms=processing_time
        )
    
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
    
    def _process_classifications(self, prompt: str, main_classification: Dict, 
                                detailed_classifications: Dict) -> Tuple[str, Dict]:
        """Process classifications and apply intelligent sanitization"""
        
        modified_prompt = prompt
        sanitization_applied = {}
        credential_sanitization_applied = False
        
        for i, (label, score) in enumerate(zip(main_classification['labels'], main_classification['scores'])):
            if score > 0.5 and label != "normal safe content":
                
                if any(keyword in label.lower() for keyword in ['password', 'secret', 'credential', 'api key', 'token', 'personal']):
                    credential_sanitization_applied = True
                    modified_prompt, entropy_masked = self._sanitize_high_entropy_credentials(modified_prompt)
                    if entropy_masked:
                        sanitization_applied.setdefault('entropy_masked_credentials', []).extend(entropy_masked)
                    
                    modified_prompt, keyword_masked = self._sanitize_credentials_generic(modified_prompt)
                    if keyword_masked:
                        sanitization_applied.setdefault('keyword_masked_credentials', []).extend(keyword_masked)
                
                elif "malicious code" in label.lower() or "system commands" in label.lower():
                    modified_prompt, masked = self._sanitize_malicious_content(modified_prompt)
                    if masked:
                        sanitization_applied.setdefault('malicious_removed', []).extend(masked)
                
                elif "injection" in label.lower() or "instruction manipulation" in label.lower():
                    modified_prompt, masked = self._sanitize_injection_attempts(modified_prompt)
                    if masked:
                        sanitization_applied.setdefault('injection_neutralized', []).extend(masked)
                
                elif "jailbreak" in label.lower() or "role manipulation" in label.lower():
                    modified_prompt, masked = self._sanitize_jailbreak_attempts(modified_prompt)
                    if masked:
                        sanitization_applied.setdefault('jailbreak_neutralized', []).extend(masked)
        
        if not credential_sanitization_applied:
            credential_labels = [label for label, score in zip(main_classification['labels'], main_classification['scores']) 
                               if score > 0.15 and any(kw in label.lower() for kw in ['password', 'secret', 'credential', 'api', 'token', 'database'])]
            
            if credential_labels:
                modified_prompt, entropy_masked = self._sanitize_high_entropy_credentials(modified_prompt)
                if entropy_masked:
                    sanitization_applied.setdefault('entropy_masked_credentials', []).extend(entropy_masked)
                
                modified_prompt, keyword_masked = self._sanitize_credentials_generic(modified_prompt)
                if keyword_masked:
                    sanitization_applied.setdefault('keyword_masked_credentials', []).extend(keyword_masked)
        
        return modified_prompt, sanitization_applied

    def _sanitize_high_entropy_credentials(self, text: str) -> Tuple[str, List[str]]:
        """Primary sanitization: Detect and mask high-entropy strings"""
        modified_text = text
        masked_items = []
        
        candidates = re.finditer(r'\b([A-Za-z0-9\-_\.]{8,})\b', text)
        
        for match in candidates:
            value = match.group(1)
            entropy = self._calculate_entropy(value)
            
            if entropy >= 3.5:
                has_upper = any(c.isupper() for c in value)
                has_lower = any(c.islower() for c in value)
                has_digit = any(c.isdigit() for c in value)
                
                context_start = max(0, match.start() - 30)
                context = text[context_start:match.start()].lower()
                
                credential_indicators = [
                    'key', 'token', 'secret', 'password', 'credential',
                    'auth', 'api', 'subscription', 'tenant', 'client',
                    'azure', 'aws', 'gcp', 'access', 'bearer'
                ]
                
                in_credential_context = any(word in context for word in credential_indicators)
                
                should_mask = (
                    (has_upper and has_lower and has_digit) or 
                    (entropy >= 4.0 and in_credential_context) or
                    (entropy >= 3.8 and in_credential_context)
                )
                
                if should_mask:
                    if value.lower() not in ['example', 'localhost', 'password', 'username', 'integration']:
                        masked_items.append(value)
        
        for value in reversed(masked_items):
            pattern = re.escape(value)
            modified_text = re.sub(pattern, '[CREDENTIAL_MASKED]', modified_text)
        
        return modified_text, masked_items

    def _sanitize_credentials_generic(self, text: str) -> Tuple[str, List[str]]:
        """Backup sanitization: Keyword-based credential detection"""
        masked_items = []
        modified_text = text
        
        CREDENTIAL_KEYWORDS = [
            'password', 'pass', 'pwd', 'secret', 'token', 'key', 'api',
            'auth', 'credential', 'access', 'subscription', 'tenant',
            'client_id', 'client_secret', 'bearer', 'apikey',
            'azure', 'aws', 'gcp', 'oauth', 'jwt'
        ]
        
        pattern = r'(?i)(?:' + '|'.join(CREDENTIAL_KEYWORDS) + r')(?:\s+(?:key|id|token|secret|code|subscription))?\s*[:=]?\s*([A-Za-z0-9\-_\.]{6,})'
        
        matches = re.finditer(pattern, text)
        for match in reversed(list(matches)):
            credential_value = match.group(1)
            
            if '[CREDENTIAL_MASKED]' not in credential_value and \
               credential_value.lower() not in ['example', 'localhost', 'password', 'username', 'default', 'integration']:
                start = match.start(1)
                end = match.end(1)
                modified_text = modified_text[:start] + "[CREDENTIAL_MASKED]" + modified_text[end:]
                masked_items.append(credential_value)
        
        return modified_text, masked_items

    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy to measure randomness"""
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
        masked_items = []
        modified_text = text
        
        def _mask_value(match_obj, mask_token: str) -> Tuple[str, str]:
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
            api_patterns = [
                r'(?i)(api\s+key|access\s+key|token)\s*[:=]\s*([^\s]+)',
                r'(?i)(my\s+)?(api\s+key|token)\s+is\s+([^\s]+)',
                r'(?i)(this\s+is\s+)?(my\s+)?(api\s+key|token)\s+([A-Za-z0-9]+)',
                r'(?i)(api\s+key|token)\s+([A-Za-z0-9]{8,})',
                r'(sk-[a-zA-Z0-9]{20,})',
                r'(pk_[a-zA-Z0-9]{20,})',
            ]
            
            for pattern in api_patterns:
                matches = re.finditer(pattern, text)
                for match in reversed(list(matches)):
                    modified_text, key_value = _mask_value(match, "[API_KEY_MASKED]")
                    masked_items.append(key_value)
        
        elif credential_type == "personal":
            email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
            matches = re.finditer(email_pattern, text)
            for match in reversed(list(matches)):
                modified_text, email = _mask_value(match, "[EMAIL_MASKED]")
                masked_items.append(email)
        
        return modified_text, masked_items
    
    def _sanitize_malicious_content(self, text: str) -> Tuple[str, List[str]]:
        """Sanitize malicious code and commands"""
        malicious_patterns = [
            r'(?i)(rm\s+-rf|del\s+/s|delete\s+all)',
            r'(?i)(execute|run|system)\s*\([^)]+\)',
            r'(?i)(eval|exec)\s*\([^)]+\)',
            r'(?i)(wget|curl)\s+[^\s]+',
            r'(?i)(format|destroy|wipe)\s+[^\s]+'
        ]
        
        masked_items = []
        modified_text = text
        
        for pattern in malicious_patterns:
            matches = re.finditer(pattern, text)
            for match in reversed(list(matches)):
                malicious_content = match.group(0)
                masked_items.append(malicious_content)
                modified_text = modified_text[:match.start()] + "[MALICIOUS_CODE_REMOVED]" + modified_text[match.end():]
        
        return modified_text, masked_items
    
    def _sanitize_injection_attempts(self, text: str) -> Tuple[str, List[str]]:
        """Sanitize prompt injection attempts"""
        injection_patterns = [
            r'(?i)(ignore|forget|disregard)\s+(all\s+)?(previous|above|prior)\s+(instructions|commands|prompts)',
            r'(?i)(override|skip)\s+(all\s+)?(previous|above|prior)\s+(instructions|commands)',
            r'(?i)(act\s+as|pretend\s+to\s+be|simulate)\s+[^.!?]+',
            r'(?i)(begin|start)\s+your\s+response\s+with',
            r'(?i)(respond\s+only|output\s+only)\s+with'
        ]
        
        masked_items = []
        modified_text = text
        
        for pattern in injection_patterns:
            matches = re.finditer(pattern, text)
            for match in reversed(list(matches)):
                injection_content = match.group(0)
                masked_items.append(injection_content)
                modified_text = modified_text[:match.start()] + "[INJECTION_ATTEMPT_NEUTRALIZED]" + modified_text[match.end():]
        
        return modified_text, masked_items
    
    def _sanitize_jailbreak_attempts(self, text: str) -> Tuple[str, List[str]]:
        """Sanitize jailbreak attempts"""
        jailbreak_patterns = [
            r'(?i)(hypothetically|imagine|suppose)\s+[^.!?]+',
            r'(?i)(this\s+is\s+)?(urgent|critical|emergency|important)',
            r'(?i)(you\s+must|you\s+should|you\s+will)\s+[^.!?]+',
            r'(?i)(bypass|override|ignore)\s+(safety|security|guidelines)',
            r'(?i)(turn\s+off|disable)\s+(safety|security|filters)'
        ]
        
        masked_items = []
        modified_text = text
        
        for pattern in jailbreak_patterns:
            matches = re.finditer(pattern, text)
            for match in reversed(list(matches)):
                jailbreak_content = match.group(0)
                masked_items.append(jailbreak_content)
                modified_text = modified_text[:match.start()] + "[JAILBREAK_ATTEMPT_NEUTRALIZED]" + modified_text[match.end():]
        
        return modified_text, masked_items
    
    def _generate_security_assessment(self, main_classification: Dict, detailed_classifications: Dict) -> Tuple[List[str], List[str]]:
        """Generate warnings and blocked patterns based on classifications"""
        warnings = []
        blocked_patterns = []
        
        for label, score in zip(main_classification['labels'], main_classification['scores']):
            if score > 0.6 and label != "normal safe content":
                
                if score > 0.8:
                    if "password" in label.lower() or "secret" in label.lower():
                        blocked_patterns.append("credential_exposure")
                        warnings.append(f"High-confidence credential exposure detected: {label}")
                    
                    elif "malicious" in label.lower() or "system commands" in label.lower():
                        blocked_patterns.append("malicious_code")
                        warnings.append(f"High-confidence malicious content detected: {label}")
                    
                    elif "injection" in label.lower() or "manipulation" in label.lower():
                        blocked_patterns.append("prompt_injection")
                        warnings.append(f"High-confidence injection attempt detected: {label}")
                    
                    elif "jailbreak" in label.lower() or "manipulation" in label.lower():
                        if self.security_level == SecurityLevel.HIGH:
                            blocked_patterns.append("jailbreak_attempt")
                        warnings.append(f"High-confidence jailbreak attempt detected: {label}")
                
                else:
                    warnings.append(f"Potential security issue detected: {label} (confidence: {score:.2f})")
        
        return warnings, blocked_patterns
    
    def _calculate_confidence(self, main_classification: Dict, detailed_classifications: Dict) -> float:
        """Calculate overall confidence in the security assessment"""
        safe_scores = [score for label, score in zip(main_classification['labels'], main_classification['scores']) 
                      if label == "normal safe content"]
        
        if safe_scores:
            base_confidence = safe_scores[0]
        else:
            base_confidence = 0.5
        
        threat_scores = [score for label, score in zip(main_classification['labels'], main_classification['scores']) 
                        if label != "normal safe content" and score > 0.6]
        
        if threat_scores:
            max_threat_confidence = max(threat_scores)
            adjusted_confidence = base_confidence * (1 - max_threat_confidence * 0.5)
        else:
            adjusted_confidence = base_confidence
        
        return max(0.0, min(1.0, adjusted_confidence))
