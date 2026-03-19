# RAID Log (Risks, Assumptions, Issues, Dependencies)

<execution-notes>
This template generates a BLA-compliant RAID Log for tracking risks, assumptions, issues, and dependencies.
The RAID Log is a living document that should be updated regularly throughout the engagement.
Process all prompt blocks systematically using specification package data as the exclusive source.
Follow BLA best practices: proactive risk management, assumption validation, issue resolution, dependency tracking.
Note: Architecture and technical decisions should be captured in Architecture Decision Records (ADRs), not in this RAID log.
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Date**: <prompt>Use current date</prompt>  
**Owner**: <prompt>Extract TPM or project owner name</prompt>  
**Review Frequency**: <prompt>Define review frequency (typically weekly or per sprint)</prompt>  
**Version**: 1.0  
**Status**: Active

---

## Table of Contents

1. RAID Log Overview
2. Risks
3. Assumptions
4. Issues
5. Dependencies
6. RAID Summary Dashboard

---

## 1. RAID Log Overview

### 1.1 Purpose

This RAID Log captures and tracks Risks, Assumptions, Issues, and Dependencies for the BLA engagement. It serves as a central repository for proactive risk management and issue resolution.

**Note**: Architecture and technical decisions are documented separately in Architecture Decision Records (ADRs). This RAID log focuses on project, governance, business, and operational items.

### 1.2 Management Process

<prompt>
Define RAID management process from:
- Governance framework and review cadence
- Escalation procedures and decision-making
- Update and maintenance responsibilities

Include:
- **Review Cadence**: How often RAID log is reviewed (weekly sprint reviews, steering committee meetings)
- **Update Process**: How new items are added and existing items updated
- **Escalation**: When and how items are escalated to leadership
- **Closure Criteria**: When items can be marked as closed
- **Ownership**: Who owns overall RAID log maintenance (typically TPM)
</prompt>

---

## 2. Risks

### 2.1 Risk Assessment Matrix

**Risk Scoring**:
- **Probability**: High (>60%), Medium (30-60%), Low (<30%)
- **Impact**: High (Critical to success), Medium (Significant impact), Low (Minor impact)
- **Priority**: P0 (High/High), P1 (High/Med or Med/High), P2 (All others)

### 2.2 Active Risks

<prompt>
Identify risks from:
- Risk assessment and analysis
- RAID log from LRP workshop
- Technical risks and challenges
- Business and organizational risks
- Timeline and resource risks

For each risk, create an entry:

**R-[ID]**: [Risk Title]

**Description**: <prompt>Detailed description of the risk</prompt>

**Category**: <prompt>Assign category: Technical/Business/Resource/Timeline/External/Organizational</prompt>

**Probability**: <prompt>Assess probability: High/Medium/Low</prompt>

**Impact**: <prompt>Assess impact: High/Medium/Low</prompt>

**Priority**: <prompt>Calculate priority: P0/P1/P2</prompt>

**Owner**: <prompt>Assign risk owner responsible for mitigation</prompt>

**Mitigation Strategy**: <prompt>Describe proactive mitigation approach</prompt>

**Contingency Plan**: <prompt>Describe backup plan if risk occurs</prompt>

**Status**: <prompt>Current status: Open/In Progress/Mitigated/Closed</prompt>

**Date Identified**: <prompt>When risk was identified</prompt>

**Target Resolution**: <prompt>When mitigation should be complete</prompt>

**Last Updated**: <prompt>Last update date</prompt>

**Remarks**: <prompt>Additional notes, updates, or context</prompt>

Identify 10-15 major risks across all categories.
Prioritize P0 and P1 risks for immediate attention.
</prompt>

### 2.3 Risk Summary by Category

<prompt>
Summarize risks by category:

| Category | Total | P0 | P1 | P2 | Open | Mitigated |
|----------|-------|----|----|----|----|-----------|
| Technical | [#] | [#] | [#] | [#] | [#] | [#] |
| Business | [#] | [#] | [#] | [#] | [#] | [#] |
| Resource | [#] | [#] | [#] | [#] | [#] | [#] |
| Timeline | [#] | [#] | [#] | [#] | [#] | [#] |
| External | [#] | [#] | [#] | [#] | [#] | [#] |
| **Total** | [#] | [#] | [#] | [#] | [#] | [#] |
</prompt>

---

## 3. Assumptions

### 3.1 Active Assumptions

<prompt>
Identify assumptions from:
- Requirements and planning assumptions
- Technical assumptions and constraints
- Resource and timeline assumptions
- Business and stakeholder assumptions

For each assumption, create an entry:

**A-[ID]**: [Assumption Title]

**Description**: <prompt>Detailed description of the assumption</prompt>

**Category**: <prompt>Assign category: Technical/Business/Resource/Timeline/External</prompt>

**Impact if Invalid**: <prompt>Assess impact if assumption proves false: High/Medium/Low</prompt>

**Validation Method**: <prompt>How this assumption will be validated</prompt>

**Validation Owner**: <prompt>Who is responsible for validating this assumption</prompt>

**Validation Target Date**: <prompt>When assumption should be validated</prompt>

**Status**: <prompt>Current status: Unvalidated/In Validation/Validated/Invalid</prompt>

**Date Identified**: <prompt>When assumption was identified</prompt>

**Last Updated**: <prompt>Last update date</prompt>

**Remarks**: <prompt>Validation results, updates, or context</prompt>

Identify 8-12 critical assumptions that require validation.
Prioritize assumptions with high impact if invalid.
</prompt>

### 3.2 Assumption Validation Plan

<prompt>
Create validation plan for high-impact assumptions:

| Assumption ID | Validation Method | Owner | Target Date | Status |
|---------------|-------------------|-------|-------------|--------|
| A-[ID] | [Method] | [Owner] | [Date] | [Status] |

Focus on assumptions that must be validated early to avoid downstream risks.
</prompt>

---

## 4. Issues

### 4.1 Active Issues

<prompt>
Identify current issues from:
- Blockers and impediments
- Technical issues and bugs
- Resource or organizational issues
- Stakeholder or communication issues

For each issue, create an entry:

**I-[ID]**: [Issue Title]

**Description**: <prompt>Detailed description of the issue</prompt>

**Category**: <prompt>Assign category: Technical/Business/Resource/Communication/External</prompt>

**Impact**: <prompt>Assess impact on project: High/Medium/Low</prompt>

**Priority**: <prompt>Assign priority: P0/P1/P2</prompt>

**Owner**: <prompt>Assign issue owner responsible for resolution</prompt>

**Resolution Plan**: <prompt>Describe plan to resolve the issue</prompt>

**Status**: <prompt>Current status: Open/In Progress/Resolved/Closed</prompt>

**Date Identified**: <prompt>When issue was identified</prompt>

**Target Resolution**: <prompt>When issue should be resolved</prompt>

**Last Updated**: <prompt>Last update date</prompt>

**Remarks**: <prompt>Resolution progress, updates, or context</prompt>

Identify all active issues blocking or impeding progress.
P0 issues should be escalated immediately.
</prompt>

### 4.2 Issue Escalation

<prompt>
Define escalation process for issues:

**P0 Issues (Critical)**:
- **Escalation Trigger**: Immediate escalation for critical blockers
- **Escalation Path**: <prompt>Define escalation path (TPM → SDM → Executive Sponsor)</prompt>
- **Response Time**: <prompt>Expected response time (e.g., within 4 hours)</prompt>

**P1 Issues (High)**:
- **Escalation Trigger**: If not resolved within [X] days
- **Escalation Path**: <prompt>Define escalation path</prompt>
- **Response Time**: <prompt>Expected response time (e.g., within 24 hours)</prompt>

**P2 Issues (Medium)**:
- **Escalation Trigger**: If not resolved within [X] days
- **Escalation Path**: <prompt>Define escalation path</prompt>
- **Response Time**: <prompt>Expected response time (e.g., within 1 week)</prompt>
</prompt>

---

## 5. Dependencies

### 5.1 Active Dependencies

<prompt>
Identify dependencies from:
- Implementation roadmap dependencies
- External dependencies and integrations
- Resource dependencies
- Decision dependencies

For each dependency, create an entry:

**D-[ID]**: [Dependency Title]

**Description**: <prompt>Detailed description of the dependency</prompt>

**Type**: <prompt>Assign type: Technical/Resource/External/Decision/Data</prompt>

**Dependent Item**: <prompt>What depends on this (epic, story, milestone)</prompt>

**Dependency Source**: <prompt>What this depends on (external system, team, decision, resource)</prompt>

**Owner**: <prompt>Who owns managing this dependency</prompt>

**Required By**: <prompt>When this dependency must be resolved (sprint/date)</prompt>

**Impact if Not Met**: <prompt>Impact if dependency is not met: High/Medium/Low</prompt>

**Status**: <prompt>Current status: Pending/In Progress/Resolved/Blocked</prompt>

**Mitigation Plan**: <prompt>Backup plan if dependency is delayed or not met</prompt>

**Date Identified**: <prompt>When dependency was identified</prompt>

**Last Updated**: <prompt>Last update date</prompt>

**Remarks**: <prompt>Progress updates, coordination notes, or context</prompt>

Identify 10-15 critical dependencies across internal and external sources.
Focus on dependencies on the critical path.
</prompt>

### 5.2 Dependency Management

<prompt>
Define dependency management approach:

**Tracking and Coordination**:
- **Dependency Review**: <prompt>How often dependencies are reviewed (weekly, per sprint)</prompt>
- **Coordination Mechanism**: <prompt>How dependencies are coordinated (meetings, communication channels)</prompt>
- **Status Updates**: <prompt>How dependency status is communicated</prompt>

**Risk Mitigation**:
- **Early Identification**: <prompt>Process for identifying dependencies early</prompt>
- **Proactive Management**: <prompt>How dependencies are managed proactively</prompt>
- **Contingency Planning**: <prompt>Backup plans for critical dependencies</prompt>
</prompt>

---

## 6. RAID Summary Dashboard

### 6.1 Overall RAID Status

<prompt>
Create summary dashboard:

| RAID Type | Total | Open/Active | In Progress | Resolved/Closed | P0 | P1 | P2 |
|-----------|-------|-------------|-------------|-----------------|----|----|-----|
| **Risks** | [#] | [#] | [#] | [#] | [#] | [#] | [#] |
| **Assumptions** | [#] | [#] | [#] | [#] | [#] | [#] | [#] |
| **Issues** | [#] | [#] | [#] | [#] | [#] | [#] | [#] |
| **Dependencies** | [#] | [#] | [#] | [#] | [#] | [#] | [#] |
| **Total** | [#] | [#] | [#] | [#] | [#] | [#] | [#] |
</prompt>

### 6.2 Critical Items Requiring Attention

<prompt>
Highlight critical items requiring immediate attention:

**P0 Risks**: <prompt>List all P0 risks with owners and target resolution dates</prompt>

**P0 Issues**: <prompt>List all P0 issues with owners and target resolution dates</prompt>

**High-Impact Assumptions**: <prompt>List unvalidated assumptions with high impact if invalid</prompt>

**Critical Path Dependencies**: <prompt>List dependencies on critical path that are pending or blocked</prompt>
</prompt>

### 6.3 Trend Analysis

<prompt>
Provide trend analysis if historical data available:

**Risk Trends**:
- New risks identified this period: [#]
- Risks mitigated this period: [#]
- Net change: [+/-#]
- Trend: [Improving/Stable/Worsening]

**Issue Trends**:
- New issues identified this period: [#]
- Issues resolved this period: [#]
- Net change: [+/-#]
- Average resolution time: [X days]
- Trend: [Improving/Stable/Worsening]

**Dependency Trends**:
- New dependencies identified this period: [#]
- Dependencies resolved this period: [#]
- Net change: [+/-#]
- Blocked dependencies: [#]
- Trend: [Improving/Stable/Worsening]
</prompt>

---

## Appendix A: RAID Log Template

<prompt>
Provide blank template for adding new RAID items:

### Risk Template
**R-[ID]**: [Risk Title]  
**Description**: [Detailed description]  
**Category**: [Technical/Business/Resource/Timeline/External/Organizational]  
**Probability**: [High/Medium/Low]  
**Impact**: [High/Medium/Low]  
**Priority**: [P0/P1/P2]  
**Owner**: [Name]  
**Mitigation Strategy**: [Description]  
**Contingency Plan**: [Description]  
**Status**: [Open/In Progress/Mitigated/Closed]  
**Date Identified**: [Date]  
**Target Resolution**: [Date]  
**Last Updated**: [Date]  
**Remarks**: [Notes]

### Assumption Template
**A-[ID]**: [Assumption Title]  
**Description**: [Detailed description]  
**Category**: [Technical/Business/Resource/Timeline/External]  
**Impact if Invalid**: [High/Medium/Low]  
**Validation Method**: [Description]  
**Validation Owner**: [Name]  
**Validation Target Date**: [Date]  
**Status**: [Unvalidated/In Validation/Validated/Invalid]  
**Date Identified**: [Date]  
**Last Updated**: [Date]  
**Remarks**: [Notes]

### Issue Template
**I-[ID]**: [Issue Title]  
**Description**: [Detailed description]  
**Category**: [Technical/Business/Resource/Communication/External]  
**Impact**: [High/Medium/Low]  
**Priority**: [P0/P1/P2]  
**Owner**: [Name]  
**Resolution Plan**: [Description]  
**Status**: [Open/In Progress/Resolved/Closed]  
**Date Identified**: [Date]  
**Target Resolution**: [Date]  
**Last Updated**: [Date]  
**Remarks**: [Notes]

### Dependency Template
**D-[ID]**: [Dependency Title]  
**Description**: [Detailed description]  
**Type**: [Technical/Resource/External/Decision/Data]  
**Dependent Item**: [What depends on this]  
**Dependency Source**: [What this depends on]  
**Owner**: [Name]  
**Required By**: [Sprint/Date]  
**Impact if Not Met**: [High/Medium/Low]  
**Status**: [Pending/In Progress/Resolved/Blocked]  
**Mitigation Plan**: [Description]  
**Date Identified**: [Date]  
**Last Updated**: [Date]  
**Remarks**: [Notes]
</prompt>

---

**Document Review and Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| AWS TPM (Owner) | <prompt>Extract TPM name</prompt> | | |
| AWS SDM (Reviewer) | <prompt>Extract SDM name</prompt> | | |
| Customer Product Owner | <prompt>Extract Product Owner</prompt> | | |

**Change History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial RAID Log per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This RAID Log follows Build Like Amazon (BLA) prescriptive guidance.*

*Note: Architecture and technical decisions should be documented in Architecture Decision Records (ADRs), not in this RAID log.*

*For support: BLA Practice Team: bla-practice@amazon.com*
