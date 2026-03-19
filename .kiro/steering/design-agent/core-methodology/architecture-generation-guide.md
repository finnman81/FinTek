---
inclusion: manual
---

# Architecture Generation Principles

## Purpose

This document provides universal principles and quality standards for architecture generation that apply regardless of the specific workflow or tools used. These principles guide systematic architecture design through research-driven decision making.

## Architecture Quality Principles

### Customer Context Awareness

**Principle**: Architecture complexity and approach must align with customer context and project constraints.

**AWS Platform Context**: This tool is designed for AWS customers building on AWS. AWS earns customer trust through value, not lock-in tactics. Do not proactively list "vendor lock-in" as a risk - customers choose AWS for its services. If the customer raises portability requirements, address them factually: AWS provides full data control, ownership, and portability, plus support for open standards, containers, and third-party tooling. (Source: docs.aws.amazon.com/whitepapers/latest/unpicking-vendor-lock-in/)

**Application Guidelines**:
- **POC Mode**: Focus on core functionality validation, avoid enterprise complexity
- **Production Mode**: Include full enterprise considerations (scalability, availability, security)
- **Compliance Mode**: Integrate regulatory requirements and security controls
- **Budget-Conscious Mode**: Optimize for cost-effectiveness and resource efficiency

### Simplicity - You Aren't Gonna Need It (YAGNI)

**Principle**: The best architecture is the simplest one that meets the stated requirements. Do not add components, services, or capabilities that are not explicitly required.

**CRITICAL - Scope Discipline**:
- **Only implement what is explicitly requested** - never derive or infer additional requirements
- **Research findings are suggestions, not requirements** - deep research may suggest capabilities beyond scope; ignore them unless they directly address stated requirements
- **"Out of Scope" means OUT** - if the user explicitly excludes something, do not design for it
- **No future-proofing for POC/MVP** - design for current requirements only

**POC/MVP Simplicity Rules**:
1. **Single API Pattern**: Use ONE API type (REST OR WebSocket OR GraphQL) - never multiple
2. **No RAG Unless Requested**: Do not add Knowledge Bases, OpenSearch, or vector stores unless user explicitly requests semantic search over their own content
3. **No HA/DR for POC**: Skip multi-AZ, multi-region, and disaster recovery unless explicitly required
4. **Minimal Data Stores**: One database type per data pattern; avoid adding caching layers, search indexes, or secondary stores
5. **No Enterprise Patterns**: Skip service mesh, API versioning, blue-green deployments for POC

**Simplicity Checklist** (validate before finalizing architecture):
- [ ] Every service directly maps to a stated requirement (no orphan services)
- [ ] No component exists "for future scalability" or "best practice" without explicit requirement
- [ ] Research suggestions that expand scope have been filtered out
- [ ] "Out of Scope" items from requirements are not addressed in architecture
- [ ] Single API pattern used (not multiple)
- [ ] No RAG/Knowledge Base unless explicitly requested for user's own content

**Common Scope Creep Patterns to Reject**:
- Research suggests multi-API patterns (REST + WebSocket) when single pattern suffices
- Research suggests HA/DR patterns for a POC
- Research suggests caching layers, search indexes for simple data access patterns
- Research suggests enterprise patterns (service mesh, API versioning, blue-green) for POC
- Research suggests storing user content when user only asked to query external sources

### Reference Architecture Leverage

**Principle**: Prefer proven reference architectures over custom solutions when applicable.

**Application Guidelines**:
- Apply systematic guidance selection framework to identify relevant reference architectures
- Leverage AWS Well-Architected Framework and industry best practices
- Combine multiple reference architecture patterns when appropriate for complex requirements

### Technology Selection Standards

**Principle**: Technology choices must be justified with clear rationale and aligned with project constraints.

**Selection Criteria**:
- **Functional Fit**: Technology meets functional requirements
- **Non-Functional Alignment**: Supports performance, security, scalability needs
- **Team Capability**: Aligns with team skills and experience
- **Operational Complexity**: Matches operational maturity and resources
- **Cost Effectiveness**: Balances capability with budget constraints

### Research-Driven Decision Making

**Principle**: Architecture decisions must be based on comprehensive research from authoritative sources.

**Research Tool Priority**: Follow `.kiro/steering/design-agent/architecture/research.md` for tool selection order and decision flow.

**Research Standards**:
- **Multi-Source Validation**: Consult multiple authoritative sources (AWS documentation, industry best practices, COE analyses)
- **Decision Traceability**: Document research sources that influenced each architectural decision
- **Alternative Evaluation**: Research and document alternatives considered with rationale for selection
- **Risk Assessment**: Include research-identified risks and mitigation strategies
- **Cost Analysis**: Research pricing implications and optimization strategies
- **Regional Availability**: Verify service availability in target regions

---

## Documentation Standards

### Architecture Decision Records (ADRs)

**Principle**: Document architectural decisions with clear rationale and context.

**ADR-Worthy Decision Criteria** - Create an ADR when:
1. Multiple viable AWS/technology alternatives exist
2. The decision has cost, operational, or scalability implications
3. The decision affects deployment, CI/CD, or operational patterns
4. Trade-offs were evaluated (even implicitly)

**CRITICAL - ADR Coverage Rule**: Every AWS service in the architecture MUST trace to either:
- An explicit ADR documenting the selection rationale and alternatives considered, OR
- A stated requirement that explicitly mandates a specific service

**Required ADR Categories:**

| Category | Examples | Common Alternatives to Document |
|----------|----------|--------------------------------|
| **Compute** | Lambda vs ECS vs App Runner | Serverless vs containers vs managed |
| **Database** | DynamoDB vs Aurora vs RDS | NoSQL vs SQL, serverless vs provisioned |
| **API Layer** | API Gateway vs ALB vs AppSync | REST vs GraphQL, regional vs edge |
| **Static Hosting** | S3+CloudFront vs Amplify Hosting vs Alternatives | Managed vs DIY, CDN patterns |
| **Authentication** | Cognito vs IAM Identity Center vs third-party | Managed vs federated |
| **Messaging** | SQS vs SNS vs EventBridge | Queue vs pub/sub vs event bus |
| **Storage** | S3 vs EFS vs FSx | Object vs file, access patterns |
| **AI/ML** | Bedrock vs SageMaker vs AgentCore | Managed vs custom, agent patterns |

**Quality Standards**:
- **Individual files**: `ADR-XXX-[descriptive-title].md` in `architecture-decision-records/`
- **Folder Organization**: Place in `architecture-decision-records/` folder
- **Sequential Numbering**: Use zero-padded numbering (001, 002, 003, etc.)

**ADR Content Requirements**:
- **Status**: Current state (Proposed/Accepted/Deprecated/Superseded)
- **Context**: Clear problem statement and constraints
- **Decision**: Specific architectural choice made
- **Consequences**: Trade-offs and implications (Positive/Negative/Neutral)
- **Alternatives**: Options considered (minimum 2) and why they were rejected
- **Rationale**: Reasoning behind the decision (expert insights, customer context, constraints)
- **Research Sources**: Citations and references from research that informed the decision
- **Related Decisions**: Links to other ADRs if applicable

### Technical Specification Standards

**Principle**: Provide implementable technical specifications that development teams can follow directly.

**Quality Criteria**:
- **Component Specifications**: Clear purpose, responsibilities, interfaces, dependencies
- **API Specifications**: Complete endpoint definitions with request/response formats
- **Data Architecture**: Data models, schema design, indexing strategy
- **Integration Patterns**: External system integrations and internal service communication

### Architecture Package Structure

**Standard Genneration Output**:
- `system-architecture.md` - High-level system design and component overview
- `architecture-decision-records/` folder containing:
  - `ADR-001-[decision-title].md`
  - `ADR-002-[decision-title].md`
  - `ADR-00X-[decision-title].md`
- `technical-specifications.md` - Detailed component specifications
- `api-specifications.md` - API endpoint definitions and schemas
- `data-architecture.md` - Data models and database design
- `research-report.md` - Research findings and citations

**File Descriptions**:

**system-architecture.md**
- High-level system design and component overview
- System architecture diagrams (Mermaid format) showing all components with AWS services
- Data flow patterns between components
- Integration points with external systems
- Security boundaries and controls
- Integration patterns used (REST APIs, GraphQL, gRPC, Event-driven, MCP, Batch, Streaming)

**technical-specifications.md**
- Detailed specifications for each system component
- Component purpose and responsibilities
- Service boundaries and interfaces
- Data models and schemas per component
- API specifications for internal component communication
- Dependencies between components
- Security controls per component
- Performance and scalability considerations
- Component diagrams (Mermaid format)

**api-specifications.md**
- Complete API endpoint definitions
- HTTP methods and paths for each endpoint
- Request parameters and body schemas
- Response formats and status codes
- Authentication and authorization requirements
- Rate limiting and quota specifications
- Error handling and response codes
- API versioning strategy

**data-architecture.md**
- Data models and entity definitions
- Database schemas and table structures
- Data relationships and foreign keys
- Indexing strategy for performance optimization
- Data retention and archival policies
- Data migration strategies
- Backup and recovery procedures
- Data access patterns

**architecture-decision-records/ADR-XXX-[title].md**
- Individual files for each significant architectural decision
- Naming convention: `ADR-001-database-selection.md`, `ADR-002-api-gateway-choice.md`
- Each ADR contains:
  - **Context**: Requirements and constraints that led to the decision
  - **Decision**: Specific architectural choice made (with specific AWS service or technology)
  - **Consequences**: Trade-offs, benefits, and implications of the decision
  - **Alternatives**: Other options considered and why they were rejected
  - **Rationale**: Reasoning behind the decision (research findings, customer context, constraints)
  - **Research Sources**: Citations and references from research that informed the decision

**research-report.md**
- Preserved output from research phase
- Complete research findings with citations
- Source material for architecture decisions
- Provides traceability from research to architecture choices
- Reference for understanding decision context and alternatives

## Architecture Quality Assessment

### Technical Accuracy Standards

**Principle**: All architectural decisions must be technically sound and implementable.

**Validation Criteria**:
- **Service Limits Awareness**: Architecture considers AWS service quotas and limits
- **Scalability Validation**: Components can scale to meet non-functional requirements
- **Security Integration**: Security controls integrated throughout architecture
- **Performance Feasibility**: Architecture can meet performance requirements
- **Cost Optimization**: Architecture balances capability with cost constraints

**Quality Score Thresholds**:
- **90-100 (Excellent)**: Ready to proceed, high confidence
- **85-89 (Good)**: Ready to proceed, minor improvements optional
- **70-84 (Conditional)**: Address identified issues before proceeding
- **<70 (Failed)**: Significant work needed, do not proceed

**Validation Targets**:
- **Requirements Coverage**: 95%+ functional, 95%+ non-functional, 100% user stories
- **Component Integration**: All interfaces compatible, data flows validated
- **Service Limits**: All services analyzed, high-risk services (<20% of total) have mitigation
- **Technical Feasibility**: All technologies GA or Preview, team has adequate expertise
- **Documentation**: All required documents exist and meet quality standards

### Implementation Readiness

**Principle**: Architecture documentation must provide sufficient detail for development teams to implement without additional clarification.

**Readiness Indicators**:
- **Complete Specifications**: All components fully specified
- **Clear Interfaces**: Component interactions well-defined
- **Technology Justification**: Technology choices explained with rationale
- **Implementation Guidance**: Development strategy and phases defined
- **Risk Mitigation**: Known risks identified with mitigation strategies

### Stakeholder Communication

**Principle**: Architecture must be communicated effectively to different stakeholder groups.

**Communication Standards**:
- **Executive Summary**: High-level overview focusing on business alignment and risk
- **Development Team View**: Detailed technical specifications and implementation guidance
- **Operations View**: Deployment, monitoring, and operational considerations
- **Security View**: Security controls, compliance, and risk mitigation measures

## Continuous Improvement Standards

### Architecture Feedback Integration

**Principle**: Architecture effectiveness should be measured and improved continuously through systematic stakeholder feedback integration.

**Feedback Mechanisms**:
- **Implementation Velocity**: Track time from architecture to working implementation
- **Architecture Clarity**: Monitor clarification requests during development
- **Technical Debt**: Assess architecture decisions requiring future refactoring
- **Performance Achievement**: Compare actual vs. planned performance outcomes
- **Team Satisfaction**: Collect feedback on architecture quality and usability
- **Stakeholder Feedback Integration**: Systematic collection and analysis of feedback through `project-doc/feedback/iteration-N/` folders
- **Dynamic Improvement**: Automatic generation of architecture improvement tasks based on feedback content
- **Research Quality**: Evaluate comprehensiveness and accuracy of research-driven decisions

**Iterative Architecture Refinement**:
- **Feedback-Driven Updates**: Architecture modifications based on systematic stakeholder feedback analysis
- **Complete Project Iterations**: Creation of new complete project folders (project-name-iteration-N) incorporating feedback
- **Traceability Maintenance**: Complete audit trail linking feedback documents to specific architecture changes
- **Quality Continuity**: Ensure architecture quality standards are maintained or improved across feedback iterations

### Version Control and Change Management

**Principle**: Architecture changes must be tracked and managed systematically across feedback iterations.

**Change Management Standards**:
- **Version Control**: All architecture documents under version control with iteration-based versioning
- **Change Logs**: Document all architectural modifications with rationale and feedback source traceability
- **Review Cycles**: Regular architecture review with development teams and systematic stakeholder feedback integration
- **Update Procedures**: Clear process for updating architecture based on feedback through dynamic task generation
- **Iteration Management**: Systematic management of complete project folder iterations with proper versioning and organization
