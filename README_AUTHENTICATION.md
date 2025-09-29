# Secure Prompt MCP Server with FastMCP Token Authentication

This implementation uses FastMCP's `TokenVerifier` class for robust, production-ready authentication with JWT tokens, static tokens for development, and HMAC for internal services.

## 🔐 Authentication Overview

The server supports three authentication modes:

1. **Static Tokens** (Development) - Predefined tokens for testing
2. **JWT with JWKS** (Production) - Industry-standard JWT with public key discovery
3. **HMAC** (Internal Services) - Symmetric key authentication for microservices

## 📁 File Structure

```
SecureMCP/
├── securenlpmcp_with_auth.py    # Main server with authentication
├── auth_config.py               # Authentication configuration module
├── test_auth_server.py          # Authentication test suite
├── requirements-auth.txt        # Dependencies with auth support
├── env.example                  # Environment configuration template
└── README_AUTHENTICATION.md    # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-auth.txt
python -m spacy download en_core_web_sm
```

### 2. Development Mode (Static Tokens)

```bash
# Set authentication mode
export FASTMCP_AUTH_MODE=static

# Start the server
python securenlpmcp_with_auth.py
```

### 3. Test Authentication

```bash
# Run the test suite
python test_auth_server.py

# Or test manually with curl
curl -H "Authorization: Bearer spv-admin-dev-2024-abc123" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "My password is secret123"}' \
     http://localhost:8001/validate_and_secure_prompt
```

## 🔑 Authentication Modes

### Development Mode (Static Tokens)

Perfect for development and testing. Uses predefined tokens with specific permissions.

**Configuration:**
```bash
export FASTMCP_AUTH_MODE=static
```

**Available Tokens:**
- `spv-admin-dev-2024-abc123` - Full admin access
- `spv-user-dev-2024-def456` - Standard user access  
- `spv-basic-dev-2024-ghi789` - Basic validation only
- `spv-prod-test-2024-jkl012` - Production testing
- `spv-service-2024-mno345` - Service account

### Production Mode (JWT with JWKS)

Industry-standard JWT authentication with automatic public key discovery.

**Configuration:**
```bash
export FASTMCP_AUTH_MODE=jwt
export JWT_JWKS_URI=https://your-auth.com/.well-known/jwks.json
export JWT_ISSUER=https://your-auth.com
export JWT_AUDIENCE=secure-prompt-mcp-api
```

**Features:**
- Automatic key rotation support
- Standard OAuth 2.0/OIDC compatibility
- Cryptographic signature verification
- Audience and issuer validation

### Internal Services Mode (HMAC)

Symmetric key authentication for trusted internal microservices.

**Configuration:**
```bash
export FASTMCP_AUTH_MODE=hmac
export JWT_SHARED_SECRET=your-32-character-minimum-shared-secret
export JWT_ISSUER=internal-auth-service
export JWT_AUDIENCE=secure-prompt-mcp-internal
export JWT_ALGORITHM=HS256
```

**Features:**
- Fast symmetric key validation
- Perfect for microservice architectures
- Shared secret management
- HMAC algorithms (HS256/384/512)

## 🛡️ Permission Scopes

The server uses scope-based authorization:

| Scope | Description | Required For |
|-------|-------------|--------------|
| `prompt:validate` | Validate and sanitize prompts | `validate_and_secure_prompt` |
| `prompt:analyze` | Analyze semantic features | `analyze_prompt_semantics` |
| `security:stats` | Access security statistics | `get_security_stats` |
| `security:admin` | Administrative access | `update_security_level` |

## 📊 API Endpoints

### 1. Validate and Secure Prompt
**Endpoint:** `POST /validate_and_secure_prompt`  
**Scope:** `prompt:validate`  
**Description:** Validates prompts for security threats and provides sanitized versions.

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "My password is secret123", "context": "{}"}' \
     http://localhost:8001/validate_and_secure_prompt
```

**Response:**
```json
{
  "is_safe": true,
  "secured_prompt": "My password is [PASSWORD_MASKED]",
  "original_prompt": "My password is secret123",
  "warnings": ["Sensitive data detected and sanitized"],
  "blocked_patterns": [],
  "confidence": 0.80,
  "modifications_made": true,
  "nlp_analysis": {...},
  "client_info": {
    "client_id": "admin@company.com",
    "authenticated": true,
    "scopes": ["prompt:validate", "prompt:analyze"]
  }
}
```

### 2. Analyze Prompt Semantics
**Endpoint:** `POST /analyze_prompt_semantics`  
**Scope:** `prompt:analyze`  
**Description:** Analyzes semantic features without security validation.

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "What is the weather today?"}' \
     http://localhost:8001/analyze_prompt_semantics
```

### 3. Get Security Statistics
**Endpoint:** `GET /get_security_stats`  
**Scope:** `security:stats`  
**Description:** Retrieves security configuration and statistics.

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8001/get_security_stats
```

### 4. Update Security Level
**Endpoint:** `POST /update_security_level`  
**Scope:** `security:admin`  
**Description:** Updates the security validation level.

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"level": "high"}' \
     http://localhost:8001/update_security_level
```

## 🧪 Testing

### Automated Test Suite

Run the comprehensive authentication test suite:

```bash
python test_auth_server.py
```

The test suite validates:
- ✅ Token authentication for all endpoints
- ✅ Scope-based authorization
- ✅ Permission denied scenarios
- ✅ Invalid token handling
- ✅ Client information extraction

### Manual Testing

Test different permission levels:

```bash
# Admin token (full access)
export TOKEN="spv-admin-dev-2024-abc123"

# User token (no admin access)
export TOKEN="spv-user-dev-2024-def456"

# Basic token (validation only)
export TOKEN="spv-basic-dev-2024-ghi789"

# Test validation
curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Test prompt"}' \
     http://localhost:8001/validate_and_secure_prompt
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FASTMCP_AUTH_MODE` | Authentication mode | `static` | No |
| `JWT_JWKS_URI` | JWKS endpoint URL | - | JWT mode |
| `JWT_ISSUER` | JWT issuer | - | JWT/HMAC mode |
| `JWT_AUDIENCE` | JWT audience | - | JWT/HMAC mode |
| `JWT_SHARED_SECRET` | HMAC shared secret | - | HMAC mode |
| `JWT_ALGORITHM` | HMAC algorithm | `HS256` | HMAC mode |

### Token Claims Structure

JWT tokens should include these claims:

```json
{
  "sub": "user-id-123",
  "client_id": "user@company.com",
  "scopes": ["prompt:validate", "prompt:analyze"],
  "iss": "https://your-auth.com",
  "aud": "secure-prompt-mcp-api",
  "exp": 1640995200,
  "iat": 1640908800
}
```

## 🚨 Security Considerations

### Token Security
- ✅ Use HTTPS in production
- ✅ Implement token expiration
- ✅ Rotate signing keys regularly
- ✅ Use strong shared secrets (32+ characters)
- ✅ Validate audience and issuer claims

### Scope Management
- ✅ Follow principle of least privilege
- ✅ Grant minimal required scopes
- ✅ Regular scope auditing
- ✅ Separate admin and user permissions

### Production Deployment
- ✅ Use JWT mode with JWKS
- ✅ Configure proper CORS policies
- ✅ Enable request logging
- ✅ Implement rate limiting
- ✅ Monitor authentication failures

## 🔄 Migration from Original Server

To migrate from the original `securenlpmcp.py`:

1. **Install authentication dependencies:**
   ```bash
   pip install -r requirements-auth.txt
   ```

2. **Update your client code:**
   ```python
   # Add Authorization header
   headers = {
       "Authorization": f"Bearer {your_token}",
       "Content-Type": "application/json"
   }
   ```

3. **Configure authentication mode:**
   ```bash
   export FASTMCP_AUTH_MODE=static  # for development
   ```

4. **Use the new server:**
   ```bash
   python securenlpmcp_with_auth.py
   ```

## 📝 Logging

The server provides comprehensive logging:

```
[INFO] Starting Enhanced Secure Prompt MCP Server with Token Authentication...
[INFO] Authentication verifier: StaticTokenVerifier
[INFO] Starting prompt validation for client: admin@company.com
[DEBUG] Input prompt length: 45 characters
[DEBUG] Client scopes: ['prompt:validate', 'prompt:analyze', 'security:admin']
[INFO] Validation complete - Safe: True, Confidence: 0.80
```

## 🆘 Troubleshooting

### Common Issues

**1. "Invalid token" errors:**
- Check token format and spelling
- Verify token is not expired
- Ensure correct Authorization header format

**2. "Insufficient permissions" errors:**
- Check token scopes
- Verify endpoint requirements
- Use appropriate token for the operation

**3. "Connection refused" errors:**
- Ensure server is running
- Check host and port configuration
- Verify firewall settings

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python securenlpmcp_with_auth.py
```

## 🎯 Next Steps

1. **Production Setup:**
   - Configure JWT with your identity provider
   - Set up HTTPS with proper certificates
   - Implement monitoring and alerting

2. **Advanced Features:**
   - Add Redis for rate limiting
   - Implement audit logging
   - Add metrics and monitoring

3. **Integration:**
   - Integrate with your existing auth system
   - Add client SDKs
   - Create deployment scripts

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Run the test suite to verify setup
3. Review server logs for error details
4. Ensure all dependencies are installed correctly

---

**🔐 Your Secure Prompt MCP Server is now protected with FastMCP Token Authentication!**
