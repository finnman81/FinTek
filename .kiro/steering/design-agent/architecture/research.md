---
inclusion: manual
---

# AWS Information Lookup Priority

When researching AWS services, APIs, or best practices, follow this priority order:

## 1. AWS Documentation MCP Server (First Choice)
Use `mcp_awslabsaws_documentation_mcp_server_*` tools for:
- Official AWS documentation pages
- API reference lookups
- Service-specific user guides
- SDK and CLI documentation
- AWS China region documentation (aws-cn partition)

Tools:
- `mcp_awslabsaws_documentation_mcp_server_search_documentation` - Search AWS docs
- `mcp_awslabsaws_documentation_mcp_server_read_documentation` - Fetch specific doc pages
- `mcp_awslabsaws_documentation_mcp_server_recommend` - Get related content

## 2. AWS Knowledge MCP Server (Second Choice)
Use `mcp_aws_knowledge_mcp_aws___*` tools when Documentation server doesn't have what you need, or for:
- What's New announcements and latest features
- AWS blog posts and Builder Center content
- Well-Architected guidance and architectural patterns
- Troubleshooting guides and error solutions
- Regional availability of APIs and CloudFormation resources
- CDK patterns, constructs, and code examples
- Amplify framework guidance

Tools:
- `mcp_aws_knowledge_mcp_aws___search_documentation` - Broader search with topic filtering
- `mcp_aws_knowledge_mcp_aws___read_documentation` - Fetch content
- `mcp_aws_knowledge_mcp_aws___recommend` - Related content
- `mcp_aws_knowledge_mcp_aws___list_regions` - AWS region info
- `mcp_aws_knowledge_mcp_aws___get_regional_availability` - Service/API availability by region

## 3. Web Search (Last Resort)
Use `remote_web_search` and `webFetch` only when:
- Information is not available in AWS documentation or knowledge sources
- You need third-party integrations or community solutions
- Looking for non-AWS specific information
- AWS sources returned no relevant results

## Decision Flow
1. Is this about AWS services, APIs, or official documentation? → Use Documentation Server
2. Need broader context (blogs, What's New, architecture patterns, troubleshooting)? → Use Knowledge Server
3. Still can't find it or need non-AWS info? → Use Web Search

## Important Notes
- Always cite sources when providing AWS information
- Prefer official AWS documentation over blog posts when both are available
- For code examples, check Knowledge Server's CDK/CloudFormation patterns first
