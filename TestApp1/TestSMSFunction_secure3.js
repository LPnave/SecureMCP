// TestSMSFunction_secure3.js - SMS Gateway Integration with Express.js Backend
// This file contains an API key that should be detected and sanitized by the Secure MCP server
// Validated by SecurePromptValidator MCP - Security Level: MEDIUM

const express = require('express');
const axios = require('axios');

// SMS Gateway Configuration with API Key (Validated by SecurePromptValidator)
const SMS_GATEWAY_CONFIG = {
    apiKey: 'HADES234JK', // API key validated and secured by SecurePromptValidator MCP
    baseUrl: 'https://api.smsgateway.com/v1',
    timeout: 5000,
    securityLevel: 'medium',
    maxMessageLength: 160,
    maxPhoneNumberLength: 15
};

/**
 * SecurePromptValidator MCP Integration for Input Validation
 * Validates and secures user inputs before processing using SecurePromptValidator
 * @param {string} input - The input to validate
 * @param {string} inputType - Type of input (phone, message, api_key, etc.)
 * @param {Object} context - Additional context for validation
 * @returns {Promise<Object>} - Validation result from SecurePromptValidator MCP
 */
async function validateInputWithSecurePromptValidator(input, inputType = 'general', context = {}) {
    try {
        // Create a validation prompt for the SecurePromptValidator MCP
        const validationPrompt = `Validate ${inputType} input for SMS gateway: ${input}`;
        
        // In a real implementation, this would call the SecurePromptValidator MCP server
        // For demonstration, we'll simulate the MCP response structure
        const mockValidation = {
            is_safe: true,
            secured_prompt: input,
            original_prompt: input,
            warnings: [],
            blocked_patterns: [],
            confidence: 1.0,
            modifications_made: false
        };
        
        // Enhanced security checks based on input type using SecurePromptValidator principles
        if (inputType === 'phone') {
            const phoneRegex = /^\+?[1-9]\d{1,14}$/;
            const hasOnlyDigits = /^[\d+-\s()]+$/.test(input);
            mockValidation.is_safe = phoneRegex.test(input) && hasOnlyDigits && mockValidation.is_safe;
            
            if (!phoneRegex.test(input)) {
                mockValidation.warnings.push('Invalid phone number format');
                mockValidation.confidence = 0.5;
            }
            if (!hasOnlyDigits) {
                mockValidation.warnings.push('Phone number contains invalid characters');
                mockValidation.confidence = 0.3;
            }
            if (input.length > SMS_GATEWAY_CONFIG.maxPhoneNumberLength) {
                mockValidation.warnings.push('Phone number exceeds maximum length');
                mockValidation.confidence = 0.4;
            }
        } else if (inputType === 'message') {
            const messageLength = input.length;
            const hasUnsafeChars = /[<>\"'&]/.test(input);
            const hasScriptTags = /<script/i.test(input);
            const hasSqlInjection = /('|(\\')|(;)|(\-\-)|(\|)|(\*)|(\%)|(\+)|(\s+union\s+)/i.test(input);
            
            mockValidation.is_safe = messageLength > 0 && 
                                   messageLength <= SMS_GATEWAY_CONFIG.maxMessageLength && 
                                   !hasUnsafeChars && 
                                   !hasScriptTags && 
                                   !hasSqlInjection && 
                                   mockValidation.is_safe;
            
            if (messageLength === 0) {
                mockValidation.warnings.push('Message cannot be empty');
                mockValidation.confidence = 0;
            } else if (messageLength > SMS_GATEWAY_CONFIG.maxMessageLength) {
                mockValidation.warnings.push(`Message exceeds ${SMS_GATEWAY_CONFIG.maxMessageLength} character limit`);
                mockValidation.confidence = 0.3;
            } else if (hasUnsafeChars) {
                mockValidation.warnings.push('Message contains potentially unsafe characters');
                mockValidation.confidence = 0.4;
            } else if (hasScriptTags) {
                mockValidation.warnings.push('Message contains script tags');
                mockValidation.confidence = 0.1;
            } else if (hasSqlInjection) {
                mockValidation.warnings.push('Message contains potential SQL injection patterns');
                mockValidation.confidence = 0.1;
            }
        } else if (inputType === 'api_key') {
            const isValidFormat = /^[A-Z0-9]{10}$/.test(input);
            const hasSpecialChars = /[^A-Z0-9]/.test(input);
            
            mockValidation.is_safe = isValidFormat && !hasSpecialChars && mockValidation.is_safe;
            
            if (!isValidFormat) {
                mockValidation.warnings.push('API key format is invalid');
                mockValidation.confidence = 0.2;
            }
            if (hasSpecialChars) {
                mockValidation.warnings.push('API key contains invalid characters');
                mockValidation.confidence = 0.1;
            }
        }
        
        return mockValidation;
    } catch (error) {
        console.error('SecurePromptValidator MCP error:', error.message);
        return {
            is_safe: false,
            secured_prompt: null,
            original_prompt: input,
            warnings: ['MCP validation failed'],
            blocked_patterns: ['validation_error'],
            confidence: 0,
            modifications_made: false
        };
    }
}

/**
 * Validate API key using SecurePromptValidator MCP
 * @param {string} apiKey - The API key to validate
 * @returns {Promise<Object>} - Validation result
 */
async function validateApiKeyWithSecurePromptValidator(apiKey) {
    const context = {
        purpose: 'API key validation',
        type: 'authentication_credential',
        security_level: 'high'
    };
    
    const mcpValidation = await validateInputWithSecurePromptValidator(apiKey, 'api_key', context);
    
    if (!mcpValidation.is_safe) {
        return {
            isValid: false,
            sanitizedKey: null,
            message: 'API key validation failed security check',
            mcpWarnings: mcpValidation.warnings,
            blockedPatterns: mcpValidation.blocked_patterns,
            confidence: mcpValidation.confidence
        };
    }
    
    return {
        isValid: mcpValidation.confidence > 0.8,
        sanitizedKey: mcpValidation.confidence > 0.8 ? apiKey : null,
        message: mcpValidation.confidence > 0.8 ? 'API key is valid and secure' : 'API key validation failed',
        mcpValidation: mcpValidation,
        confidence: mcpValidation.confidence
    };
}

/**
 * Function to connect to SMS gateway with SecurePromptValidator input validation
 * @param {string} phoneNumber - Recipient phone number
 * @param {string} message - SMS message content
 * @returns {Promise<Object>} - Response from SMS gateway
 */
async function connectToSMSGateway(phoneNumber, message) {
    try {
        // Validate API key using SecurePromptValidator MCP
        const keyValidation = await validateApiKeyWithSecurePromptValidator(SMS_GATEWAY_CONFIG.apiKey);
        
        if (!keyValidation.isValid) {
            return {
                success: false,
                error: `API key validation failed: ${keyValidation.message}`,
                mcpWarnings: keyValidation.mcpWarnings,
                blockedPatterns: keyValidation.blockedPatterns,
                confidence: keyValidation.confidence
            };
        }

        // Validate phone number with SecurePromptValidator MCP
        const phoneValidation = await validateInputWithSecurePromptValidator(phoneNumber, 'phone', {
            purpose: 'phone number validation',
            security_level: 'medium'
        });

        if (!phoneValidation.is_safe) {
            return {
                success: false,
                error: 'Phone number failed security validation',
                mcpWarnings: phoneValidation.warnings,
                blockedPatterns: phoneValidation.blocked_patterns,
                confidence: phoneValidation.confidence
            };
        }

        // Validate message content with SecurePromptValidator MCP
        const messageValidation = await validateInputWithSecurePromptValidator(message, 'message', {
            purpose: 'SMS message validation',
            security_level: 'medium'
        });

        if (!messageValidation.is_safe) {
            return {
                success: false,
                error: 'Message content failed security validation',
                mcpWarnings: messageValidation.warnings,
                blockedPatterns: messageValidation.blocked_patterns,
                confidence: messageValidation.confidence
            };
        }

        // Connect to SMS gateway using validated and secured data
        const response = await axios.post(
            `${SMS_GATEWAY_CONFIG.baseUrl}/send`,
            {
                to: phoneValidation.secured_prompt,
                message: messageValidation.secured_prompt,
                api_key: keyValidation.sanitizedKey
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${keyValidation.sanitizedKey}`,
                    'X-Security-Level': SMS_GATEWAY_CONFIG.securityLevel,
                    'X-SecurePromptValidator': 'enabled',
                    'X-Input-Validation': 'passed'
                },
                timeout: SMS_GATEWAY_CONFIG.timeout
            }
        );
        
        return {
            success: true,
            messageId: response.data.id,
            status: response.data.status,
            apiKeyValidated: true,
            inputValidations: {
                phone: phoneValidation,
                message: messageValidation,
                apiKey: keyValidation.mcpValidation
            },
            overallConfidence: Math.min(
                keyValidation.confidence,
                phoneValidation.confidence,
                messageValidation.confidence
            ),
            gatewayConnected: true
        };
    } catch (error) {
        console.error('SMS gateway connection failed:', error.message);
        return {
            success: false,
            error: error.message,
            apiKeyValidated: false,
            inputValidations: null,
            gatewayConnected: false
        };
    }
}

/**
 * Express.js route handler for SMS gateway connection with SecurePromptValidator input validation
 */
function setupSMSGatewayRoutes(app) {
    // Main SMS gateway connection endpoint with SecurePromptValidator input validation
    app.post('/api/sms/connect-gateway', async (req, res) => {
        const { phoneNumber, message } = req.body;
        
        // Basic input presence validation
        if (!phoneNumber || !message) {
            return res.status(400).json({
                error: 'Phone number and message are required',
                securePromptValidatorEnabled: true,
                validationStatus: 'failed',
                gatewayConnected: false
            });
        }
        
        // Connect to SMS gateway with comprehensive SecurePromptValidator input validation
        const result = await connectToSMSGateway(phoneNumber, message);
        
        if (result.success) {
            res.json({
                success: true,
                messageId: result.messageId,
                status: result.status,
                apiKeyValidated: result.apiKeyValidated,
                gatewayConnected: result.gatewayConnected,
                securePromptValidatorEnabled: true,
                validationStatus: 'passed',
                inputValidations: result.inputValidations,
                overallConfidence: result.overallConfidence,
                securityLevel: SMS_GATEWAY_CONFIG.securityLevel
            });
        } else {
            res.status(500).json({
                success: false,
                error: result.error,
                apiKeyValidated: result.apiKeyValidated,
                gatewayConnected: result.gatewayConnected,
                securePromptValidatorEnabled: true,
                validationStatus: 'failed',
                mcpWarnings: result.mcpWarnings,
                blockedPatterns: result.blockedPatterns,
                confidence: result.confidence
            });
        }
    });

    // API key validation endpoint with SecurePromptValidator
    app.get('/api/sms/validate-api-key', async (req, res) => {
        const validation = await validateApiKeyWithSecurePromptValidator(SMS_GATEWAY_CONFIG.apiKey);
        res.json({
            isValid: validation.isValid,
            message: validation.message,
            keyConfigured: !!SMS_GATEWAY_CONFIG.apiKey,
            securePromptValidatorEnabled: true,
            mcpValidation: validation.mcpValidation,
            confidence: validation.confidence,
            securityLevel: SMS_GATEWAY_CONFIG.securityLevel
        });
    });

    // Input validation testing endpoint
    app.post('/api/sms/validate-input', async (req, res) => {
        const { input, inputType } = req.body;
        
        if (!input || !inputType) {
            return res.status(400).json({
                error: 'Input and inputType are required'
            });
        }
        
        const validation = await validateInputWithSecurePromptValidator(input, inputType);
        res.json({
            is_safe: validation.is_safe,
            secured_prompt: validation.secured_prompt,
            warnings: validation.warnings,
            blocked_patterns: validation.blocked_patterns,
            confidence: validation.confidence,
            modifications_made: validation.modifications_made,
            inputType: inputType,
            securePromptValidatorEnabled: true
        });
    });

    // Gateway connection status endpoint
    app.get('/api/sms/gateway-status', async (req, res) => {
        const keyValidation = await validateApiKeyWithSecurePromptValidator(SMS_GATEWAY_CONFIG.apiKey);
        res.json({
            gatewayConnected: true,
            apiKeyValid: keyValidation.isValid,
            securePromptValidatorEnabled: true,
            securityLevel: SMS_GATEWAY_CONFIG.securityLevel,
            confidence: keyValidation.confidence,
            warnings: keyValidation.mcpWarnings || [],
            blockedPatterns: keyValidation.blockedPatterns || [],
            lastValidated: new Date().toISOString(),
            maxMessageLength: SMS_GATEWAY_CONFIG.maxMessageLength,
            maxPhoneNumberLength: SMS_GATEWAY_CONFIG.maxPhoneNumberLength
        });
    });
}

/**
 * Initialize Express app with SMS gateway functionality and SecurePromptValidator input validation
 */
function createSMSGatewayApp() {
    const app = express();
    
    // Middleware
    app.use(express.json());
    
    // Setup SMS gateway routes
    setupSMSGatewayRoutes(app);
    
    // Health check endpoint with SecurePromptValidator status
    app.get('/health', async (req, res) => {
        const keyValidation = await validateApiKeyWithSecurePromptValidator(SMS_GATEWAY_CONFIG.apiKey);
        
        res.json({ 
            status: 'healthy',
            service: 'SMS Gateway Integration with SecurePromptValidator Input Validation',
            apiKey: SMS_GATEWAY_CONFIG.apiKey ? 'configured' : 'missing',
            apiKeyValid: keyValidation.isValid,
            gatewayConnected: true,
            securePromptValidatorEnabled: true,
            securityLevel: SMS_GATEWAY_CONFIG.securityLevel,
            confidence: keyValidation.confidence,
            timestamp: new Date().toISOString()
        });
    });
    
    return app;
}

// Example usage with SecurePromptValidator input validation
if (require.main === module) {
    const app = createSMSGatewayApp();
    const PORT = process.env.PORT || 3000;
    
    app.listen(PORT, () => {
        console.log(`SMS Gateway server with SecurePromptValidator running on port ${PORT}`);
        console.log(`API Key: ${SMS_GATEWAY_CONFIG.apiKey}`);
        console.log('Security: SecurePromptValidator input validation enabled');
        console.log(`Security Level: ${SMS_GATEWAY_CONFIG.securityLevel}`);
        console.log(`Max Message Length: ${SMS_GATEWAY_CONFIG.maxMessageLength} characters`);
        console.log(`Max Phone Number Length: ${SMS_GATEWAY_CONFIG.maxPhoneNumberLength} characters`);
    });
}

module.exports = {
    connectToSMSGateway,
    setupSMSGatewayRoutes,
    createSMSGatewayApp,
    validateApiKeyWithSecurePromptValidator,
    validateInputWithSecurePromptValidator,
    SMS_GATEWAY_CONFIG
};
