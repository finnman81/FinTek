---
inclusion: manual
---

# Foundation Model Selection

## Critical Rule
**NEVER rely on prior knowledge.** Always research current catalog. Select newest GA version found—if research shows Claude 4.x available, recommending Claude 3.x is PROHIBITED.

## Mandatory Research (NO EXCEPTIONS)

Before selecting ANY model, execute:
```
mcp_aws_knowledge_mcp_server_search_documentation("Amazon Bedrock supported foundation models")
mcp_aws_knowledge_mcp_server_search_documentation("Claude models Amazon Bedrock latest")
remote_web_search("Amazon Bedrock Claude 4 availability [current year]")
```

**Skipping research and defaulting to older versions = INVALID design.**

## Workflow

1. **Discover** - Search AWS docs for current Bedrock catalog + "[model family] latest version Bedrock [current year]"
2. **Verify currency** - Confirm latest GA (Claude 4 Sonnet/Opus likely available; check Nova, others)
3. **Research capabilities** - Context window, output limits, tool use, vision, streaming
4. **Check pricing** - Input/output token costs, provisioned throughput
5. **Verify region** - `get_regional_availability` for target region
6. **Map requirements** - Match context, latency, volume, budget

## Model ID Lookup (REQUIRED)

**Never hardcode model IDs.** After selecting, search:
```
mcp_aws_knowledge_mcp_server_search_documentation("Amazon Bedrock model IDs [model name]")
mcp_aws_knowledge_mcp_server_search_documentation("Amazon Bedrock inference profiles [model name]")
mcp_aws_knowledge_mcp_server_search_documentation("Amazon Bedrock cross-region inference")
```

### Inference Profiles
- **Cross-region (preferred)**: Auto-routes for availability
- **Global**: `global.<provider>.<model>` - all commercial regions
- **Regional**: `<region-prefix>.<provider>.<model>` - specific region group
- **Base model IDs**: Direct access, no cross-region routing

**Prefer `global.*` profiles unless data residency requires specific region.**

## Selection Criteria

| Factor | Check |
|--------|-------|
| Currency | Latest GA? (NOT 3.5 if 4 exists) |
| Context | Fits longest input? |
| Output | Supports longest response? |
| Latency | Meets performance? |
| Cost | Within budget at volume? |
| Region | Available in target? |

## ADR Requirements

Document: Model + exact version, Bedrock model/inference profile ID, research date + source URLs, evidence newer versions checked, alternatives compared, cost projection, regional availability.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Defaulting to Claude 3.5 | Search for latest Claude on Bedrock |
| Using versions from memory | Verify current naming/versions |
| Assuming availability | Check regional availability |
| No cost projection | Calculate token costs |
| Skipping research | Research MANDATORY every time |
| Omitting model ID | Include Bedrock model/inference profile ID |

## Validation Checklist

- [ ] Searched AWS docs for current catalog
- [ ] Searched for latest version of model family
- [ ] Confirmed no newer version exists
- [ ] Documented search results with URLs
- [ ] Included Bedrock model/inference profile ID
- [ ] Checked regional availability
- [ ] Calculated cost estimate
