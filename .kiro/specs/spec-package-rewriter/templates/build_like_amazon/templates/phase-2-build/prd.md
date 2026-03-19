# Product Requirements Document (PRD)

<execution-notes>
This template generates a BLA-compliant Product Requirements Document following official BLA PRD structure.
The PRD details requirements for a product or service, providing alignment among stakeholders and serving as input for design documents.
Process all prompt blocks systematically using specification package data as the exclusive source.
Maintain complete traceability to business requirements and customer value.
Follow BLA best practices: working backwards methodology, SMART requirements, stakeholder engagement.

**Integration with BLA Templates**:
- Reference CBO Canvas for business outcomes and customer value proposition
- Extract vision from Working Backwards Press Release
- Link to Working Backwards FAQ for detailed requirements context
- Connect to Success Metrics Canvas for measurable success criteria
- Reference Implementation Roadmap for delivery planning and phasing
- Link to Stakeholder Analysis for stakeholder engagement strategy
- Ensure requirements support business outcomes from CBO Canvas
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Version**: 1.0  
**Date**: <prompt>Use current date</prompt>  
**Status**: Draft  
**Author**: <prompt>Extract TPM from team information or use "BLA Design Agent Workflow"</prompt>  
**Reviewers**: <prompt>Extract reviewers from specification package (SDE3, SDM, Customer PO)</prompt>

## Table of Contents

1. Summary
2. Background
3. Vision for Product or Service
4. Tenets for Product or Service
5. Current State
6. Future State
7. Product Requirements
   - 7.1 User Personas
   - 7.2 Core Features and Major Modules
   - 7.3 Functional Requirements
   - 7.4 Non-Functional Requirements
8. Feature List
9. Dependencies, Risks, and Constraints
10. Assumptions
11. Operational Readiness
12. Appendices

---

## 1. Summary

<prompt>
Provide PRD summary including:
- Brief description of the product or service
- Purpose and scope of this PRD
- Target audience and stakeholders
- Key business objectives and customer value

**CBO Canvas Integration**:
- Reference CBO Canvas for customer challenges and business outcomes
- Link to CBO Elevator Level 4-5 quantified outcomes
- Connect to CBO Value Hierarchy (Agility, Cost, Resilience, Productivity)

Focus on customer value and business impact. Keep summary concise (1-2 paragraphs).
</prompt>

## 2. Background

<prompt>
Provide background context including:
- History of the project or product
- Current situation or status quo
- Business drivers and market context
- Customer pain points and challenges
- Previous attempts or related initiatives

**CBO Canvas and Working Backwards Integration**:
- Reference CBO Canvas for customer challenges and current state
- Extract context from Working Backwards Press Release
- Link to Problem/Solution Canvas for problem definition

Include relevant business context and customer perspective.
</prompt>

## 3. Vision for Product or Service

<prompt>
Define product vision including:
- Customer or business value proposition
- Long-term vision and strategic goals
- Success criteria for product delivery
- Expected business outcomes and impact
- Alignment with customer's strategic objectives

**Working Backwards and CBO Canvas Integration**:
- Extract vision from Working Backwards Press Release
- Reference CBO Canvas for business capability outcomes
- Link to Success Metrics Canvas for measurable success criteria
- Connect vision to CBO Elevator Level 4-5 outcomes

Focus on customer value and measurable business outcomes. Ensure vision is inspiring yet achievable.
</prompt>

## 4. Tenets for Product or Service

<prompt>
Define product tenets including:
- Core principles guiding product development
- Non-negotiable requirements and constraints
- Quality standards and customer experience principles
- Trade-off decisions and prioritization criteria

Tenets should be specific, actionable, and guide decision-making throughout development.
Include 3-5 key tenets that reflect customer priorities and business objectives.
</prompt>

## 5. Current State

<prompt>
Describe current state including:
- Existing systems, processes, or solutions
- Current capabilities and limitations
- Pain points and inefficiencies
- Technical debt and constraints
- User experience challenges

**CBO Canvas and Problem/Solution Canvas Integration**:
- Reference CBO Canvas for current state challenges
- Link to Problem/Solution Canvas for detailed problem analysis
- Quantify current state metrics where possible

Provide objective assessment of current state without proposed solutions.
</prompt>

## 6. Future State

<prompt>
Describe proposed future state including:
- Proposed solution and capabilities
- Value proposition for customers and business
- Key improvements and benefits
- User experience enhancements
- Technical capabilities and architecture approach

**Working Backwards and Problem/Solution Canvas Integration**:
- Extract future state from Working Backwards Press Release
- Reference Problem/Solution Canvas for solution approach
- Link to How Might We statements for solution ideation
- Connect to CBO Canvas for business outcome achievement

Document all options considered and rationale for selected approach.
Include comparison of alternatives and decision criteria.
</prompt>

## 7. Product Requirements

### 7.1 User Personas

<prompt>
Define user personas including:
- Primary and secondary user types
- User roles, responsibilities, and goals
- User needs, behaviors, and pain points
- Technical proficiency and context
- Success criteria from user perspective

Include 3-5 key personas that represent target users.
Focus on user needs and goals rather than demographics.
</prompt>

### 7.2 Core Features and Major Modules

<prompt>
Define core features and modules including:
- Major functional areas and capabilities
- Key features and user workflows
- Module organization and architecture
- Integration points and dependencies
- Priority and phasing of features

**Implementation Roadmap Integration**:
- Reference Implementation Roadmap for feature phasing
- Link features to epics and sprints
- Show feature dependencies and sequencing

Organize features by functional area or user journey.
</prompt>

### 7.3 Functional Requirements

<prompt>
Define functional requirements including:
- Detailed feature specifications
- User interactions and workflows
- Business logic and rules
- Data requirements and processing
- Integration requirements

**Format**: Use requirement IDs (FR-001, FR-002, etc.) for traceability.

**Requirements Structure**:
- **ID**: Unique identifier (FR-001)
- **Requirement**: Clear, specific requirement statement
- **Description**: Detailed explanation and context
- **Priority**: High/Medium/Low
- **Acceptance Criteria**: Measurable validation criteria

**Working Backwards Integration**:
- Extract requirements from Working Backwards FAQ
- Reference user stories and use cases
- Link to Success Metrics Canvas for validation criteria

Ensure requirements are SMART (Specific, Measurable, Attainable, Relevant, Timely).
</prompt>

### 7.4 Non-Functional Requirements

<prompt>
Define non-functional requirements including:
- Performance requirements (response times, throughput, scalability)
- Security requirements (authentication, authorization, encryption)
- Reliability requirements (availability, fault tolerance, recovery)
- Usability requirements (user experience, accessibility)
- Compatibility requirements (browsers, devices, platforms)
- Compliance requirements (standards, regulations)

**Format**: Use requirement IDs (NFR-001, NFR-002, etc.) for traceability.

**Success Metrics Canvas Integration**:
- Link NFRs to controllable input metrics
- Reference Success Metrics Canvas for performance targets
- Connect to CBO Value Hierarchy dimensions

Include specific, measurable targets for each NFR.
</prompt>

## 8. Feature List

<prompt>
Provide prioritized feature list including:
- Feature name and description
- Business value and user benefit
- Priority (High/Medium/Low)
- Estimated effort or complexity
- Dependencies and prerequisites
- Target release or sprint

**Format**: Table with columns for Feature, Description, Priority, Effort, Dependencies, Target Release

**Implementation Roadmap Integration**:
- Reference Implementation Roadmap for feature sequencing
- Link features to epics and sprints
- Show feature dependencies and critical path

Prioritize features top to bottom based on business value and dependencies.
</prompt>

## 9. Dependencies, Risks, and Constraints

<prompt>
Identify dependencies, risks, and constraints including:
- External dependencies (systems, teams, vendors)
- Technical dependencies and integration points
- Resource constraints (budget, timeline, skills)
- Technical constraints (platforms, technologies, standards)
- Business constraints (regulations, policies, processes)
- Key risks and mitigation strategies

**RAID Log Integration**:
- Reference RAID Log for comprehensive risk management
- Link to dependencies and assumptions tracking
- Connect to risk mitigation strategies

Provide complete description of factors that could impact successful implementation.
</prompt>

## 10. Assumptions

<prompt>
List assumptions including:
- Business assumptions and expectations
- Technical assumptions and prerequisites
- Resource assumptions (availability, skills, tools)
- Timeline assumptions and dependencies
- Integration assumptions and availability

**Format**: Table with columns for Assumption, Owner, Timeline, Status

**RAID Log Integration**:
- Reference RAID Log for assumption tracking
- Link to assumption validation and closure
- Track assumption status and impact

Assign ownership and timelines for validating each assumption.
</prompt>

## 11. Operational Readiness

<prompt>
Define operational readiness requirements including:
- Deployment and infrastructure requirements
- Monitoring and observability needs
- Support and maintenance procedures
- Training and documentation requirements
- Runbook and operational procedures
- Incident response and escalation

**Optional but highly recommended section**.
Collaborate with operations teams to define operational requirements.
Include manual processes and operational impacts.
</prompt>

## 12. Appendices

### Appendix A - Frequently Asked Questions (FAQ)

<prompt>
Provide FAQ including:
- Common questions and answers about the product
- Clarifications on requirements and scope
- Technical questions and considerations
- Business questions and justifications

**Working Backwards FAQ Integration**:
- Reference Working Backwards FAQ for comprehensive Q&A
- Include customer, technical, business, and risk questions
- Address stakeholder concerns proactively

Organize FAQ by category (Customer, Technical, Business, Risk).
</prompt>

### Appendix B - User Experience Research

<prompt>
Provide UX research including:
- User research findings and insights
- Usability testing results
- User feedback and validation
- Design iterations and rationale
- Relevant metrics and analytics

**Optional appendix** - include if user research has been conducted.
</prompt>

### Appendix C - User Persona Definitions

<prompt>
Provide detailed persona definitions including:
- Persona name and role
- Background and context
- Goals and motivations
- Pain points and challenges
- Technical proficiency and tools
- Success criteria and metrics

Expand on Section 7.1 with detailed persona descriptions.
</prompt>

### Appendix D - Useful Links and References

<prompt>
Provide links and references including:
- Related documentation (BRD, HLD, Working Backwards artifacts)
- Wikis and knowledge bases
- Design mockups and prototypes
- Customer tickets and feature requests
- Program information and roadmaps

**BLA Template Integration**:
- Link to CBO Canvas
- Link to Working Backwards Press Release and FAQ
- Link to Success Metrics Canvas
- Link to Implementation Roadmap
- Link to Stakeholder Analysis

Organize links by category for easy navigation.
</prompt>

---

**Document Review and Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| TPM (Author) | <prompt>Extract TPM name from team information</prompt> | | |
| SDE3 (Reviewer) | <prompt>Extract SDE3 name from team information</prompt> | | |
| SDM (Reviewer) | <prompt>Extract SDM name from team information</prompt> | | |
| Customer PO (Approver) | <prompt>Extract Customer PO from stakeholder information</prompt> | | |

**Change History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial PRD creation from business requirements per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This document follows Build Like Amazon (BLA) prescriptive guidance for Product Requirements Documents.*

*For support: BLA Practice Team: bla-practice@amazon.com*
