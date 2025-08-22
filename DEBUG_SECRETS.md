# Debugging OpenShift Secrets Issues

## Quick Troubleshooting Steps

### 1. Verify Secret Exists and is in Correct Namespace
```bash
# Check if secret exists
oc get secrets -n trend-analysis-using-ai--runtime-int | grep idea-hub-mcp-secrets

# Describe the secret to see its keys
oc describe secret idea-hub-mcp-secrets -n trend-analysis-using-ai--runtime-int

# Check if secret has the right data keys
oc get secret idea-hub-mcp-secrets -n trend-analysis-using-ai--runtime-int -o yaml
```

### 2. Verify Deployment Configuration
```bash
# Check deployment status
oc get deployment idea-hub-mcp-server -n trend-analysis-using-ai--runtime-int

# Check pod status and logs
oc get pods -n trend-analysis-using-ai--runtime-int -l app=idea-hub-mcp-server
oc logs deployment/idea-hub-mcp-server -n trend-analysis-using-ai--runtime-int

# Check environment variables in the pod
oc exec deployment/idea-hub-mcp-server -n trend-analysis-using-ai--runtime-int -- env | grep DATABASE
```

### 3. Check for Configuration Validation Errors

The application validates configuration at startup. Look for these errors in logs:
- `GOOGLE_API_KEY is required for AI features`
- `Database configuration incomplete - all DATABASE_* environment variables required`

### 4. Apply Secrets and Deployment

Make sure to apply in this order:
```bash
# 1. Apply secrets first
oc apply -f openshift/secrets.yaml

# 2. Then apply deployment
oc apply -f openshift/deployment.yaml

# 3. Check rollout status
oc rollout status deployment/idea-hub-mcp-server -n trend-analysis-using-ai--runtime-int
```

## Common Issues and Solutions

### Issue 1: Secret Not Found
**Error**: `secret "idea-hub-mcp-secrets" not found`
**Solution**: Apply the secrets.yaml file first

### Issue 2: Wrong Namespace
**Error**: Secret exists but pod can't access it
**Solution**: Ensure secret and deployment are in same namespace

### Issue 3: Invalid Base64 Encoding
**Error**: Configuration validation fails
**Solution**: Re-encode secrets properly:
```bash
echo -n "your_actual_value" | base64
```

### Issue 4: RBAC Permissions
**Error**: Pod cannot read secrets
**Solution**: Check service account has proper permissions

## Environment Variable Mapping

Your deployment maps these secret keys to environment variables:
- `database-host` → `DATABASE_HOST`
- `database-port` → `DATABASE_PORT`
- `database-name` → `DATABASE_NAME`
- `database-user` → `DATABASE_USER`
- `database-password` → `DATABASE_PASSWORD`
- `google-api-key` → `GOOGLE_API_KEY`

## Validation Script

You can also test the configuration locally:
```python
import os
import base64

# Simulate what Kubernetes does - decode the base64 values
secrets = {
    'DATABASE_HOST': base64.b64decode('ZGJwcm94eTAxLmRiYS0wMDEucHJvZC51cy1lYXN0LTEuYXdzLnJlZGhhdC5jb20=').decode('utf-8'),
    'DATABASE_PORT': base64.b64decode('MjA4MQ==').decode('utf-8'),
    'DATABASE_NAME': base64.b64decode('Z3NzX3ZlY3RvcmRi').decode('utf-8'),
    'DATABASE_USER': base64.b64decode('Z3NzX3ZlY3RvcmRiX3VzZXI=').decode('utf-8'),
    'DATABASE_PASSWORD': base64.b64decode('Q2s1OHp0bFZjVE9zNGg=').decode('utf-8'),
    'GOOGLE_API_KEY': base64.b64decode('QUl6YVN5Q3ZPN2xGaEtfaU85cHRZOWROZFNLMjR4dEJzeVMtRF9jSQ==').decode('utf-8')
}

# Set environment variables
for key, value in secrets.items():
    os.environ[key] = value

# Test configuration loading
from src.utils.config import MCPConfig
try:
    config = MCPConfig()
    print("✅ Configuration validation passed!")
    print(f"Database host: {config.database.host}")
    print(f"Database port: {config.database.port}")
    print(f"Database name: {config.database.database}")
    print(f"API key present: {'Yes' if config.ai.google_api_key else 'No'}")
except Exception as e:
    print(f"❌ Configuration validation failed: {e}")
```

## Next Steps

1. Run the verification commands above
2. Check the pod logs for specific error messages
3. If secrets are missing, apply them first
4. If validation fails, check the exact error message in logs

