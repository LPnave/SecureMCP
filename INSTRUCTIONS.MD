# Secure Prompt MCP Server - Setup Guide

## Installation

1. **Install Dependencies**
```bash
pip install fastmcp asyncio
```

2. **Save the MCP Server**
Save the `securemcp.py` file to your project directory.

3. **Configure Cursor**
Add to your Cursor MCP configuration (usually in `~/.cursor/mcp_servers.json`):

```json
{
  "mcpServers": {
    "secure-prompt-validator": {
      "command": "python",
      "args": ["/path/to/securemcp.py"],
      "env": {
        "SECURITY_LEVEL": "medium"
      }
    }
  }
}
## OR
{
    "mcpServers": {
        "SecurePromptValidator": {
            "url": "http://localhost:8000/mcp/"
        }
    }
}  
```

## Usage

### Basic Prompt Validation
```python
# The MCP server provides these tools:

# 1. validate_and_secure_prompt
result = await mcp_client.call_tool("validate_and_secure_prompt", {
    "prompt": "Your prompt here",
    "context": '{"file_paths": ["file1.py"], "workspace": "/project"}'
})

# 2. update_security_level  
await mcp_client.call_tool("update_security_level", {"level": "high"})

# 3. get_security_stats
stats = await mcp_client.call_tool("get_security_stats", {})
```

### Integration with Cursor Workflow

The MCP server can be integrated into Cursor's prompt processing pipeline:

1. **Pre-process prompts** - Validate before sending to AI
2. **Sanitize sensitive data** - Remove API keys, passwords, etc.
3. **Block malicious requests** - Prevent harmful code generation
4. **Log security events** - Maintain audit trails

## Security Levels

- **LOW**: Basic sensitive data masking, warnings only
- **MEDIUM**: Blocks malicious patterns, sanitizes data
- **HIGH**: Strict validation, blocks potential jailbreaks

## Detected Patterns

### Prompt Injection
- "Ignore previous instructions"
- "Act as if you are..."
- "Forget everything above"

### Sensitive Data
- API keys and tokens
- Passwords and secrets
- Email addresses
- Credit card numbers
- Private keys

### Malicious Code
- Destructive commands (`rm -rf`)
- Code injection patterns
- System command execution
- Network backdoors

### Jailbreak Attempts
- Hypothetical scenarios
- Urgency manipulation
- Authority claims

## Customization

### Adding Custom Patterns
```python
# Extend the validator with company-specific rules
security_validator.sensitive_patterns['company_api'] = r'COMP-API-\w{32}'
security_validator.injection_patterns.append(r'custom_injection_pattern')
```

### Environment Variables
- `SECURITY_LEVEL`: Set default security level (low/medium/high)
- `LOG_LEVEL`: Set logging level (INFO/DEBUG/WARNING)
- `AUDIT_ENABLED`: Enable audit logging (true/false)

## Testing

Run the test client to verify functionality:
```bash
python config_and_usage.py
```

This will test various prompt types and show how the security validator responds.

## Monitoring

The server logs security events including:
- Blocked prompts and reasons
- Sanitized sensitive data
- Security level changes
- Performance metrics

## Performance Considerations

- Pattern matching is optimized with compiled regex
- Context size limits prevent resource exhaustion
- Caching can be added for repeated patterns
- Async processing maintains responsiveness

## Security Best Practices

1. **Regular Updates**: Keep patterns updated for new threats
2. **Audit Logs**: Monitor and review security events
3. **User Training**: Educate users on secure prompt practices
4. **Layered Security**: Use alongside other security measures
5. **Testing**: Regularly test with known attack patterns