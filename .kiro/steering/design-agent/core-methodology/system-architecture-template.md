---
inclusion: manual
---

# System Architecture Document Template

## Purpose

Primary high-level design artifact describing:
- what is the purpose of the system
- what problem does it solve 
- how a system satisfies functional and non-functional requirements.

**Document Objectives**: Establish system context, describe components, illustrate behavior via flows, trace requirements, define interfaces.

---

## Template Structure

### Section 1: Executive Summary

Concise overview describing: 
- system purpose
- what problem does it solve
- key architectural decisions (3-5 bullets)
- primary technologies
- deployment environment.

### Section 2: Architecture Principles

4-6 guiding principles with trade-off acknowledgments. Format:

| Principle | Description | Trade-off |
|-----------|-------------|-----------|
| Serverless-first | Managed, consumption-based services | Higher per-request cost vs lower ops overhead |

### Section 3: Technology Summary

**AWS Services Inventory**:
| Service | Purpose | Configuration | ADR Reference |
|---------|---------|---------------|---------------|

**Implementation Technologies** (when applicable):

| Category | Technology | Scope |
|----------|------------|-------|
| Language | e.g., Python, TypeScript | Backend services, Lambda functions |
| IaC | e.g., Terraform, CDK, CloudFormation | Infrastructure provisioning | 
| Framework | e.g., FastAPI, Express | API layer |

**External Dependencies**:
| Dependency | Purpose | Version/Endpoint |
|------------|---------|------------------|

### Section 4: System Context

**Purpose**: Define system boundary and external entities.

**CRITICAL - What is "External"**:
- **External**: Users, third-party APIs, external services
- **NOT External**: AWS services used to BUILD the system (shown in Component Architecture)

**Required**: External systems list, user/actor identification, trust boundaries.

**Diagram**: System as single box, only truly external actors outside, arrows with interaction labels.

**External Dependencies Table**:
| External Entity | Type | Interaction | Data Exchanged | Criticality |
|----------------|------|-------------|----------------|-------------|

### Section 5: Core Components

**Purpose**: Detail internal components, responsibilities, relationships.

**Required**: Component diagram (grouped by layer/domain), component catalog.

#### [Component Name]

**Component Overview**: For each component provide a brief description of it's purpose, responsibilities and dependencies.

**Tech stack**: Recommended technologies, frameworks, AWS Services. Describe briefly which alternatives have been considered and why this one was chosen. This needs to be aligned with the Architecture Decision Record (ADR)

### Section 6: Interface Specifications

**Interface Matrix**:
| Source | Target | Interface Type | Protocol | Authentication | Data Format |
|--------|--------|---------------|----------|----------------|-------------|

**Interface Details** (for significant interfaces): Protocol, Authentication, Data Format, Request/Response specs.

### Section 7: Data Flow Diagrams

**Required flows**: Primary business (happy path), authentication/authorization, error handling, one per major feature.

**Per flow document**: Trigger, Actors, Outcome, Requirements refs, sequence diagram, step details table.

**Step Details Table**:
| Step | Description | Data | Error Handling |
|------|-------------|------|----------------|

### Section 8: Security Architecture

**Required**: Security zones diagram, authentication architecture, authorization model, data protection controls.

**Tables**:
- Authentication: Component, Method, Token Type, Validation
- Authorization: Resource, Actor, Permissions, Enforcement Point
- Data Protection: Data Type, At Rest, In Transit, Access Control

### Section 9: Requirements Traceability

**Functional Requirements Coverage**:
| Requirement | Component(s) | Flow(s) | Coverage |
|-------------|--------------|---------|----------|

**Non-Functional Requirements Coverage**:
| Requirement | Architectural Solution | Validation Method |
|-------------|----------------------|-------------------|

**Summary**: X/Y functional covered (Z%), X/Y non-functional covered (Z%), gaps with mitigation.

---

## Quality Checklist

**Completeness**: Executive summary, system context diagram, all components documented, interfaces specified, primary flows diagrammed, security architecture, requirements traceability.

**Clarity**: Readable diagrams, clear non-overlapping responsibilities, data shown at each flow step.

**Consistency**: Component names consistent across diagrams, interfaces match flows, tech aligns with ADRs.

**Implementability**: Sufficient detail for dev team, unambiguous boundaries, clear contracts, actionable security controls.

---

## Diagram Standards

| Scenario | Mermaid Type |
|----------|--------------|
| System context | `graph TB` |
| Component architecture | `graph TB` with `subgraph` |
| Data flows (multi-step) | `sequenceDiagram` |
| Decision flows | `flowchart TD` |
| State transitions | `stateDiagram-v2` |

**Conventions**: Consistent styles, labeled arrows, grouped subgraphs, technology names in labels, standard AWS service names.

---

## Anti-Patterns vs Best Practices

| ❌ Avoid | ✅ Instead |
|----------|-----------|
| Vague descriptions ("handles business logic") | Specific responsibilities |
| Missing external dependencies | Complete context diagram |
| Only happy path flows | Multiple flows including errors |
| No requirements traceability | Every component maps to requirements |
| Technology without justification | ADR references for decisions |
| Inconsistent naming | Same names everywhere |
| Missing security boundaries | Clear trust zones |
| Orphan components | Every component in at least one flow |
