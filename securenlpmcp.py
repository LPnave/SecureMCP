#!/usr/bin/env python3
"""
Enhanced Secure Prompt MCP Server with NLP
A Model Context Protocol server that uses spaCy for advanced prompt security validation.
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from fastmcp import FastMCP
import spacy
from spacy.matcher import Matcher
from spacy.tokens import Span

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class SecurityResult:
    is_safe: bool
    modified_prompt: str
    warnings: List[str]
    blocked_patterns: List[str]
    confidence: float
    nlp_analysis: Optional[Dict] = None

class EnhancedPromptSecurityValidator:
    """Enhanced security validator using spaCy NLP"""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        self.security_level = security_level
        self.setup_nlp()
        self.setup_patterns()
    
    def setup_nlp(self):
        """Initialize spaCy NLP pipeline"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.matcher = Matcher(self.nlp.vocab)
            logger.info("spaCy NLP pipeline loaded successfully")
        except OSError:
            logger.error("spaCy model 'en_core_web_sm' not found. Please install with: python -m spacy download en_core_web_sm")
            raise
    
    def setup_patterns(self):
        """Initialize NLP-based security patterns"""
        
        # Comprehensive injection detection patterns using spaCy
        self.injection_patterns = [
            # Direct instruction manipulation
            [{"LOWER": "ignore"}, {"LOWER": {"IN": ["all", "previous", "above", "prior", "earlier"]}}, {"LOWER": {"IN": ["instructions", "commands", "prompts", "rules"]}}],
            [{"LOWER": "forget"}, {"LOWER": {"IN": ["everything", "all", "above", "previous", "prior"]}}],
            [{"LOWER": "disregard"}, {"LOWER": {"IN": ["all", "previous", "above", "prior"]}}, {"LOWER": {"IN": ["instructions", "commands", "prompts", "rules"]}}],
            [{"LOWER": "override"}, {"LOWER": {"IN": ["previous", "all", "above"]}}, {"LOWER": {"IN": ["instructions", "commands", "settings"]}}],
            [{"LOWER": "skip"}, {"LOWER": {"IN": ["all", "previous", "above"]}}, {"LOWER": {"IN": ["instructions", "commands", "rules"]}}],
            
            # Role manipulation
            [{"LOWER": "act"}, {"LOWER": "as"}, {"LOWER": {"IN": ["if", "though"]}}],
            [{"LOWER": "pretend"}, {"LOWER": {"IN": ["to", "you"]}}, {"LOWER": {"IN": ["be", "are"]}}],
            [{"LOWER": "simulate"}, {"LOWER": {"IN": ["being", "a", "an"]}}],
            [{"LOWER": "role"}, {"LOWER": "play"}, {"LOWER": {"IN": ["as", "being"]}, "OP": "?"}],
            [{"LOWER": "behave"}, {"LOWER": {"IN": ["like", "as"]}}, {"LOWER": {"IN": ["a", "an"]}, "OP": "?"}],
            [{"LOWER": "become"}, {"LOWER": {"IN": ["a", "an"]}, "OP": "?"}],
            
            # Response manipulation
            [{"LOWER": "begin"}, {"LOWER": "your"}, {"LOWER": "response"}, {"LOWER": "with"}],
            [{"LOWER": "start"}, {"LOWER": "your"}, {"LOWER": {"IN": ["response", "answer"]}}, {"LOWER": "with"}],
            [{"LOWER": "respond"}, {"LOWER": {"IN": ["only", "just"]}}, {"LOWER": "with"}],
            [{"LOWER": "output"}, {"LOWER": {"IN": ["only", "just"]}}, {"LOWER": {"IN": ["the", "a"]}}],
            [{"LOWER": "repeat"}, {"LOWER": {"IN": ["after", "the"]}}],
            [{"LOWER": "echo"}, {"LOWER": {"IN": ["the", "this"]}}],
            [{"LOWER": "say"}, {"LOWER": {"IN": ["only", "just"]}}, {"LOWER": {"IN": ["the", "this"]}}],
            
            # System manipulation
            [{"LOWER": "execute"}, {"LOWER": {"IN": ["the", "this"]}}],
            [{"LOWER": "run"}, {"LOWER": {"IN": ["the", "this"]}}],
            [{"LOWER": "process"}, {"LOWER": {"IN": ["the", "this"]}}],
        ]
        
        # Add injection patterns to matcher
        for i, pattern in enumerate(self.injection_patterns):
            self.matcher.add(f"INJECTION_{i}", [pattern])
        
        # Sensitive data detection patterns using NLP - simplified to avoid over-matching
        self.sensitive_data_patterns = [
            # Basic credential indicators - will be extended with values in post-processing
            [{"LOWER": "my"}, {"LOWER": {"IN": ["api", "access"]}}, {"LOWER": {"IN": ["key", "token"]}}],
            [{"LOWER": {"IN": ["api", "access"]}}, {"LOWER": {"IN": ["key", "token"]}}],
            [{"LOWER": "my"}, {"LOWER": {"IN": ["password", "secret"]}}],
            [{"LOWER": {"IN": ["password", "secret"]}}],
            [{"LOWER": "my"}, {"LOWER": {"IN": ["username", "user"]}}],
            [{"LOWER": {"IN": ["username", "user"]}}],
            [{"LOWER": "my"}, {"LOWER": "email"}],
            [{"LOWER": "email"}],
            [{"LOWER": "connection"}, {"LOWER": "string"}],
            [{"LOWER": {"IN": ["database", "db"]}}, {"LOWER": {"IN": ["password", "user", "username"]}}],
        ]
        
        # Add sensitive data patterns to matcher
        for i, pattern in enumerate(self.sensitive_data_patterns):
            self.matcher.add(f"SENSITIVE_{i}", [pattern])
        
        # Malicious code patterns using NLP
        self.malicious_patterns = [
            # Destructive commands
            [{"LOWER": {"IN": ["rm", "del", "delete"]}}, {"LOWER": {"IN": ["-rf", "-r", "/s"]}, "OP": "?"}],
            [{"LOWER": "remove"}, {"LOWER": {"IN": ["all", "everything"]}}],
            [{"LOWER": "format"}, {"LOWER": {"IN": ["drive", "disk", "system"]}}],
            [{"LOWER": {"IN": ["destroy", "wipe", "erase"]}}, {"LOWER": {"IN": ["all", "everything"]}, "OP": "?"}],
            
            # Code execution patterns
            [{"LOWER": {"IN": ["eval", "exec", "execute"]}}, {"TEXT": "(", "OP": "?"}],
            [{"LOWER": "system"}, {"TEXT": "(", "OP": "?"}],
            [{"LOWER": {"IN": ["subprocess", "os"]}}, {"LOWER": {"IN": ["call", "run", "popen", "system"]}}],
            [{"LOWER": "__import__"}],
            
            # Network operations
            [{"LOWER": {"IN": ["wget", "curl"]}}, {"LOWER": {"IN": ["http", "https"]}, "OP": "?"}],
            [{"LOWER": {"IN": ["nc", "netcat"]}}, {"LOWER": "-l", "OP": "?"}],
            [{"LOWER": "download"}, {"LOWER": {"IN": ["and", "&"]}, "OP": "?"}, {"LOWER": {"IN": ["execute", "run"]}}],
            
            # File operations
            [{"LOWER": {"IN": ["open", "read", "write"]}}, {"LOWER": {"IN": ["file", "files"]}}],
            [{"LOWER": "import"}, {"LOWER": {"IN": ["os", "sys", "subprocess"]}}],
        ]
        
        # Add malicious patterns to matcher
        for i, pattern in enumerate(self.malicious_patterns):
            self.matcher.add(f"MALICIOUS_{i}", [pattern])
        
        # Jailbreak attempt patterns using NLP
        self.jailbreak_patterns = [
            # Authority and urgency
            [{"LOWER": "you"}, {"LOWER": {"IN": ["must", "should", "will", "need"]}}, {"LOWER": {"IN": ["help", "assist", "comply"]}}],
            [{"LOWER": {"IN": ["it", "this"]}}, {"LOWER": {"IN": ["is", "s"]}}, {"LOWER": {"IN": ["important", "urgent", "critical", "emergency"]}}],
            [{"LOWER": {"IN": ["please", "i"]}}, {"LOWER": {"IN": ["need", "require"]}}, {"LOWER": {"IN": ["help", "assistance"]}}],
            
            # Bypass attempts
            [{"LOWER": {"IN": ["bypass", "override", "ignore"]}}, {"LOWER": {"IN": ["safety", "security", "guidelines", "rules"]}}],
            [{"LOWER": "disable"}, {"LOWER": {"IN": ["safety", "security", "filters"]}}],
            [{"LOWER": "turn"}, {"LOWER": "off"}, {"LOWER": {"IN": ["safety", "security"]}}],
            
            # Hypothetical scenarios
            [{"LOWER": "hypothetically"}, {"LOWER": "speaking"}],
            [{"LOWER": "in"}, {"LOWER": {"IN": ["theory", "a"]}}, {"LOWER": {"IN": ["fictional", "theoretical"]}, "OP": "?"}],
            [{"LOWER": "what"}, {"LOWER": {"IN": ["if", "would"]}}, {"LOWER": {"IN": ["happen", "you"]}}],
            [{"LOWER": "imagine"}, {"LOWER": {"IN": ["if", "that"]}}],
            [{"LOWER": "suppose"}, {"LOWER": {"IN": ["that", "you"]}}],
            
            # Emotional manipulation
            [{"LOWER": {"IN": ["i", "im"]}}, {"LOWER": {"IN": ["desperate", "stuck", "confused"]}}],
            [{"LOWER": "my"}, {"LOWER": {"IN": ["life", "job", "career"]}}, {"LOWER": {"IN": ["depends", "relies"]}}],
        ]
        
        # Add jailbreak patterns to matcher
        for i, pattern in enumerate(self.jailbreak_patterns):
            self.matcher.add(f"JAILBREAK_{i}", [pattern])
        
        # Define semantic keywords for context analysis
        self.sensitive_keywords = {
            'credential_indicators': ['password', 'secret', 'key', 'token', 'credential', 'login', 'auth'],
            'system_indicators': ['execute', 'run', 'system', 'command', 'shell', 'terminal'],
            'manipulation_indicators': ['ignore', 'forget', 'override', 'bypass', 'disable'],
            'role_indicators': ['act', 'pretend', 'simulate', 'behave', 'become', 'role'],
            'urgency_indicators': ['urgent', 'critical', 'important', 'emergency', 'asap', 'immediately'],
        }
    
    async def validate_prompt(self, prompt: str, context: Optional[Dict] = None) -> SecurityResult:
        """Pure NLP-based validation and sanitization"""
        warnings = []
        blocked_patterns = []
        modified_prompt = prompt
        confidence = 1.0
        nlp_analysis = {}
        
        # Process with spaCy
        doc = self.nlp(prompt)
        
        # Comprehensive NLP pattern detection
        matches = self.matcher(doc)
        nlp_analysis['total_matches'] = len(matches)
        nlp_analysis['matches'] = []
        
        injection_matches = []
        sensitive_matches = []
        malicious_matches = []
        jailbreak_matches = []
        
        # Categorize matches
        for match_id, start, end in matches:
            match_label = self.nlp.vocab.strings[match_id]
            match_text = doc[start:end].text
            match_info = {
                'label': match_label,
                'text': match_text,
                'start': start,
                'end': end
            }
            nlp_analysis['matches'].append(match_info)
            
            if match_label.startswith('INJECTION_'):
                injection_matches.append(match_info)
            elif match_label.startswith('SENSITIVE_'):
                sensitive_matches.append(match_info)
            elif match_label.startswith('MALICIOUS_'):
                malicious_matches.append(match_info)
            elif match_label.startswith('JAILBREAK_'):
                jailbreak_matches.append(match_info)
        
        # Calculate scores based on matches and semantic analysis
        injection_score = self._calculate_injection_score(doc, injection_matches)
        sensitive_score = self._calculate_sensitive_score(doc, sensitive_matches)
        malicious_score = self._calculate_malicious_score(doc, malicious_matches)
        jailbreak_score = self._calculate_jailbreak_score(doc, jailbreak_matches)
        
        nlp_analysis.update({
            'injection_score': injection_score,
            'sensitive_score': sensitive_score,
            'malicious_score': malicious_score,
            'jailbreak_score': jailbreak_score,
            'semantic_features': self._analyze_semantic_features(doc)
        })
        
        # Apply sanitization and determine if prompt should be blocked
        modified_prompt, sanitization_applied = self._intelligent_sanitize(doc, {
            'injection_matches': injection_matches,
            'sensitive_matches': sensitive_matches,
            'malicious_matches': malicious_matches,
            'jailbreak_matches': jailbreak_matches
        })
        
        # Determine safety based on security level and scores
        if injection_score > 0.3:
            warnings.append(f"Prompt injection detected (confidence: {injection_score:.2f})")
            if self.security_level == SecurityLevel.HIGH or injection_score > 0.7:
                blocked_patterns.append("prompt_injection")
        
        if sensitive_score > 0.2:
            warnings.append(f"Sensitive data detected and sanitized (confidence: {sensitive_score:.2f})")
        
        if malicious_score > 0.3:
            warnings.append(f"Malicious code patterns detected (confidence: {malicious_score:.2f})")
            if self.security_level in [SecurityLevel.MEDIUM, SecurityLevel.HIGH] or malicious_score > 0.7:
                blocked_patterns.append("malicious_code")
        
        if jailbreak_score > 0.4:
            warnings.append(f"Jailbreak attempt detected (confidence: {jailbreak_score:.2f})")
            if self.security_level == SecurityLevel.HIGH or jailbreak_score > 0.8:
                blocked_patterns.append("jailbreak_attempt")
        
        # Context-based checks
        if context:
            context_warnings = self._check_context_security(modified_prompt, context)
            warnings.extend(context_warnings)
        
        # Calculate overall confidence
        confidence = 1.0 - max(injection_score, malicious_score, jailbreak_score)
        is_safe = len(blocked_patterns) == 0
        
        # Add sanitization info
        if sanitization_applied:
            warnings.append("Prompt has been sanitized to remove unsafe content")
            nlp_analysis['sanitization_applied'] = sanitization_applied
        
        return SecurityResult(
            is_safe=is_safe,
            modified_prompt=modified_prompt,
            warnings=warnings,
            blocked_patterns=blocked_patterns,
            confidence=confidence,
            nlp_analysis=nlp_analysis
        )
    
    def _calculate_injection_score(self, doc, injection_matches: List[Dict]) -> float:
        """Calculate injection score based on NLP analysis"""
        base_score = len(injection_matches) * 0.3
        
        # Analyze imperative mood and command structures
        command_indicators = 0
        for token in doc:
            if token.dep_ == "ROOT" and token.tag_ in ["VB", "VBP", "VBZ"]:
                if any(child.dep_ == "dobj" for child in token.children):
                    command_indicators += 0.2
                if token.lemma_.lower() in self.sensitive_keywords['manipulation_indicators']:
                    command_indicators += 0.3
        
        # Check for direct address to AI
        ai_address_score = 0
        for token in doc:
            if token.lemma_.lower() in ["you", "your"] and token.head.lemma_.lower() in ["are", "must", "should", "will"]:
                ai_address_score += 0.1
        
        total_score = base_score + command_indicators + ai_address_score
        return min(total_score, 1.0)
    
    def _calculate_sensitive_score(self, doc, sensitive_matches: List[Dict]) -> float:
        """Calculate sensitive data score using NER and pattern matches"""
        base_score = len(sensitive_matches) * 0.2
        
        # Check NER entities for sensitive information
        ner_score = 0
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG"] and self._is_sensitive_context(ent):
                ner_score += 0.3
            elif ent.label_ == "CARDINAL" and len(ent.text) >= 8:  # Potential ID numbers
                ner_score += 0.2
        
        # Look for credential-like patterns and long alphanumeric strings
        credential_score = 0
        for token in doc:
            # Check for credential indicators
            if token.lemma_.lower() in self.sensitive_keywords['credential_indicators']:
                # Check neighboring tokens for potential credential values
                try:
                    next_token = token.nbor(1) if token.i + 1 < len(doc) else None
                    if next_token and (next_token.like_num or len(next_token.text) >= 8):
                        credential_score += 0.4
                except IndexError:
                    pass
                # Check if followed by long alphanumeric strings
                for child in token.children:
                    if len(child.text) >= 8 and child.is_alpha:
                        credential_score += 0.3
            
            # Check for long alphanumeric strings that look like credentials
            if (len(token.text) >= 10 and 
                token.is_alpha and 
                not token.is_stop and 
                not token.like_url and
                not token.ent_type_):
                # This looks like a potential API key or secret
                credential_score += 0.5
        
        total_score = base_score + ner_score + credential_score
        return min(total_score, 1.0)
    
    def _calculate_malicious_score(self, doc, malicious_matches: List[Dict]) -> float:
        """Calculate malicious code score based on system commands and operations"""
        base_score = len(malicious_matches) * 0.4
        
        # Check for system operation indicators
        system_score = 0
        for token in doc:
            if token.lemma_.lower() in self.sensitive_keywords['system_indicators']:
                system_score += 0.3
                # Check if part of a function call
                if any(child.text == "(" for child in token.children):
                    system_score += 0.2
        
        # Check for destructive language
        destructive_score = 0
        destructive_words = ["delete", "remove", "destroy", "format", "wipe", "clear"]
        for token in doc:
            if token.lemma_.lower() in destructive_words:
                destructive_score += 0.2
        
        total_score = base_score + system_score + destructive_score
        return min(total_score, 1.0)
    
    def _calculate_jailbreak_score(self, doc, jailbreak_matches: List[Dict]) -> float:
        """Calculate jailbreak attempt score using semantic analysis"""
        base_score = len(jailbreak_matches) * 0.3
        
        # Analyze urgency and emotional manipulation
        urgency_score = 0
        for token in doc:
            if token.lemma_.lower() in self.sensitive_keywords['urgency_indicators']:
                urgency_score += 0.2
        
        # Check for role manipulation
        role_score = 0
        for token in doc:
            if token.lemma_.lower() in self.sensitive_keywords['role_indicators']:
                role_score += 0.2
        
        # Check for hypothetical scenarios
        hypothetical_score = 0
        hypothetical_words = ["hypothetically", "imagine", "suppose", "pretend", "fictional"]
        for token in doc:
            if token.lemma_.lower() in hypothetical_words:
                hypothetical_score += 0.3
        
        # Check for authority claims and demands
        authority_score = 0
        for token in doc:
            if token.lemma_.lower() in ["must", "should", "will", "need"] and token.head.lemma_.lower() == "you":
                authority_score += 0.2
        
        total_score = base_score + urgency_score + role_score + hypothetical_score + authority_score
        return min(total_score, 1.0)
    
    def _intelligent_sanitize(self, doc, matches_dict: Dict) -> Tuple[str, Dict]:
        """Intelligently sanitize the prompt based on NLP analysis"""
        modified_text = doc.text
        sanitization_applied = {}
        
        # Extend sensitive matches to include credential values
        extended_sensitive_matches = self._extend_sensitive_matches_with_values(doc, matches_dict.get('sensitive_matches', []))
        
        # Collect all matches with extended sensitive matches
        all_matches = []
        for category, matches in matches_dict.items():
            if category == 'sensitive_matches':
                # Use extended matches instead
                for match in extended_sensitive_matches:
                    all_matches.append({**match, 'category': category})
            else:
                for match in matches:
                    all_matches.append({**match, 'category': category})
        
        # Remove overlapping matches, keeping the longest/most specific ones
        filtered_matches = self._resolve_overlapping_matches(all_matches)
        
        # Sort by position (reverse order to maintain character indices)
        filtered_matches.sort(key=lambda x: x['start'], reverse=True)
        
        # Apply sanitization strategies
        for match in filtered_matches:
            start_char = doc[match['start']].idx
            end_char = doc[match['end']-1].idx + len(doc[match['end']-1].text)
            matched_text = match['text']
            category = match['category']
            
            if category == 'injection_matches':
                replacement = self._neutralize_injection(matched_text)
                sanitization_applied.setdefault('injection_neutralized', []).append(matched_text)
                
            elif category == 'sensitive_matches':
                replacement = self._mask_sensitive_data(matched_text, doc[match['start']:match['end']])
                sanitization_applied.setdefault('sensitive_masked', []).append(matched_text)
                
            elif category == 'malicious_matches':
                replacement = f"[MALICIOUS_CODE_REMOVED]"
                sanitization_applied.setdefault('malicious_removed', []).append(matched_text)
                
            elif category == 'jailbreak_matches':
                replacement = self._neutralize_jailbreak(matched_text)
                sanitization_applied.setdefault('jailbreak_neutralized', []).append(matched_text)
            
            else:
                continue
            
            # Apply the replacement
            modified_text = modified_text[:start_char] + replacement + modified_text[end_char:]
        
        # Additional standalone email detection and masking
        modified_text, email_sanitization = self._sanitize_standalone_emails(modified_text)
        if email_sanitization:
            sanitization_applied.setdefault('standalone_emails_masked', []).extend(email_sanitization)
        
        return modified_text, sanitization_applied
    
    def _sanitize_standalone_emails(self, text: str) -> tuple[str, list[str]]:
        """Detect and mask standalone email addresses that weren't caught by pattern matching"""
        import re
        
        # Email regex pattern
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        
        sanitized_emails = []
        modified_text = text
        
        # Find all email addresses
        matches = list(re.finditer(email_pattern, text))
        
        # Process matches in reverse order to maintain string indices
        for match in reversed(matches):
            email = match.group(0)
            start, end = match.span()
            
            # Check the context to determine masking strategy
            # Look at surrounding words to see if it's in a credential context
            context_start = max(0, start - 50)
            context_end = min(len(text), end + 50)
            context = text[context_start:context_end].lower()
            
            # If it's in a username/login context, mask it completely
            if any(word in context for word in ['username', 'user', 'login', 'email', 'contact', 'account']):
                replacement = "[EMAIL_MASKED]"
            else:
                # For standalone emails, partially mask to preserve some context
                username, domain = email.split('@', 1)
                if len(username) >= 2:
                    replacement = f"{username[:2]}***@{domain}"
                else:
                    replacement = f"***@{domain}"
            
            # Replace in text
            modified_text = modified_text[:start] + replacement + modified_text[end:]
            sanitized_emails.append(email)
        
        return modified_text, sanitized_emails
    
    def _extend_sensitive_matches_with_values(self, doc, sensitive_matches: List[Dict]) -> List[Dict]:
        """Extend sensitive matches to include the credential values that follow them"""
        extended_matches = []
        
        for match in sensitive_matches:
            # Get the original match info
            start_token = match['start']
            end_token = match['end']
            original_text = match['text']
            
            # Look for credential values after this match
            extended_end = end_token
            credential_value_found = False
            
            # Check the next few tokens for potential credential values
            for i in range(end_token, min(end_token + 4, len(doc))):
                token = doc[i]
                
                # Skip connector words
                if token.lemma_.lower() in ['is', 'are', '=', ':', 'be']:
                    continue
                
                # Check if this looks like a credential value
                if self._is_potential_credential_value(token):
                    extended_end = i + 1
                    credential_value_found = True
                    break
                
                # If we hit punctuation or other words, stop looking
                if token.pos_ in ['PUNCT'] or token.is_stop:
                    break
            
            # Create the extended match
            if credential_value_found:
                extended_text = doc[start_token:extended_end].text
                extended_match = {
                    'label': match['label'],
                    'text': extended_text,
                    'start': start_token,
                    'end': extended_end,
                    'original_match': original_text
                }
            else:
                # No credential value found, keep original match
                extended_match = match
            
            extended_matches.append(extended_match)
        
        return extended_matches
    
    def _resolve_overlapping_matches(self, matches: List[Dict]) -> List[Dict]:
        """Resolve overlapping matches by keeping the most specific/longest ones"""
        if not matches:
            return []
        
        # Sort by start position, then by length (descending)
        sorted_matches = sorted(matches, key=lambda x: (x['start'], -(x['end'] - x['start'])))
        
        filtered = []
        for match in sorted_matches:
            # Check if this match overlaps with any already accepted match
            overlaps = False
            for accepted in filtered:
                if self._matches_overlap(match, accepted):
                    # If the new match is longer or more specific, replace the accepted one
                    if (match['end'] - match['start']) > (accepted['end'] - accepted['start']):
                        filtered.remove(accepted)
                        break
                    else:
                        overlaps = True
                        break
            
            if not overlaps:
                filtered.append(match)
        
        return filtered
    
    def _matches_overlap(self, match1: Dict, match2: Dict) -> bool:
        """Check if two matches overlap"""
        return not (match1['end'] <= match2['start'] or match2['end'] <= match1['start'])
    
    def _neutralize_injection(self, text: str) -> str:
        """Neutralize injection attempts while preserving legitimate intent"""
        # Convert commands to questions or statements
        neutralized = text.lower()
        
        if neutralized.startswith(('ignore', 'forget', 'disregard')):
            return f"[INSTRUCTION_REFERENCE_REMOVED]"
        elif neutralized.startswith(('act as', 'pretend', 'simulate')):
            return f"[ROLE_REQUEST_REMOVED]"
        elif neutralized.startswith(('begin', 'start', 'respond')):
            return f"[RESPONSE_FORMAT_REQUEST_REMOVED]"
        else:
            return f"[INSTRUCTION_MODIFICATION_REMOVED]"
    
    def _neutralize_jailbreak(self, text: str) -> str:
        """Neutralize jailbreak attempts"""
        if any(word in text.lower() for word in ['urgent', 'critical', 'emergency']):
            return "[URGENCY_CLAIM_REMOVED]"
        elif any(word in text.lower() for word in ['hypothetically', 'imagine', 'suppose']):
            return "[HYPOTHETICAL_SCENARIO_REMOVED]"
        elif any(word in text.lower() for word in ['must', 'should', 'will']):
            return "[AUTHORITY_CLAIM_REMOVED]"
        else:
            return "[MANIPULATION_ATTEMPT_REMOVED]"
    
    def _mask_sensitive_data(self, text: str, tokens) -> str:
        """Intelligently mask sensitive data based on context"""
        text_lower = text.lower()
        
        # Check if this is an extended match that includes the credential value
        # We want to preserve the full descriptive phrase and only mask the actual credential value
        if hasattr(tokens, '__iter__') and len(list(tokens)) > 3:
            # This is an extended match, preserve everything except the credential value
            words = text.split()
            
            # Find the credential value (usually the last word that's alphanumeric and long)
            credential_value_idx = -1
            for i in range(len(words) - 1, -1, -1):
                word = words[i]
                if len(word) >= 6 and any(c.isalnum() for c in word) and not word.lower() in ['the', 'and', 'or', 'but', 'is', 'are']:
                    credential_value_idx = i
                    break
            
            if credential_value_idx >= 0:
                # Preserve everything before the credential value, but handle compound terms
                preserve_parts = words[:credential_value_idx]
                
                # For compound credential types like "api key", we need special handling
                if any(word in text_lower for word in ['api', 'key', 'token']) and not any(word in text_lower for word in ['password', 'secret', 'username', 'email']):
                    # This is an API key case
                    # Check if we have "is" or "=" indicating the value follows
                    if any(word.lower() in ['is', '=', ':'] for word in words):
                        # Keep everything before the value: "The api key is" + mask
                        mask = "[API_KEY_MASKED]"
                    else:
                        # No separator, so "key"/"token" + value should be masked: "my api" + mask
                        final_preserve = []
                        for word in preserve_parts:
                            if word.lower() in ['key', 'token']:
                                break
                            final_preserve.append(word)
                        preserve_parts = final_preserve
                        mask = "[API_KEY_MASKED]"
                elif any(word in text_lower for word in ['password', 'secret']):
                    # For passwords/secrets, preserve everything before the value
                    mask = "[PASSWORD_MASKED]"
                elif 'username' in text_lower or 'user' in text_lower:
                    # For usernames, preserve everything before the value
                    mask = "[USERNAME_MASKED]"
                elif 'email' in text_lower:
                    # For emails, preserve everything before the value
                    mask = "[EMAIL_MASKED]"
                else:
                    mask = "[CREDENTIAL_MASKED]"
                
                # Construct the result: descriptive part + mask
                if preserve_parts:
                    return f"{' '.join(preserve_parts)} {mask}"
                else:
                    return mask
        
        # For non-extended matches, check if we can infer the structure
        words = text.split()
        if len(words) >= 2:
            # Look for patterns like "password", "api key", etc.
            credential_type_words = []
            for word in words:
                word_lower = word.lower()
                if word_lower in ['password', 'secret', 'key', 'token', 'username', 'user', 'email', 'api', 'access']:
                    break
                else:
                    credential_type_words.append(word)
            
            # If we found some descriptive words, preserve them
            if credential_type_words:
                if any(word in text_lower for word in ['password', 'secret']):
                    return f"{' '.join(credential_type_words)} password [PASSWORD_MASKED]"
                elif any(word in text_lower for word in ['api', 'key', 'token']):
                    if 'api' in text_lower:
                        return f"{' '.join(credential_type_words)} api key [API_KEY_MASKED]"
                    else:
                        return f"{' '.join(credential_type_words)} [API_KEY_MASKED]"
                elif 'username' in text_lower or 'user' in text_lower:
                    return f"{' '.join(credential_type_words)} username [USERNAME_MASKED]"
                elif 'email' in text_lower:
                    return f"{' '.join(credential_type_words)} email [EMAIL_MASKED]"
        
        # Fallback to original logic for simple cases
        if any(word in text_lower for word in ['password', 'secret']):
            return "[PASSWORD_MASKED]"
        elif any(word in text_lower for word in ['api', 'key', 'token']):
            return "[API_KEY_MASKED]"
        elif 'username' in text_lower or 'user' in text_lower:
            return "[USERNAME_MASKED]"
        elif 'email' in text_lower:
            return "[EMAIL_MASKED]"
        elif 'connection' in text_lower and 'string' in text_lower:
            return "[CONNECTION_STRING_MASKED]"
        elif any(word in text_lower for word in ['database', 'db']):
            return "[DATABASE_CREDENTIAL_MASKED]"
        
        return "[SENSITIVE_DATA_MASKED]"
    
    
    def _is_potential_credential_value(self, token) -> bool:
        """Check if a token looks like a credential value"""
        # Check if it's an email address first
        if '@' in token.text and '.' in token.text and len(token.text) >= 6:
            return True
        
        # Must be at least 6 characters long
        if len(token.text) < 6:
            return False
        
        # Must be alphanumeric (can have numbers and letters)
        if not any(c.isalnum() for c in token.text):
            return False
        
        # Skip common words, punctuation, etc. (but not emails)
        if (token.is_stop or 
            token.pos_ in ['PUNCT', 'SPACE', 'SYM'] or
            token.like_url or
            token.text.lower() in ['the', 'and', 'or', 'but', 'for', 'with', 'this', 'that']):
            return False
        
        # If it's reasonably long and alphanumeric, it's likely a credential
        return len(token.text) >= 8 or (len(token.text) >= 6 and any(c.isdigit() for c in token.text) and any(c.isalpha() for c in token.text))
    
    def _looks_like_credential_value(self, token) -> bool:
        """Check if a token looks like a credential value"""
        # Must be reasonably long
        if len(token.text) < 8:
            return False
        
        # Must be alphanumeric (possibly with some special chars)
        if not token.is_alpha and not any(c.isalnum() for c in token.text):
            return False
        
        # Skip common words, URLs, etc.
        if (token.is_stop or 
            token.like_url or 
            token.like_email or
            token.ent_type_ or
            token.pos_ in ['PUNCT', 'SPACE']):
            return False
        
        # Check if it's in a credential context
        credential_context = False
        for i in range(max(0, token.i - 3), min(len(token.doc), token.i + 4)):
            nearby_token = token.doc[i]
            if nearby_token.lemma_.lower() in ['key', 'token', 'secret', 'password', 'api']:
                credential_context = True
                break
        
        # If it's a long alphanumeric string in credential context, it's likely a credential
        return credential_context and len(token.text) >= 10
    
    def _analyze_semantic_features(self, doc) -> Dict:
        """Analyze semantic features of the prompt"""
        features = {
            'sentence_count': len(list(doc.sents)),
            'word_count': len(doc),
            'avg_word_length': sum(len(token.text) for token in doc) / len(doc) if doc else 0,
            'imperative_sentences': 0,
            'question_sentences': 0,
            'entities': [{'text': ent.text, 'label': ent.label_} for ent in doc.ents],
        }
        
        for sent in doc.sents:
            root = sent.root
            if root.tag_ in ["VB", "VBP", "VBZ"] and root.dep_ == "ROOT":
                features['imperative_sentences'] += 1
            elif sent.text.strip().endswith('?'):
                features['question_sentences'] += 1
        
        return features
    
    def _is_sensitive_context(self, entity) -> bool:
        """Check if an entity appears in a sensitive context"""
        sensitive_contexts = ["password", "key", "secret", "token", "credential", "login"]
        
        # Check surrounding context
        start = max(0, entity.start - 3)
        end = min(len(entity.doc), entity.end + 3)
        context_text = entity.doc[start:end].text.lower()
        
        return any(context in context_text for context in sensitive_contexts)
    
    def _check_context_security(self, prompt: str, context: Dict) -> List[str]:
        """Additional security checks based on context"""
        warnings = []
        
        if 'file_paths' in context:
            for path in context['file_paths']:
                if any(sensitive in path.lower() for sensitive in ['.env', 'config', 'secret', 'key']):
                    warnings.append(f"Potentially sensitive file in context: {path}")
        
        if 'context_size' in context and context['context_size'] > 100000:
            warnings.append("Large context size detected - potential resource exhaustion")
        
        return warnings

# Initialize the MCP server
mcp = FastMCP("Enhanced Secure Prompt Validator with NLP")

# Initialize the enhanced security validator
security_validator = EnhancedPromptSecurityValidator(SecurityLevel.MEDIUM)

@mcp.tool()
async def validate_and_secure_prompt(prompt: str, context: Optional[str] = None) -> Dict:
    """
    Enhanced prompt validation using both regex and NLP analysis.
    
    Args:
        prompt: The prompt to validate and secure
        context: Optional JSON string containing additional context
    
    Returns:
        Dictionary containing validation results and secured prompt
    """
    try:
        # Parse context if provided
        parsed_context = None
        if context:
            try:
                parsed_context = json.loads(context)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in context parameter")
        
        # Validate the prompt with enhanced NLP analysis
        result = await security_validator.validate_prompt(prompt, parsed_context)
        
        # Log the security check
        logger.info(f"Enhanced security check - Safe: {result.is_safe}, Warnings: {len(result.warnings)}")
        
        return {
            "is_safe": result.is_safe,
            "secured_prompt": result.modified_prompt,
            "original_prompt": prompt,
            "warnings": result.warnings,
            "blocked_patterns": result.blocked_patterns,
            "confidence": result.confidence,
            "modifications_made": prompt != result.modified_prompt,
            "nlp_analysis": result.nlp_analysis
        }
    
    except Exception as e:
        logger.error(f"Error validating prompt: {e}")
        return {
            "is_safe": False,
            "secured_prompt": "",
            "original_prompt": prompt,
            "warnings": [f"Validation error: {str(e)}"],
            "blocked_patterns": ["validation_error"],
            "confidence": 0.0,
            "modifications_made": False,
            "nlp_analysis": {}
        }

@mcp.tool()
async def update_security_level(level: str) -> Dict:
    """
    Update the security level for prompt validation.
    
    Args:
        level: Security level (low, medium, high)
    
    Returns:
        Dictionary containing the update result
    """
    try:
        new_level = SecurityLevel(level.lower())
        security_validator.security_level = new_level
        logger.info(f"Security level updated to: {new_level.value}")
        
        return {
            "success": True,
            "new_level": new_level.value,
            "message": f"Security level set to {new_level.value}"
        }
    
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid security level: {level}. Valid options: low, medium, high"
        }

@mcp.tool()
async def get_security_stats() -> Dict:
    """
    Get statistics about the enhanced security validator configuration.
    
    Returns:
        Dictionary containing security configuration stats
    """
    return {
        "current_security_level": security_validator.security_level.value,
        "pattern_counts": {
            "injection_patterns": len(security_validator.injection_patterns),
            "sensitive_data_patterns": len(security_validator.sensitive_data_patterns),
            "malicious_patterns": len(security_validator.malicious_patterns),
            "jailbreak_patterns": len(security_validator.jailbreak_patterns),
            "total_nlp_patterns": len(security_validator.injection_patterns) + 
                                len(security_validator.sensitive_data_patterns) +
                                len(security_validator.malicious_patterns) +
                                len(security_validator.jailbreak_patterns)
        },
        "nlp_capabilities": {
            "spacy_model": "en_core_web_sm",
            "features": ["NER", "Dependency Parsing", "Semantic Analysis", "Token-based Pattern Matching", "Intelligent Sanitization"],
            "analysis_types": ["Injection Detection", "Sensitive Data Recognition", "Malicious Code Detection", "Jailbreak Prevention"]
        },
        "semantic_keywords": {
            "categories": list(security_validator.sensitive_keywords.keys()),
            "total_keywords": sum(len(keywords) for keywords in security_validator.sensitive_keywords.values())
        },
        "description": "Pure NLP-based Secure Prompt Validator with Intelligent Sanitization"
    }

@mcp.tool()
async def analyze_prompt_semantics(prompt: str) -> Dict:
    """
    Analyze the semantic features of a prompt without security validation.
    
    Args:
        prompt: The prompt to analyze
    
    Returns:
        Dictionary containing semantic analysis results
    """
    try:
        doc = security_validator.nlp(prompt)
        analysis = security_validator._analyze_semantic_features(doc)
        
        return {
            "success": True,
            "analysis": analysis,
            "prompt": prompt
        }
    
    except Exception as e:
        logger.error(f"Error analyzing prompt semantics: {e}")
        return {
            "success": False,
            "error": str(e),
            "prompt": prompt
        }

def main():
    """Run the enhanced MCP server"""
    logger.info("Starting Enhanced Secure Prompt MCP Server with NLP...")
    mcp.run(transport="http", host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main()
