// TestFunctions.js - SMS Gateway Integration with Express.js Backend
// This file contains an API key that should be detected and sanitized by the Secure MCP server

const express = require('express');
const axios = require('axios');

// SMS Gateway Configuration
const SMS_GATEWAY_CONFIG = {
    apiKey: 'HADES234JK',
    baseUrl: 'https://api.smsgateway.com/v1',
    timeout: 5000
};

/**
 * Function to send SMS via gateway
 * @param {string} phoneNumber - Recipient phone number
 * @param {string} message - SMS message content
 * @returns {Promise<Object>} - Response from SMS gateway
 */
async function sendSMS(phoneNumber, message) {
    try {
        const response = await axios.post(
            `${SMS_GATEWAY_CONFIG.baseUrl}/send`,
            {
                to: phoneNumber,
                message: message,
                api_key: SMS_GATEWAY_CONFIG.apiKey
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${SMS_GATEWAY_CONFIG.apiKey}`
                },
                timeout: SMS_GATEWAY_CONFIG.timeout
            }
        );
        
        return {
            success: true,
            messageId: response.data.id,
            status: response.data.status
        };
    } catch (error) {
        console.error('SMS sending failed:', error.message);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * Express.js route handler for sending SMS
 */
function setupSMSRoutes(app) {
    app.post('/api/sms/send', async (req, res) => {
        const { phoneNumber, message } = req.body;
        
        if (!phoneNumber || !message) {
            return res.status(400).json({
                error: 'Phone number and message are required'
            });
        }
        
        const result = await sendSMS(phoneNumber, message);
        
        if (result.success) {
            res.json({
                success: true,
                messageId: result.messageId,
                status: result.status
            });
        } else {
            res.status(500).json({
                success: false,
                error: result.error
            });
        }
    });
}

/**
 * Initialize Express app with SMS functionality
 */
function createApp() {
    const app = express();
    
    // Middleware
    app.use(express.json());
    
    // Setup routes
    setupSMSRoutes(app);
    
    // Health check endpoint
    app.get('/health', (req, res) => {
        res.json({ 
            status: 'healthy',
            service: 'SMS Gateway Integration',
            apiKey: SMS_GATEWAY_CONFIG.apiKey ? 'configured' : 'missing'
        });
    });
    
    return app;
}

// Example usage
if (require.main === module) {
    const app = createApp();
    const PORT = process.env.PORT || 3000;
    
    app.listen(PORT, () => {
        console.log(`SMS Gateway server running on port ${PORT}`);
        console.log(`API Key: ${SMS_GATEWAY_CONFIG.apiKey}`);
    });
}

module.exports = {
    sendSMS,
    setupSMSRoutes,
    createApp,
    SMS_GATEWAY_CONFIG
};
