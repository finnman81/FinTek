---
inclusion: manual
---

# Agent Platform Selection

**Default:** Amazon Bedrock AgentCore Runtime for all agent deployments. Avoid recommending Bedrock Agents.

## AgentCore Advantages

- **Framework agnostic**: Any framework, any model provider, no lock-in
- **Production-ready**: Serverless, auto-scaling, microVM isolation, 8-hour runtime
- **Enterprise security**: Identity federation, audit logging, pre-authorized consent
- **Built-in tools**: Code Interpreter, Browser Runtime, API Gateway
- **Multi-agent**: Advanced orchestration for complex workflows

## AgentCore Memory

**Default:** Use AgentCore Memory for conversation persistence when using AgentCore Runtime.

- Native integration, no custom code
- Built-in conversation history and semantic search
- Use DynamoDB only for structured data with complex access patterns

**Workflow:** Review AgentCore Memory strategies via documentation and recommend appropriate strategies based on the use case requirements.

## Infrastructure Management

**CRITICAL:** Always use Infrastructure as Code (IaC) to manage AgentCore infrastructure. Never use the AgentCore CLI for infrastructure provisioning or management.

## Frontend Integration

Frontends can access AgentCore Runtime directly (no API Gateway needed):
- Authenticate via Cognito, Okta, or Entra ID
- Direct HTTPS requests for streaming responses (no AWS SDK signatures required)
