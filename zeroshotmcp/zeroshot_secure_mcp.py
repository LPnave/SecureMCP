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
        self.setup_models()
        self.setup_classification_categories()
        self.setup_spacy_matcher()

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
        
        # Main security categories
        self.security_categories = [
            "contains password or secret credentials",
            "contains API key or authentication token", 
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
            if score > 0.6 and category != "normal safe content":
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
        modified_prompt, sanitization_applied = await self._process_classifications(
            modified_prompt, main_classification, detailed_classifications, ctx
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
                                     detailed_classifications: Dict, ctx=None) -> Tuple[str, Dict]:
        """Process classifications and apply sanitization"""
        
        modified_prompt = prompt
        sanitization_applied = {}
        
        # Process each high-confidence threat
        for i, (label, score) in enumerate(zip(main_classification['labels'], main_classification['scores'])):
            if score > 0.5 and label != "normal safe content":
                
                if ctx:
                    await ctx.debug(f"Processing threat: {label} (confidence: {score:.2f})")
                
                # Apply appropriate sanitization based on threat type
                if "password" in label.lower() or "secret" in label.lower():
                    modified_prompt, masked_items = self._sanitize_credentials(modified_prompt, "password")
                    if masked_items:
                        sanitization_applied['passwords_masked'] = masked_items
                
                elif "api key" in label.lower() or "token" in label.lower():
                    modified_prompt, masked_items = self._sanitize_credentials(modified_prompt, "api_key")
                    if masked_items:
                        sanitization_applied['api_keys_masked'] = masked_items
                
                elif "personal information" in label.lower() or "email" in label.lower():
                    modified_prompt, masked_items = self._sanitize_credentials(modified_prompt, "personal")
                    if masked_items:
                        sanitization_applied['personal_info_masked'] = masked_items
                
                elif "malicious code" in label.lower() or "system commands" in label.lower():
                    modified_prompt, masked_items = self._sanitize_malicious_content(modified_prompt)
                    if masked_items:
                        sanitization_applied['malicious_content_removed'] = masked_items
                
                elif "prompt injection" in label.lower() or "instruction manipulation" in label.lower():
                    modified_prompt, masked_items = self._sanitize_injection_attempts(modified_prompt)
                    if masked_items:
                        sanitization_applied['injection_attempts_neutralized'] = masked_items
                
                elif "jailbreak" in label.lower() or "role manipulation" in label.lower():
                    modified_prompt, masked_items = self._sanitize_jailbreak_attempts(modified_prompt)
                    if masked_items:
                        sanitization_applied['jailbreak_attempts_neutralized'] = masked_items
        
        return modified_prompt, sanitization_applied
    
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
            # Look for email addresses and personal info
            email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
            matches = re.finditer(email_pattern, text)
            for match in reversed(list(matches)):
                modified_text, email = _mask_value(match, "[EMAIL_MASKED]")
                masked_items.append(email)
        
        return modified_text, masked_items
    
    def _sanitize_malicious_content(self, text: str) -> Tuple[str, List[str]]:
        """Sanitize malicious code and commands"""
        import re
        
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
        import re
        
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
        import re
        
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
        
        # Process main classification results
        for label, score in zip(main_classification['labels'], main_classification['scores']):
            if score > 0.6 and label != "normal safe content":
                
                if score > 0.8:  # High confidence - block
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
                
                else:  # Medium confidence - warn
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
