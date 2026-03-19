# Implementation Roadmap Canvas

<execution-notes>
This template generates a BLA-compliant Implementation Roadmap Canvas.
The roadmap provides detailed timeline and sequencing for BLA implementation with workstream organization, epic breakdown, and dependency mapping.
Process all prompt blocks systematically using specification package data as the exclusive source.
Follow BLA best practices: 6-month delivery target, sprint-based planning, granular traceability, critical path identification.
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Date**: <prompt>Use current date</prompt>  
**Roadmap Duration**: <prompt>Extract duration (typically 6 months for BLA)</prompt>  
**Start Date**: <prompt>Extract or calculate start date</prompt>  
**Target Launch Date**: <prompt>Extract or calculate launch date (6 months from start)</prompt>  
**Version**: 1.0  
**Status**: Draft

---

## Table of Contents

1. Roadmap Overview
2. Workstream Organization
3. Epic and Story Breakdown
4. Timeline and Milestones
5. Resource Allocation
6. Dependency Mapping
7. Critical Path Analysis
8. Risk and Mitigation

---

## 1. Roadmap Overview

### 1.1 Implementation Approach

<prompt>
Describe implementation approach from:
- Implementation planning and delivery methodology
- Agile/sprint-based development approach
- BLA 6-month delivery commitment
- Phased rollout or big-bang deployment strategy

Include:
- **Methodology**: Agile, Scrum, or hybrid approach
- **Sprint Duration**: Typically 2-week sprints
- **Number of Sprints**: Total sprints in 6-month timeline (typically 12-13 sprints)
- **Delivery Phases**: Major phases (e.g., Foundation, Core Features, Integration, Launch)
- **Deployment Strategy**: How solution will be deployed (phased, pilot, full rollout)
</prompt>

### 1.2 Success Criteria

<prompt>
Define roadmap success criteria from:
- Customer Business Outcomes Canvas
- Success Metrics Canvas
- Stakeholder expectations and commitments

Include:
- **On-Time Delivery**: Launch within 6-month BLA commitment
- **Scope Completion**: All P0 features delivered
- **Quality Standards**: Quality gates and acceptance criteria met
- **Business Outcomes**: Key business metrics achieved
- **Stakeholder Satisfaction**: Stakeholder approval and sign-off
</prompt>

### 1.3 Governance and Decision-Making

<prompt>
Define governance approach from:
- Governance framework and decision-making authority
- Sprint review and retrospective cadence
- Stakeholder communication and escalation

Include:
- **Sprint Reviews**: Frequency and participants
- **Steering Committee**: Executive oversight and decision-making
- **Escalation Path**: How issues and blockers are escalated
- **Change Control**: How scope changes are managed
</prompt>

---

## 2. Workstream Organization

<prompt>
Organize work into workstreams from:
- Functional requirements and feature groupings
- Architecture components and modules
- Team structure and skill sets
- Parallel work opportunities

For each workstream:

### Workstream [#]: [Name]

**Description**: <prompt>Describe the workstream focus and scope</prompt>

**Objectives**: <prompt>List 3-5 key objectives for this workstream</prompt>

**Team Composition**: <prompt>Identify team members and roles assigned to this workstream</prompt>

**Dependencies**: <prompt>List dependencies on other workstreams or external factors</prompt>

**Deliverables**: <prompt>List major deliverables from this workstream</prompt>

**Timeline**: <prompt>Identify start and end sprints for this workstream</prompt>

Identify 3-6 major workstreams that can progress in parallel.
Example workstreams: Frontend Development, Backend Services, Data Integration, Infrastructure & DevOps, Testing & Quality, Security & Compliance
</prompt>

---

## 3. Epic and Story Breakdown

<prompt>
Break down work into epics and stories from:
- User stories and requirements
- Functional requirements and features
- Architecture components and capabilities

For each epic:

### Epic [#]: [Name]

**Description**: <prompt>Describe the epic and its business value</prompt>

**Business Value**: <prompt>Explain the business value and customer benefit</prompt>

**Workstream**: <prompt>Identify which workstream owns this epic</prompt>

**Story Points**: <prompt>Total story points for this epic</prompt>

**Sprint Assignment**: <prompt>Which sprints this epic spans</prompt>

**User Stories**: <prompt>List 3-8 user stories within this epic with story points</prompt>
- US-[ID]: [User story title] ([X] points) - Sprint [#]
- US-[ID]: [User story title] ([X] points) - Sprint [#]

**Acceptance Criteria**: <prompt>High-level acceptance criteria for epic completion</prompt>

**Dependencies**: <prompt>List dependencies on other epics or external factors</prompt>

Identify 10-15 major epics covering all functional requirements.
Ensure total story points align with team velocity and timeline.
</prompt>

---

## 4. Timeline and Milestones

### 4.1 Sprint Schedule

<prompt>
Create sprint schedule from:
- Sprint planning and capacity
- Epic and story assignments
- Team velocity estimates

| Sprint | Dates | Focus | Key Deliverables | Story Points |
|--------|-------|-------|------------------|--------------|
| Sprint 1 | [Dates] | [Focus area] | [Deliverables] | [Points] |
| Sprint 2 | [Dates] | [Focus area] | [Deliverables] | [Points] |
| ... | ... | ... | ... | ... |
| Sprint 12 | [Dates] | [Focus area] | [Deliverables] | [Points] |

Include all sprints in 6-month timeline (typically 12-13 two-week sprints).
</prompt>

### 4.2 Major Milestones

<prompt>
Define major milestones from:
- Implementation phases and gates
- Stakeholder review and approval points
- Technical milestones and integrations
- Launch readiness criteria

For each milestone:

**Milestone [#]**: [Name]  
**Target Date**: [Date/Sprint]  
**Description**: <prompt>Describe what this milestone represents</prompt>  
**Success Criteria**: <prompt>Define criteria for milestone completion</prompt>  
**Deliverables**: <prompt>List deliverables due at this milestone</prompt>  
**Stakeholder Review**: <prompt>Identify stakeholder review/approval required</prompt>

Include 6-10 major milestones across the 6-month timeline.
Example milestones: Architecture Approval, MVP Complete, Integration Complete, UAT Complete, Production Ready, Launch
</prompt>

### 4.3 Phase Breakdown

<prompt>
Organize timeline into phases from:
- Implementation approach and delivery strategy
- Logical groupings of work
- Risk mitigation and validation points

For each phase:

**Phase [#]**: [Name] (Sprint [X] - Sprint [Y])

**Objectives**: <prompt>List 3-5 key objectives for this phase</prompt>

**Key Activities**: <prompt>Describe major activities in this phase</prompt>

**Deliverables**: <prompt>List major deliverables from this phase</prompt>

**Exit Criteria**: <prompt>Define criteria to exit this phase and move to next</prompt>

Typical BLA phases:
- Phase 1: Foundation & Architecture (Sprints 1-3)
- Phase 2: Core Feature Development (Sprints 4-7)
- Phase 3: Integration & Testing (Sprints 8-10)
- Phase 4: Launch Preparation & Deployment (Sprints 11-12)
</prompt>

---

## 5. Resource Allocation

### 5.1 Team Composition

<prompt>
Define team composition from:
- Resource planning and allocation
- Skill requirements and roles
- AWS and customer team structure

| Role | Name | Allocation % | Workstream(s) | Key Responsibilities |
|------|------|--------------|---------------|---------------------|
| TPM | [Name] | 100% | All | Program management, coordination |
| SDE3 | [Name] | 100% | [Workstream] | Technical leadership, architecture |
| SDE2 | [Name] | 100% | [Workstream] | Development, implementation |
| ... | ... | ... | ... | ... |

Include all AWS and customer team members with roles and allocation.
</prompt>

### 5.2 Capacity Planning

<prompt>
Calculate capacity from:
- Team size and allocation
- Sprint duration and velocity
- Story points and effort estimates

**Team Velocity**: <prompt>Calculate expected story points per sprint based on team size</prompt>

**Total Capacity**: <prompt>Calculate total story points across all sprints</prompt>

**Planned Work**: <prompt>Sum of all story points from epics</prompt>

**Buffer**: <prompt>Calculate buffer (typically 20% for unknowns and risks)</prompt>

**Capacity Utilization**: <prompt>Calculate planned work / total capacity percentage</prompt>

Ensure capacity utilization is 75-85% to allow for unknowns and risks.
</prompt>

### 5.3 Skill Requirements

<prompt>
Identify skill requirements from:
- Technology stack and architecture
- Development and testing needs
- Specialized expertise requirements

List required skills and availability:
- **Skill**: [Skill name]
- **Required Level**: [Junior/Mid/Senior/Expert]
- **Team Members**: [Who has this skill]
- **Gap**: [Any skill gaps identified]
- **Mitigation**: [How gaps will be addressed]

Identify any skill gaps and training or hiring needs.
</prompt>

---

## 6. Dependency Mapping

### 6.1 Internal Dependencies

<prompt>
Map internal dependencies from:
- Epic and story dependencies
- Workstream dependencies
- Technical dependencies and sequencing

Create dependency matrix:

| Dependent Item | Depends On | Type | Impact | Mitigation |
|----------------|------------|------|--------|------------|
| [Epic/Story] | [Epic/Story] | [Technical/Resource/Data] | [High/Med/Low] | [Mitigation approach] |

Identify all critical path dependencies.
</prompt>

### 6.2 External Dependencies

<prompt>
Identify external dependencies from:
- RAID log dependencies
- Third-party integrations and APIs
- Customer-provided resources or data
- External approvals or decisions

For each external dependency:

**Dependency [#]**: [Description]

**Owner**: <prompt>Who owns this dependency (external party)</prompt>

**Required By**: <prompt>When this dependency must be resolved (sprint/date)</prompt>

**Status**: <prompt>Current status of dependency</prompt>

**Risk**: <prompt>Risk if dependency is not met</prompt>

**Mitigation**: <prompt>Mitigation plan if dependency is delayed</prompt>

Include 5-10 critical external dependencies.
</prompt>

### 6.3 Dependency Management Plan

<prompt>
Define dependency management approach from:
- Governance framework and coordination
- Communication and escalation procedures
- Risk mitigation strategies

Include:
- **Tracking Mechanism**: How dependencies are tracked and monitored
- **Review Cadence**: How often dependencies are reviewed
- **Escalation Process**: How blocked dependencies are escalated
- **Mitigation Strategies**: Approaches to reduce dependency risks
</prompt>

---

## 7. Critical Path Analysis

<prompt>
Identify critical path from:
- Epic and story dependencies
- Timeline and milestone sequencing
- Resource constraints and bottlenecks

**Critical Path Items**: <prompt>List epics/stories on the critical path that cannot be delayed without impacting launch date</prompt>

**Critical Path Duration**: <prompt>Calculate total duration of critical path</prompt>

**Float/Buffer**: <prompt>Calculate available buffer before launch date is impacted</prompt>

**Risk Areas**: <prompt>Identify areas on critical path with highest risk</prompt>

**Mitigation Strategies**: <prompt>Define strategies to protect critical path (parallel work, early starts, resource prioritization)</prompt>

Visualize critical path:
```
Sprint 1-2: [Critical Epic 1] → Sprint 3-4: [Critical Epic 2] → Sprint 5-7: [Critical Epic 3] → Sprint 8-10: [Critical Epic 4] → Sprint 11-12: [Launch Activities]
```
</prompt>

---

## 8. Risk and Mitigation

<prompt>
Identify roadmap risks from:
- RAID log risk assessment
- Timeline and dependency risks
- Resource and capacity risks
- Technical and integration risks

For each major risk:

**Risk [#]**: [Description]

**Impact on Roadmap**: <prompt>How this risk could impact timeline or scope</prompt>

**Probability**: <prompt>Likelihood of risk occurring (High/Medium/Low)</prompt>

**Impact**: <prompt>Severity if risk occurs (High/Medium/Low)</prompt>

**Mitigation Strategy**: <prompt>How risk will be mitigated proactively</prompt>

**Contingency Plan**: <prompt>Backup plan if risk occurs</prompt>

**Owner**: <prompt>Who owns risk mitigation</prompt>

Include 5-8 major roadmap risks with mitigation strategies.
</prompt>

---

## Appendix A: Detailed Sprint Planning

<prompt>
Provide detailed sprint-by-sprint breakdown:

### Sprint [#]: [Sprint Name]

**Dates**: [Start Date] - [End Date]

**Sprint Goal**: <prompt>Define the sprint goal and focus</prompt>

**User Stories**: <prompt>List all user stories planned for this sprint with story points</prompt>
- US-[ID]: [Title] ([X] points) - [Workstream]

**Total Story Points**: [Sum]

**Key Deliverables**: <prompt>List key deliverables expected from this sprint</prompt>

**Dependencies**: <prompt>List any dependencies that must be resolved before or during this sprint</prompt>

**Risks**: <prompt>Identify any risks specific to this sprint</prompt>

Repeat for all sprints in the 6-month timeline.
</prompt>

---

**Document Review and Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| AWS TPM | <prompt>Extract TPM name</prompt> | | |
| AWS SDE3 | <prompt>Extract SDE3 name</prompt> | | |
| Customer Product Owner | <prompt>Extract Product Owner</prompt> | | |
| Customer Executive Sponsor | <prompt>Extract Executive Sponsor</prompt> | | |

**Change History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial Implementation Roadmap Canvas per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This Implementation Roadmap Canvas follows Build Like Amazon (BLA) prescriptive guidance for 6-month delivery.*

*For support: BLA Practice Team: bla-practice@amazon.com*
