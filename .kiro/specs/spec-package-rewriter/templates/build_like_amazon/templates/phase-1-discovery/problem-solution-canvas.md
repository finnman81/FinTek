# Problem/Solution Canvas

<execution-notes>
This template generates a BLA-compliant Problem/Solution Canvas.
The canvas clearly articulates core problems and proposed solutions with root cause analysis and validation approach.
Process all prompt blocks systematically using specification package data as the exclusive source.
Follow BLA best practices: root cause focus, solution validation, customer obsession, measurable success criteria.
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Date**: <prompt>Use current date</prompt>  
**Version**: 1.0  
**Status**: Draft

---

## 1. Problem Statement

### 1.1 Core Problem Definition

<prompt>
Define the core problem from:
- Customer Business Outcomes Canvas challenges
- Business requirements problem statements
- Current state analysis and pain points
- Customer journey mapping issues

Provide clear, concise problem statement (2-3 sentences) that describes:
- What the problem is
- Who experiences the problem
- Why it matters (business impact)
- Current state quantification

Example: "Customer service teams spend 4 hours per day manually processing returns, resulting in $2M annual operational costs and 48-hour average response times. This manual process leads to 30% customer dissatisfaction and prevents the team from focusing on high-value customer interactions. The current system lacks automation capabilities and integration with inventory management."
</prompt>

### 1.2 Problem Scope and Boundaries

<prompt>
Define problem scope from:
- Requirements documentation and scope definition
- Stakeholder analysis and affected parties
- System boundaries and integration points

Clarify:
- **In Scope**: What aspects of the problem will be addressed
- **Out of Scope**: What aspects will not be addressed (and why)
- **Affected Stakeholders**: Who experiences this problem
- **System Boundaries**: Where the problem exists in the ecosystem
</prompt>

### 1.3 Problem Evidence and Validation

<prompt>
Provide evidence for the problem from:
- Current state metrics and baselines
- Stakeholder feedback and pain point validation
- Customer journey mapping data
- Business impact quantification

Include:
- **Quantitative Evidence**: Metrics, costs, time measurements, error rates
- **Qualitative Evidence**: Stakeholder quotes, user feedback, observed behaviors
- **Business Impact**: Revenue impact, cost impact, customer satisfaction impact
- **Validation Method**: How the problem was validated with stakeholders
</prompt>

---

## 2. Root Cause Analysis

### 2.1 Primary Root Causes

<prompt>
Identify root causes from:
- Problem analysis and discovery findings
- Current state technical and process limitations
- Architecture constraints and technical debt
- Organizational or process issues

Use "5 Whys" or similar technique to identify root causes rather than symptoms.

For each root cause:
**Root Cause [#]**: [Description]

**Analysis**: <prompt>Explain why this is a root cause rather than a symptom</prompt>

**Evidence**: <prompt>Provide evidence supporting this root cause</prompt>

**Impact**: <prompt>Quantify the impact of this root cause on the problem</prompt>

Identify 3-5 primary root causes.
</prompt>

### 2.2 Contributing Factors

<prompt>
Identify contributing factors from:
- Environmental constraints and limitations
- Resource constraints (budget, time, skills)
- Technical constraints and dependencies
- Organizational or cultural factors

List 3-5 contributing factors that exacerbate the problem but are not primary root causes.
</prompt>

### 2.3 Root Cause Prioritization

<prompt>
Prioritize root causes by:
- Impact on the problem (High/Medium/Low)
- Feasibility of addressing (High/Medium/Low)
- Cost to address (High/Medium/Low)

Create prioritization matrix:

| Root Cause | Impact | Feasibility | Cost | Priority |
|------------|--------|-------------|------|----------|
| [RC-1] | [H/M/L] | [H/M/L] | [H/M/L] | [P0/P1/P2] |

Focus solution on high-impact, high-feasibility root causes.
</prompt>

---

## 3. Solution Description

### 3.1 Proposed Solution Overview

<prompt>
Describe the proposed solution from:
- Product requirements and feature descriptions
- Architecture overview and technical approach
- Working Backwards press release and vision
- Customer Business Outcomes Canvas solution

Provide comprehensive solution description (3-5 paragraphs) covering:
- **What**: What the solution is and how it works
- **How**: How it addresses the root causes
- **Why**: Why this approach was chosen over alternatives
- **Benefits**: Key benefits and capabilities delivered

Focus on business capabilities and outcomes rather than technical implementation details.
</prompt>

### 3.2 Solution Components and Capabilities

<prompt>
Break down solution into components from:
- Functional requirements and feature descriptions
- Architecture components and modules
- User stories and capabilities

For each major component:
**Component [#]**: [Name]

**Description**: <prompt>Describe what this component does</prompt>

**Root Causes Addressed**: <prompt>Which root causes this component addresses</prompt>

**Key Capabilities**: <prompt>List 3-5 key capabilities this component provides</prompt>

**User Benefit**: <prompt>Describe the benefit to end users or stakeholders</prompt>

Identify 4-6 major solution components.
</prompt>

### 3.3 Solution Architecture Approach

<prompt>
Describe high-level architecture from:
- Architecture documentation and diagrams
- Technology stack and AWS services
- Integration approach and patterns
- Non-functional requirements approach

Include:
- **Architecture Pattern**: Overall architectural approach (e.g., microservices, event-driven, serverless)
- **Key Technologies**: Primary technologies and AWS services used
- **Integration Approach**: How solution integrates with existing systems
- **Quality Attributes**: How solution addresses performance, scalability, security, reliability
</prompt>

---

## 4. Problem-Solution Mapping

<prompt>
Create explicit mapping between problems/root causes and solution components:

| Problem / Root Cause | Solution Component(s) | How It Solves | Expected Improvement |
|---------------------|----------------------|---------------|---------------------|
| [Problem/RC description] | [Component name(s)] | [Explanation] | [Quantified improvement] |

This mapping ensures complete coverage of all identified problems and root causes.
Identify any gaps where problems are not fully addressed by the solution.
</prompt>

---

## 5. Success Criteria

### 5.1 Solution Success Metrics

<prompt>
Define success metrics from:
- Success Metrics Canvas
- KPI scorecard and measurement framework
- Customer Business Outcomes Canvas results
- Non-functional requirements and SLAs

For each success metric:
**Metric**: [Metric name]

**Current Baseline**: <prompt>Current state measurement</prompt>

**Target**: <prompt>Future state goal with timeframe</prompt>

**Measurement Method**: <prompt>How this will be measured</prompt>

**Success Threshold**: <prompt>Minimum acceptable improvement to consider solution successful</prompt>

Include 5-8 key success metrics covering:
- Performance improvements (speed, efficiency)
- Cost reductions (operational costs, resource utilization)
- Quality improvements (error rates, customer satisfaction)
- Business outcomes (revenue, conversion, retention)
</prompt>

### 5.2 User Acceptance Criteria

<prompt>
Define user acceptance criteria from:
- User stories and acceptance criteria
- Stakeholder success definitions
- User experience requirements

List 5-10 acceptance criteria that must be met for users to consider the solution successful.
Format: "Users can [action] [with what result] [within what constraints]"
</prompt>

### 5.3 Business Outcome Validation

<prompt>
Define business outcome validation from:
- Customer Business Outcomes Canvas
- Business case and ROI expectations
- Stakeholder success criteria

Describe how business outcomes will be validated:
- **Validation Timeframe**: When outcomes will be measured (e.g., 3 months post-launch, 6 months post-launch)
- **Validation Method**: How outcomes will be measured and validated
- **Success Criteria**: What constitutes successful business outcome achievement
- **Stakeholder Review**: How results will be reviewed with stakeholders
</prompt>

---

## 6. Validation Approach

### 6.1 Solution Validation Strategy

<prompt>
Define validation strategy from:
- Testing strategy and quality assurance approach
- Pilot or phased rollout plans
- User acceptance testing approach
- Proof of concept or prototype plans

Describe how the solution will be validated before full deployment:
- **Proof of Concept**: Early validation of key technical assumptions
- **Prototype Testing**: User testing of key workflows and experiences
- **Pilot Deployment**: Limited rollout to validate solution in production
- **User Acceptance Testing**: Formal UAT with representative users
- **Performance Testing**: Validation of non-functional requirements
</prompt>

### 6.2 Risk Mitigation and Contingency

<prompt>
Identify risks and mitigation from:
- RAID log risk assessment
- Technical risks and challenges
- Adoption and change management risks

For each major risk:
**Risk**: [Risk description]

**Impact**: <prompt>Potential impact if risk occurs</prompt>

**Mitigation**: <prompt>How risk will be mitigated</prompt>

**Contingency**: <prompt>Backup plan if mitigation fails</prompt>

Include 3-5 major risks with mitigation strategies.
</prompt>

### 6.3 Feedback and Iteration Plan

<prompt>
Define feedback and iteration approach from:
- Agile development and sprint planning
- User feedback collection mechanisms
- Continuous improvement processes

Describe how feedback will be collected and incorporated:
- **Feedback Channels**: How users and stakeholders provide feedback
- **Feedback Frequency**: How often feedback is collected and reviewed
- **Iteration Approach**: How feedback drives solution improvements
- **Prioritization**: How feedback is prioritized for implementation
</prompt>

---

## 7. Alternatives Considered

<prompt>
Document alternative solutions from:
- Architecture decision records
- Technology evaluation and selection
- Build vs. buy analysis
- Alternative approaches discussed

For each alternative:
**Alternative [#]**: [Name/Description]

**Approach**: <prompt>Describe the alternative approach</prompt>

**Pros**: <prompt>List advantages of this alternative</prompt>

**Cons**: <prompt>List disadvantages of this alternative</prompt>

**Why Not Selected**: <prompt>Explain why this alternative was not chosen</prompt>

Include 2-4 significant alternatives that were seriously considered.
</prompt>

---

## 8. Implementation Considerations

<prompt>
Identify implementation considerations from:
- Implementation roadmap and delivery plan
- Technical complexity and dependencies
- Resource requirements and constraints
- Change management and adoption planning

Include:
- **Technical Complexity**: Assessment of implementation complexity
- **Dependencies**: Critical dependencies that must be managed
- **Resource Requirements**: Team, skills, budget, time required
- **Change Management**: Organizational changes and adoption approach
- **Timeline**: High-level implementation timeline and phases
</prompt>

---

**Document Review and Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| AWS TPM | <prompt>Extract TPM name</prompt> | | |
| AWS SDE3 | <prompt>Extract SDE3 name</prompt> | | |
| Customer Product Owner | <prompt>Extract Product Owner</prompt> | | |
| Customer Technical Lead | <prompt>Extract Technical Lead</prompt> | | |

**Change History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial Problem/Solution Canvas per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This Problem/Solution Canvas follows Build Like Amazon (BLA) prescriptive guidance.*

*For support: BLA Practice Team: bla-practice@amazon.com*
