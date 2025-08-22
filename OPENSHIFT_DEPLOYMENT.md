# OpenShift Deployment Guide for Idea Hub MCP Server

This guide explains how to deploy the Idea Hub MCP Server on Red Hat's Managed Platform Plus (MPP) following Red Hat's internal deployment patterns.

## 🏗️ **Architecture Overview**

The deployment consists of:
- **MCP Server**: Model Context Protocol server for AI agent interactions
- **Web Interface**: HTTP API for testing and integration
- **Dual Transport**: Both STDIO (MCP) and HTTP (Web API)
- **Internal Routes**: Uses `shard: internal` for MPP compliance

## 📋 **Prerequisites**

1. **Access to Red Hat OpenShift MPP**
2. **Quay.io repository access** (`quay.io/rhn-support-nitsingh/`)
3. **Database access** (already configured)
4. **API keys** (Google Gemini)

## 🚀 **Deployment Steps**

### **Step 1: Build and Push Container Image**

```bash
# Build the container image
podman build --arch amd64 -t idea-hub-mcp-server:latest -f Containerfile .

# Tag for Quay
podman tag idea-hub-mcp-server:latest quay.io/rhn-support-nitsingh/idea-hub-mcp-server:latest

# Push to Quay
podman push quay.io/rhn-support-nitsingh/idea-hub-mcp-server:latest
```

### **Step 2: Deploy to OpenShift**

```bash
# Apply all resources
oc apply -k openshift/

# Or apply individually
oc apply -f openshift/secrets.yaml
oc apply -f openshift/deployment.yaml
oc apply -f openshift/service.yaml
oc apply -f openshift/route.yaml
```

### **Step 3: Verify Deployment**

```bash
# Check pod status
oc get pods -l app=idea-hub-mcp-server

# Check service
oc get svc idea-hub-mcp-server

# Check routes
oc get routes | grep idea-hub-mcp

# Check logs
oc logs -f deployment/idea-hub-mcp-server
```

## 🔗 **Access URLs**

After deployment, the service will be available at:

### **Web Interface (HTTP)**
- **URL**: `https://idea-hub-mcp-server.apps.int.spoke.preprod.us-east-1.aws.paas.redhat.com`
- **API Docs**: `https://idea-hub-mcp-server.apps.int.spoke.preprod.us-east-1.aws.paas.redhat.com/docs`
- **Health Check**: `https://idea-hub-mcp-server.apps.int.spoke.preprod.us-east-1.aws.paas.redhat.com/api/health`

### **MCP Server (HTTPS)**
- **URL**: `https://idea-hub-mcp-server-secure.apps.int.spoke.preprod.us-east-1.aws.paas.redhat.com`
- **Protocol**: MCP over HTTPS
- **Transport**: TLS-encrypted

## 🔧 **Configuration**

### **Environment Variables**
All sensitive configuration is stored in Kubernetes secrets:

```yaml
# Database Configuration
DATABASE_HOST: dbproxy01.dba-001.prod.us-east-1.aws.redhat.com
DATABASE_PORT: 2081
DATABASE_NAME: gss_vectordb
DATABASE_USER: gss_vectordb_user
DATABASE_PASSWORD: [from secret]

# AI Configuration
GOOGLE_API_KEY: [from secret]
```

### **Static Configuration**
Non-sensitive settings are hardcoded in the application:
- **Embedding Model**: all-MiniLM-L6-v2
- **LLM Model**: gemini-2.5-flash
- **Vector Dimension**: 384
- **Similarity Thresholds**: 0.7, 0.8

## 🔒 **Security Features**

1. **TLS Encryption**: Both HTTP and MCP endpoints use TLS
2. **Secret Management**: Credentials stored in Kubernetes secrets
3. **Internal Routes**: Uses `shard: internal` for MPP compliance
4. **Resource Limits**: CPU and memory limits configured
5. **Health Checks**: Liveness and readiness probes

## 📊 **Monitoring**

### **Health Endpoints**
- `/api/health`: Application health status
- `/api/embedding-stats`: Vector database statistics

### **Logging**
- **Level**: INFO (configurable via `PYTHON_LOG_LEVEL`)
- **Output**: Container stdout (collected by OpenShift)

### **Metrics**
- Pod resource usage
- Request/response times
- Database connection status

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **Database Connection Failed**
   ```bash
   # Check secrets
   oc get secret idea-hub-mcp-secrets -o yaml
   
   # Test database connectivity
   oc exec -it deployment/idea-hub-mcp-server -- curl http://localhost:8000/api/health
   ```

2. **Image Pull Errors**
   ```bash
   # Check image exists
   podman pull quay.io/rhn-support-nitsingh/idea-hub-mcp-server:latest
   
   # Verify deployment image reference
   oc describe deployment idea-hub-mcp-server
   ```

3. **Route Not Accessible**
   ```bash
   # Check route status
   oc get routes idea-hub-mcp-server
   
   # Test internal connectivity
   oc exec -it deployment/idea-hub-mcp-server -- curl http://localhost:8000/api/health
   ```

### **Debug Commands**

```bash
# Get pod logs
oc logs -f deployment/idea-hub-mcp-server

# Exec into pod
oc exec -it deployment/idea-hub-mcp-server -- /bin/bash

# Check environment variables
oc exec deployment/idea-hub-mcp-server -- env | grep -E "(DATABASE|GOOGLE)"

# Test MCP server directly
oc port-forward deployment/idea-hub-mcp-server 8000:8000
curl http://localhost:8000/api/health
```

## 🔄 **Updates**

### **Rolling Updates**
```bash
# Update image
oc patch deployment idea-hub-mcp-server -p '{"spec":{"template":{"spec":{"containers":[{"name":"idea-hub-mcp-server","image":"quay.io/rhn-support-nitsingh/idea-hub-mcp-server:v1.1"}]}}}}'

# Monitor rollout
oc rollout status deployment/idea-hub-mcp-server
```

### **Configuration Updates**
```bash
# Update secrets
oc patch secret idea-hub-mcp-secrets -p '{"data":{"google-api-key":"<new-base64-encoded-key>"}}'

# Restart deployment to pick up changes
oc rollout restart deployment/idea-hub-mcp-server
```

## 📈 **Scaling**

```bash
# Scale replicas
oc scale deployment idea-hub-mcp-server --replicas=3

# Auto-scaling (if needed)
oc autoscale deployment idea-hub-mcp-server --min=1 --max=5 --cpu-percent=80
```

## 🔗 **Integration with Idea Hub**

Once deployed, the MCP server can be integrated with your main Idea Hub application:

1. **Update Idea Hub configuration** to point to MCP server endpoints
2. **Replace custom function calls** with MCP tool calls
3. **Use HTTP API** for direct integration
4. **Use MCP protocol** for AI agent interactions

## 📝 **Notes**

- **Namespace**: Update `nitsingh-dev` to your actual namespace
- **Secrets**: Base64 encoded values in secrets.yaml (update as needed)
- **Routes**: Hostname patterns follow MPP requirements
- **Resources**: Adjust CPU/memory based on usage patterns


