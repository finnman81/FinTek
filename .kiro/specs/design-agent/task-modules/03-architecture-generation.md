# Stage 3: Architecture Generation

**Objective**: Generate production-ready architecture (diagrams, specs, ADRs, validation) through research → design → validate.
**Execution**: Autonomous - complete all tasks without stopping. Make decisions based on research, document assumptions in ADRs.
**Dependencies**: 
- Requirements generation marked as complete in `.workflow-state/design-handoff.md`
- `.kiro/steering/design-agent/core-methodology/architecture-generation-guide.md`
- `.kiro/steering/design-agent/core-methodology/architecture-integration-validation-guide.md`
- `.kiro/steering/design-agent/core-methodology/system-architecture-template.md`
- `.kiro/steering/design-agent/architecture/research.md`

## Prerequisites

- Requirements complete in `.workflow-state/design-handoff.md`
- Customer context in `.workflow-state/customer-context.md`
- MCP tools: AWS Knowledge MCP server, web search

## Critical Rules

| Rule | Details |
|------|---------|
| ADRs | Separate files: `architecture/architecture-decision-records/ADR-XXX-*.md` |
| Diagrams | Mermaid format only |
| system-architecture.md | High-level only (no code, no ADRs, no detailed specs) |
| Content separation | Data → data-architecture.md (validate need in Phase 2.3), APIs → api-specifications.md (validate need in Phase 2.4) |
| Research | Write findings to file immediately after each domain |
| Context management | Max 5-10 searches per domain; summarize don't quote |

## Output Structure

**Specification Package Structure** (within `specification-package-iteration-X/architecture/`):
```
specification-package-iteration-X/
└── architecture/
    ├── system-architecture.md
    └── technical-specifications.md
```

**Supplement Material Structure** (within `supplement-material/architecture-context/`):
```
supplement-material/
└── architecture-context/
    ├── research/
    │   ├── [domain-1]-research.md
    │   └── [domain-2]-research.md
    ├── architecture-decision-records/
    │   ├── ADR-001-*.md
    │   └── ADR-002-*.md
    ├── data-architecture.md              # Only if designing data models (validated in Task 3.2.4)
    ├── api-specifications.md             # Only if defining API contracts (validated in Task 3.2.5)
    ├── architecture-requirements-traceability.md
    └── architecture-integration-validation.md
```

---

## Task 3.1: Requirements & Domain Research

### Task 3.1.2 Decompose into Research Domains

**Domain identification criteria:**
- **Clustering**: Group requirements by technical concern (data, integrations, compute, user interaction, etc.)
- **Decision density**: Areas with multiple technology choices or complex trade-offs warrant their own domain
- **Cross-cutting concerns**: Security/compliance may need a dedicated domain if requirements are complex
- **Simplicity**: Merge straightforward requirements into a single domain; prefer fewer domains to reduce context overhead

For each domain, define: focus area, key questions, constraints, out-of-scope items.

### Task 3.1.3 Load Steering Documents (MANDATORY)

**⛔ HARD GATE - DO NOT PROCEED WITHOUT COMPLETING THIS STEP**

**MANDATORY - Read these files before proceeding to research:**

1. **ALWAYS read**: `.kiro/steering/design-agent/architecture/research.md` - defines research tools priority order
2. **If AI agents/agentic workflows**: `.kiro/steering/design-agent/architecture/agentic-platform-selection-guide.md`
3. **If LLMs/generative AI/foundation models**: `.kiro/steering/design-agent/architecture/foundational-model-selection-guide.md`

**DO NOT search for these files. Read them directly using the paths above.**

### Task 3.1.4 Execute Domain Research

Execute MCP searches following the tool priority from research.md:
1. AWS Documentation MCP Server
2. AWS Knowledge MCP Server  
3. Web Search

**Context Window Management Rules:**

| Rule | Rationale |
|------|-----------|
| Max 5-10 searches per domain | Prevents context bloat |
| Write to file after each domain | Offloads context to disk |
| Summarize each research result | Avoids copying full docs |
| Use search snippets first | Only read full docs if snippet insufficient |

**Example Research Questions by Domain:**

| Domain | Example Questions |
|--------|-------------------|
| AI/Agent | "Bedrock Agents vs AgentCore patterns", "Strands SDK integration", "Agent memory management AWS" |
| Data | "DynamoDB single table design", "S3 event-driven patterns", "Aurora Serverless v2 patterns" |
| API | "API Gateway Lambda authorizer", "WebSocket API patterns", "GraphQL AppSync patterns" |
| Security | "Cognito user pool patterns", "KMS encryption serverless", "IAM least privilege Lambda" |
| Integration | "EventBridge integration patterns", "Step Functions orchestration", "SQS vs SNS patterns" |

---

## Task 3.2: Architecture Design

Load all research files and validate scope against stated requirements. Design system architecture with high-level components (frontend, API, compute, data, integration, security, monitoring). Design component specifications with interfaces and data models. Design data architecture with access patterns and security. Design API specifications with endpoints and contracts (if applicable). Design integration patterns for all integration points. Create Mermaid diagrams for system and component architecture.

**Specialized Documentation Validation**: During Tasks 3.2.4 and 3.2.5, apply the validation framework from `.kiro/steering/design-agent/architecture/data-and-api-generation-guide.md` to determine whether to create separate data-architecture.md or api-specifications.md files. For each potential file, ask: (1) Are you making design decisions or using existing services? (2) Is this design-level or usage-level work? (3) Are there multiple approaches to evaluate? If ANY answer suggests integration, document the decision in architecture-integration-validation.md and include details in technical-specifications.md instead. If ALL answers suggest separate files, query AWS Knowledge MCP for best practices and create comprehensive specialized documentation.

**Output**: `architecture/system-architecture.md`, `architecture/technical-specifications.md`, `supplement-material/architecture-context/data-architecture.md` (conditional), `supplement-material/architecture-context/api-specifications.md` (conditional)

## Task 3.3: Gap Analysis & Targeted Research

### Task 3.3.1 Identify Gaps

**Gap categories:**
- **Critical**: Version mismatches, steering violations, research contradictions
- **High**: Missing service details, unvalidated assumptions, integration specifics
- **Medium**: Regional availability, service limits
- **Low**: Documentation polish, diagram completeness

### Task 3.3.2 Execute Targeted Research

Conduct focused research to address identified gaps. Use specific queries for critical and high-priority gaps, validate assumptions with targeted searches, and perform version checks for all technologies.

### Task 3.3.3 Update Documents

Apply corrections from gap analysis to all architecture documents. Add validation notes to research files documenting what was verified and any remaining uncertainties.

### Task 3.3.4 Service-to-Requirement Mapping

Create explicit traceability mapping functional requirements to services/components and non-functional requirements to patterns/decisions. Document in architecture-requirements-traceability.md.

---

## Task 3.4: Architecture Decision Documentation

### Task 3.4.1 Identify Decisions

**Reference**: See `.kiro/steering/design-agent/core-methodology/architecture-generation-guide.md` for ADR-worthy decision criteria and required categories.

**CRITICAL**: Every AWS service in the architecture MUST trace to either:
- An explicit ADR documenting the selection rationale, OR
- A stated requirement that mandates a specific service

### Task 3.4.2 Create ADRs

**Required ADR sections:** Status, Context, Decision, Consequences, Alternatives (min 2), Rationale, Research Sources, Related Decisions

### Task 3.4.3 ADR Coverage Validation

Verify comprehensive ADR coverage by cross-referencing all technology choices against existing ADRs. Ensure no "orphan services" exist without either ADR documentation or explicit requirement justification.

---

## Task 3.5: Validation & Quality Assessment

### Task 3.5.1 Load Validation Framework

Load the architecture integration validation guide to establish validation criteria and scoring methodology for comprehensive quality assessment.

### Task 3.5.2 Validate Requirements Coverage

Verify each functional and non-functional requirement has an architectural solution. Calculate coverage percentages with targets of 95%+ for requirements and 100% for user stories.

### Task 3.5.3 Validate Component Integration

Create interface compatibility matrix to verify protocol, data format, and authentication compatibility between all components. Validate end-to-end data flows.

### Task 3.5.4 Analyze Service Limits

Inventory all AWS services, document soft vs hard limits, estimate POC and production usage, identify high-risk services (>80% of limit), and develop mitigation strategies.

### Task 3.5.5 Assess Technical Feasibility

Validate technology maturity (GA/Preview/Emerging), assess team expertise and learning curve, evaluate implementation complexity, and identify risks with mitigations.

### Task 3.5.6 Review Documentation

Verify all required files exist and are complete, ADRs follow naming conventions, every AWS service has ADR or requirement justification, and system-architecture.md follows template.

### Task 3.5.7 Calculate Quality Score

| Category | Weight |
|----------|--------|
| Requirements Coverage | 30% |
| Component Integration | 25% |
| Service Limits | 15% |
| Technical Feasibility | 15% |
| Documentation | 15% |

**Thresholds**: 90-100 Excellent, 85-89 Good, 70-84 Conditional, <70 Failed

### Task 3.5.8 Generate Validation Report

Create comprehensive validation report including executive summary, completeness assessment, integration analysis, service limits review, feasibility assessment, documentation review, quality scoring, and recommendations.

---

## Task 3.6: Workflow Completion

Confirm all deliverables are created per output structure, update design-handoff.md to mark architecture generation complete, and inform user that architecture generation is ready for holistic quality assessment.

---

## Error Handling

| Error | Resolution |
|-------|------------|
| MCP unavailable | Use web search as fallback |
| Web search unavailable | Use MCP only, note gaps |
| Research insufficient | Add to Task 3.3 targeted research list |
| Conflicting sources | Prioritize official AWS docs, document conflict in ADR |
| Context getting large | Write to file immediately, summarize more aggressively |
| Coverage <95% | Targeted research → update → recalculate |
| Score <85 | Address issues by priority → recalculate |
| Context loss | Check design-handoff.md, re-read research files, resume |

---

## Task Checklist

**MANDATORY**: Complete each checkbox in order. Do not skip tasks.

- [ ] **Task 3.1: Requirements & Domain Research**
  - [ ] **Task 3.1.1 Analyze Requirements**
    - [ ] Read functional + non-functional requirements completely
    - [ ] Read customer context from `.workflow-state/customer-context.md`
    - [ ] Identify mode (POC/Production/Compliance/Budget-Conscious)
    - [ ] Extract: scalability, performance, security, availability, integration, compliance, budget constraints
  - [ ] **Task 3.1.2 Decompose into Research Domains**
    - [ ] Group requirements by technical concern using domain identification criteria above
    - [ ] Define for each domain: focus area, key questions, constraints, out-of-scope items
  - [ ] **Task 3.1.3 Load Steering Documents (MANDATORY)**
    - [ ] Read `.kiro/steering/design-agent/architecture/research.md` - DO NOT SKIP
    - [ ] If project involves AI agents/agentic workflows → read `.kiro/steering/design-agent/architecture/agentic-platform-selection-guide.md`
    - [ ] If project involves LLMs/generative AI/foundation models → read `.kiro/steering/design-agent/architecture/foundational-model-selection-guide.md`
    - [ ] Extract from loaded documents: tool priority order, preferred technologies, constraints, anti-patterns
  - [ ] **Task 3.1.4 Execute Domain Research**
    - [ ] Verify you have loaded `.kiro/steering/design-agent/architecture/research.md`
    - [ ] For each domain, formulate targeted research questions (see examples in ### Task 3.1.4 Execute Domain Research)
    - [ ] Execute MCP searches following tool priority from research.md: AWS Documentation MCP → AWS Knowledge MCP → Web Search (max 5-10 searches per domain)
    - [ ] Write findings to `supplement-material/architecture-context/research/[domain-name]-research.md` BEFORE moving to next domain
    - [ ] Include steering document constraints in research files
    - [ ] Validate findings align with steering constraints; flag conflicts for ADRs
  - [ ] **Task 3.1.5 Simplicity Gate**
    - [ ] Filter suggestions: For each research finding, ask "Which specific requirement (FR-XXX, NFR-XXX, user story) does this address?" INCLUDE only if direct requirement match, EXCLUDE if justified by "best practice" or "nice to have"
    - [ ] Verify "Out of Scope" items not addressed: Check requirements document for excluded items, remove any architecture components that address out-of-scope functionality
    - [ ] Verify every service maps to a stated requirement: List all AWS services from research, identify specific requirement each addresses, remove services without clear requirement justification
    - [ ] Verify single API pattern: If research suggests multiple API types (REST, GraphQL, WebSocket), select ONE based on primary use case, remove others unless explicitly required
    - [ ] Verify no RAG unless explicitly requested

- [ ] **Task 3.2: Architecture Design**
  - [ ] **Task 3.2.1 Load Research & Validate Scope**
    - [ ] Read ALL files from `supplement-material/architecture-context/research/`
    - [ ] Re-read original requirements
    - [ ] For each component ask: "Which stated requirement does this address?"
    - [ ] Remove components justified only by "best practice" (Only applicable for POC projects)
  - [ ] **Task 3.2.2 System Architecture Generation**
    - [ ] Load template: `.kiro/steering/design-agent/core-methodology/system-architecture-template.md`
    - [ ] Follow ALL template sections exactly
    - [ ] Create Mermaid diagrams (context, component, sequence, security)
    - [ ] Document in `architecture/system-architecture.md`
  - [ ] **Task 3.2.3 Component Specifications Generation **
    - [ ] For each component: purpose, services, interfaces, dependencies, security controls, performance
    - [ ] Document in `architecture/technical-specifications.md`
    - [ ] Do NOT include data schemas or API formats (reference other files)
  - [ ] **Task 3.2.4 Data Architecture (if applicable)**
    - [ ] Define data models, access patterns, indexing, lifecycle, security
    - [ ] Document in `supplement-material/architecture-context/data-architecture.md`
  - [ ] **Task 3.2.5 API Specifications (if applicable)**
    - [ ] Define endpoints, request/response schemas, auth, rate limiting, error handling
    - [ ] Document in `supplement-material/architecture-context/api-specifications.md`
  - [ ] **Task 3.2.6 Integration Patterns**
    - [ ] Define patterns (sync/async/batch/streaming), protocols, auth, error handling
    - [ ] High-level in system-architecture.md, details in technical-specifications.md

- [ ] **Task 3.3: Gap Analysis & Targeted Research**
  - [ ] **Task 3.3.1 Identify Gaps**
    - [ ] Review all architecture documents for completeness
    - [ ] Categorize gaps as Critical/High/Medium/Low (see categories above)
  - [ ] **Task 3.3.2 Execute Targeted Research**
    - [ ] For Critical/High gaps: research with specific queries, update documents immediately
    - [ ] Validate assumptions with targeted searches
    - [ ] Version checks: search "[technology] latest version [current year]"
  - [ ] **Task 3.3.3 Update Documents**
    - [ ] Apply all corrections from gap analysis
    - [ ] Add "Validation Notes" to research files
  - [ ] **Task 3.3.4 Service-to-Requirement Mapping**
    - [ ] Create mapping: FR → services/components, NFR → patterns/decisions
    - [ ] Document in `supplement-material/architecture-context/architecture-requirements-traceability.md`

- [ ] **Task 3.4: Architecture Decision Documentation**
  - [ ] **Task 3.4.1 Identify Decisions**
    - [ ] Read ADR criteria from `.kiro/steering/design-agent/core-methodology/architecture-generation-guide.md`
    - [ ] List ALL AWS services from system-architecture.md
    - [ ] For EACH service, verify: explicit ADR exists OR requirement mandates it
    - [ ] Flag any service without ADR or requirement justification
  - [ ] **Task 3.4.2 Create ADRs**
    - [ ] Create `supplement-material/architecture-context/architecture-decision-records/` subfolder
    - [ ] For each decision: `ADR-XXX-[title].md` with required sections (see above)
    - [ ] Ensure all ADRs have research citations
    - [ ] Ensure all ADRs document minimum 2 alternatives considered
  - [ ] **Task 3.4.3 ADR Coverage Validation**
    - [ ] Cross-reference: Technology Summary table → ADR exists for each entry
    - [ ] Cross-reference: Component specifications → hosting/deployment decisions have ADRs
    - [ ] Verify no "orphan services" (services without ADR or requirement traceability)

- [ ] **Task 3.5: Validation & Quality Assessment**
  - [ ] **Task 3.5.1 Load Validation Framework**
    - [ ] Read `.kiro/steering/design-agent/core-methodology/architecture-integration-validation-guide.md`
  - [ ] **Task 3.5.2 Validate Requirements Coverage**
    - [ ] Verify each FR/NFR has architectural solution
    - [ ] Calculate coverage % (target: FR 95%+, NFR 95%+, user stories 100%)
  - [ ] **Task 3.5.3 Validate Component Integration**
    - [ ] Create interface compatibility matrix
    - [ ] Verify protocol, data format, auth compatibility
    - [ ] Validate data flows
  - [ ] **Task 3.5.4 Analyze Service Limits**
    - [ ] Inventory all services, document soft vs hard limits
    - [ ] Estimate POC and production usage
    - [ ] Identify high-risk services (>80% of limit)
    - [ ] Develop mitigation strategies
  - [ ] **Task 3.5.5 Assess Technical Feasibility**
    - [ ] Validate technology maturity (GA/Preview/Emerging)
    - [ ] Assess team expertise, learning curve
    - [ ] Assess implementation complexity
    - [ ] Identify risks and mitigations
  - [ ] **Task 3.5.6 Review Documentation**
    - [ ] Verify all required files exist and are complete
    - [ ] Verify ADRs in subfolder, separate files, correct naming
    - [ ] Verify ADR coverage: every AWS service has ADR or requirement justification
    - [ ] Verify Mermaid diagrams, content separation
    - [ ] Verify system-architecture.md template compliance
  - [ ] **Task 3.5.7 Calculate Quality Score**
    - [ ] Apply weights from scoring table above
    - [ ] Target: 85+ (see thresholds above)
  - [ ] **Task 3.5.8 Generate Validation Report**
    - [ ] Create `supplement-material/architecture-context/architecture-integration-validation.md`
    - [ ] Include: Executive Summary, Completeness, Integration, Service Limits, Feasibility, Documentation, Scoring, Recommendations

- [ ] **Task 3.6: Workflow Completion**
  - [ ] Confirm all deliverables created (see Output Structure above)
  - [ ] Update `.workflow-state/design-handoff.md` to mark architecture generation complete
  - [ ] Inform user: architecture generation complete, ready for holistic quality assessment
