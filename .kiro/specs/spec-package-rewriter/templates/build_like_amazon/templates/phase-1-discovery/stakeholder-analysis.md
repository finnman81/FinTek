# Stakeholder Analysis and Engagement Strategy

<execution-notes>
This template generates a BLA-compliant Stakeholder Analysis document.
The analysis identifies stakeholders, assesses their influence and interest, and defines engagement strategies.
Process all prompt blocks systematically using specification package data as the exclusive source.
Follow BLA best practices: comprehensive stakeholder mapping, proactive engagement, communication planning.
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Date**: <prompt>Use current date</prompt>  
**Version**: 1.0  
**Status**: Draft

---

## Table of Contents

1. Stakeholder Overview
2. Stakeholder Identification and Classification
3. Stakeholder Analysis Matrix
4. Engagement Strategy
5. Communication Plan
6. Stakeholder Management

---

## 1. Stakeholder Overview

### 1.1 Purpose

<prompt>
Define the purpose of stakeholder analysis from:
- Governance framework and stakeholder engagement requirements
- BLA engagement success factors
- Communication and alignment needs

Explain why stakeholder analysis is critical for BLA engagement success.
</prompt>

### 1.2 Stakeholder Categories

<prompt>
Define stakeholder categories from:
- Organizational structure and roles
- Decision-making authority and influence
- Project impact and involvement

Categories typically include:
- **Executive Sponsors**: Strategic oversight and resource commitment
- **Decision Makers**: Authority to approve scope, budget, timeline
- **Product Owners**: Product vision and requirements prioritization
- **Technical Leaders**: Architecture and technical decisions
- **Implementation Team**: Development and delivery
- **End Users**: Solution users and beneficiaries
- **Support Teams**: Operations, maintenance, support
- **External Partners**: Third-party vendors, integrators
</prompt>

---

## 2. Stakeholder Identification and Classification

<prompt>
Identify all stakeholders from:
- Stakeholder information in specification package
- Governance framework and organizational structure
- LRP workshop participants
- Team composition and resource allocation

For each stakeholder:

### Stakeholder [#]: [Name]

**Role/Title**: <prompt>Extract role and title</prompt>

**Organization**: <prompt>Extract organization/department</prompt>

**Category**: <prompt>Assign category: Executive Sponsor/Decision Maker/Product Owner/Technical Leader/Implementation Team/End User/Support Team/External Partner</prompt>

**Responsibilities**: <prompt>List key responsibilities related to this project</prompt>

**Decision Authority**: <prompt>Describe decision-making authority (Strategic/Tactical/Operational/None)</prompt>

**Project Impact**: <prompt>How this project impacts them (High/Medium/Low)</prompt>

**Influence Level**: <prompt>Their ability to influence project success (High/Medium/Low)</prompt>

**Interest Level**: <prompt>Their interest in project success (High/Medium/Low)</prompt>

**Support Level**: <prompt>Current support for project (Champion/Supporter/Neutral/Skeptic/Blocker)</prompt>

**Key Concerns**: <prompt>List their primary concerns or priorities</prompt>

**Success Criteria**: <prompt>What success looks like from their perspective</prompt>

**Contact Information**: <prompt>Email, phone, preferred communication method</prompt>

Identify 15-25 key stakeholders across all categories.
</prompt>

---

## 3. Stakeholder Analysis Matrix

### 3.1 Power-Interest Grid

<prompt>
Plot stakeholders on Power-Interest grid from stakeholder analysis:

**High Power, High Interest (Manage Closely)**:
<prompt>List stakeholders who have high influence and high interest - these require close management and frequent engagement</prompt>

**High Power, Low Interest (Keep Satisfied)**:
<prompt>List stakeholders who have high influence but lower interest - keep them satisfied with key updates</prompt>

**Low Power, High Interest (Keep Informed)**:
<prompt>List stakeholders who have lower influence but high interest - keep them informed and engaged</prompt>

**Low Power, Low Interest (Monitor)**:
<prompt>List stakeholders who have lower influence and interest - monitor with minimal effort</prompt>

This grid informs engagement strategy and communication frequency.
</prompt>

### 3.2 Influence-Impact Matrix

<prompt>
Create Influence-Impact matrix:

| Stakeholder | Influence on Project | Impact from Project | Priority | Engagement Level |
|-------------|---------------------|---------------------|----------|------------------|
| [Name] | [High/Med/Low] | [High/Med/Low] | [P0/P1/P2] | [Daily/Weekly/Monthly] |

Priority calculation:
- P0: High Influence + High Impact
- P1: High Influence OR High Impact
- P2: Medium/Low Influence AND Medium/Low Impact
</prompt>

### 3.3 Support Assessment

<prompt>
Assess stakeholder support levels:

**Champions** (Active advocates):
<prompt>List stakeholders who actively champion the project</prompt>

**Supporters** (Positive but passive):
<prompt>List stakeholders who support but may not actively advocate</prompt>

**Neutral** (Undecided or indifferent):
<prompt>List stakeholders who are neutral</prompt>

**Skeptics** (Concerns or doubts):
<prompt>List stakeholders with concerns or doubts</prompt>

**Blockers** (Active resistance):
<prompt>List stakeholders who may actively resist or block</prompt>

For Skeptics and Blockers, identify:
- **Concerns**: What are their specific concerns?
- **Strategy**: How will concerns be addressed?
- **Target**: Move them to Neutral or Supporter status
</prompt>

---

## 4. Engagement Strategy

### 4.1 Engagement Approach by Stakeholder Type

<prompt>
Define engagement approach for each stakeholder category:

#### Executive Sponsors
**Engagement Frequency**: <prompt>Define frequency (monthly, quarterly)</prompt>  
**Engagement Method**: <prompt>Define method (executive briefings, steering committee)</prompt>  
**Key Messages**: <prompt>What messages resonate (business value, ROI, strategic alignment)</prompt>  
**Success Indicators**: <prompt>How to demonstrate success to executives</prompt>

#### Decision Makers
**Engagement Frequency**: <prompt>Define frequency (bi-weekly, monthly)</prompt>  
**Engagement Method**: <prompt>Define method (decision reviews, approval sessions)</prompt>  
**Key Messages**: <prompt>What messages resonate (progress, risks, decisions needed)</prompt>  
**Success Indicators**: <prompt>How to demonstrate success to decision makers</prompt>

#### Product Owners
**Engagement Frequency**: <prompt>Define frequency (daily, per sprint)</prompt>  
**Engagement Method**: <prompt>Define method (sprint reviews, backlog grooming)</prompt>  
**Key Messages**: <prompt>What messages resonate (features, user value, priorities)</prompt>  
**Success Indicators**: <prompt>How to demonstrate success to product owners</prompt>

#### Technical Leaders
**Engagement Frequency**: <prompt>Define frequency (daily, weekly)</prompt>  
**Engagement Method**: <prompt>Define method (architecture reviews, technical discussions)</prompt>  
**Key Messages**: <prompt>What messages resonate (technical approach, quality, innovation)</prompt>  
**Success Indicators**: <prompt>How to demonstrate success to technical leaders</prompt>

#### Implementation Team
**Engagement Frequency**: <prompt>Define frequency (daily)</prompt>  
**Engagement Method**: <prompt>Define method (standups, sprint ceremonies, collaboration)</prompt>  
**Key Messages**: <prompt>What messages resonate (clarity, support, recognition)</prompt>  
**Success Indicators**: <prompt>How to demonstrate success to team</prompt>

#### End Users
**Engagement Frequency**: <prompt>Define frequency (per milestone, UAT)</prompt>  
**Engagement Method**: <prompt>Define method (user testing, feedback sessions, training)</prompt>  
**Key Messages**: <prompt>What messages resonate (ease of use, benefits, support)</prompt>  
**Success Indicators**: <prompt>How to demonstrate success to users</prompt>
</prompt>

### 4.2 Individual Stakeholder Engagement Plans

<prompt>
For top 10 priority stakeholders (P0 and key P1), create individual engagement plans:

#### [Stakeholder Name] - [Role]

**Priority**: <prompt>P0/P1</prompt>

**Engagement Objectives**: <prompt>What we need from this stakeholder (approval, input, support, resources)</prompt>

**Engagement Frequency**: <prompt>How often to engage (daily, weekly, bi-weekly, monthly)</prompt>

**Engagement Methods**: <prompt>Specific methods (1-on-1 meetings, email updates, presentations, workshops)</prompt>

**Key Messages**: <prompt>Tailored messages that resonate with this stakeholder</prompt>

**Concerns to Address**: <prompt>Specific concerns this stakeholder has</prompt>

**Success Indicators**: <prompt>How to know engagement is successful</prompt>

**Owner**: <prompt>Who owns this stakeholder relationship (typically TPM or specific team member)</prompt>
</prompt>

---

## 5. Communication Plan

### 5.1 Communication Channels

<prompt>
Define communication channels from:
- Governance framework communication protocols
- Stakeholder preferences and organizational norms
- Tool availability and access

**Formal Channels**:
- **Steering Committee Meetings**: <prompt>Frequency, participants, purpose</prompt>
- **Executive Briefings**: <prompt>Frequency, participants, purpose</prompt>
- **Sprint Reviews**: <prompt>Frequency, participants, purpose</prompt>
- **Status Reports**: <prompt>Frequency, distribution, format</prompt>

**Informal Channels**:
- **Slack/Teams Channels**: <prompt>Channel names, purposes, participants</prompt>
- **Email Distribution Lists**: <prompt>List names, purposes, participants</prompt>
- **1-on-1 Meetings**: <prompt>Frequency, participants</prompt>
- **Ad-hoc Discussions**: <prompt>When and how</prompt>

**Collaboration Tools**:
- **Project Management**: <prompt>Tool name (Jira, etc.), access, usage</prompt>
- **Documentation**: <prompt>Tool name (Confluence, SharePoint, etc.), access</prompt>
- **Code Repository**: <prompt>Tool name (GitHub, etc.), access</prompt>
</prompt>

### 5.2 Communication Matrix

<prompt>
Create communication matrix:

| Communication Type | Audience | Frequency | Owner | Channel | Purpose |
|-------------------|----------|-----------|-------|---------|---------|
| Executive Dashboard | Executive Sponsors | Monthly | TPM | Email + Presentation | Strategic updates, ROI |
| Steering Committee | Decision Makers | Bi-weekly | TPM | Meeting | Decisions, risks, escalations |
| Sprint Review | Product Owners, Stakeholders | Per Sprint | SDE3 | Meeting | Demo, feedback, acceptance |
| Status Report | All Stakeholders | Weekly | TPM | Email | Progress, risks, issues |
| Technical Review | Technical Leaders | Weekly | SDE3 | Meeting | Architecture, technical decisions |
| Daily Standup | Implementation Team | Daily | Scrum Master | Meeting | Coordination, blockers |
| User Feedback Session | End Users | Per Milestone | Product Owner | Workshop | Validation, feedback |

Include 10-15 communication types covering all stakeholder groups.
</prompt>

### 5.3 Communication Content and Messaging

<prompt>
Define communication content by audience:

**Executive Audience**:
- **Focus**: Business value, ROI, strategic alignment, risks
- **Format**: Executive summary, dashboards, high-level metrics
- **Tone**: Strategic, outcome-focused, concise
- **Frequency**: Monthly or quarterly

**Technical Audience**:
- **Focus**: Architecture, technical decisions, quality, innovation
- **Format**: Technical documentation, architecture diagrams, code reviews
- **Tone**: Technical, detailed, collaborative
- **Frequency**: Daily or weekly

**Business Audience**:
- **Focus**: Features, user value, business outcomes, timeline
- **Format**: Feature demos, user stories, business metrics
- **Tone**: Business-focused, user-centric, practical
- **Frequency**: Per sprint or bi-weekly

**User Audience**:
- **Focus**: Ease of use, benefits, training, support
- **Format**: User guides, training materials, FAQs
- **Tone**: User-friendly, supportive, clear
- **Frequency**: Per milestone or as needed
</prompt>

---

## 6. Stakeholder Management

### 6.1 Relationship Management

<prompt>
Define relationship management approach from:
- Governance framework and stakeholder engagement
- BLA best practices for stakeholder alignment
- Change management and adoption planning

**Building Trust**:
- **Transparency**: <prompt>How transparency is maintained (open communication, honest updates)</prompt>
- **Reliability**: <prompt>How reliability is demonstrated (meeting commitments, consistent delivery)</prompt>
- **Responsiveness**: <prompt>How responsiveness is ensured (timely responses, addressing concerns)</prompt>

**Managing Expectations**:
- **Clear Commitments**: <prompt>How commitments are made and tracked</prompt>
- **Realistic Timelines**: <prompt>How realistic expectations are set</prompt>
- **Scope Management**: <prompt>How scope changes are managed</prompt>

**Conflict Resolution**:
- **Early Detection**: <prompt>How conflicts are detected early</prompt>
- **Resolution Process**: <prompt>Process for resolving stakeholder conflicts</prompt>
- **Escalation Path**: <prompt>When and how conflicts are escalated</prompt>
</prompt>

### 6.2 Change Management

<prompt>
Define change management approach from:
- Organizational change requirements
- User adoption and training needs
- Stakeholder readiness assessment

**Readiness Assessment**:
- **Current State**: <prompt>Assess organizational readiness for change</prompt>
- **Change Impact**: <prompt>Assess impact of change on different stakeholder groups</prompt>
- **Resistance Points**: <prompt>Identify potential resistance points</prompt>

**Change Strategy**:
- **Communication**: <prompt>How change is communicated to stakeholders</prompt>
- **Training**: <prompt>Training approach for different stakeholder groups</prompt>
- **Support**: <prompt>Support mechanisms during transition</prompt>
- **Adoption Metrics**: <prompt>How adoption is measured</prompt>

**Resistance Management**:
- **Identification**: <prompt>How resistance is identified</prompt>
- **Root Cause**: <prompt>Understanding root causes of resistance</prompt>
- **Mitigation**: <prompt>Strategies to address resistance</prompt>
</prompt>

### 6.3 Feedback and Continuous Improvement

<prompt>
Define feedback mechanisms from:
- Stakeholder engagement and satisfaction
- Continuous improvement processes
- Governance framework review cycles

**Feedback Collection**:
- **Methods**: <prompt>How feedback is collected (surveys, interviews, retrospectives)</prompt>
- **Frequency**: <prompt>How often feedback is collected</prompt>
- **Analysis**: <prompt>How feedback is analyzed and prioritized</prompt>

**Action on Feedback**:
- **Review Process**: <prompt>How feedback is reviewed and acted upon</prompt>
- **Communication**: <prompt>How actions on feedback are communicated back to stakeholders</prompt>
- **Tracking**: <prompt>How feedback actions are tracked to completion</prompt>

**Stakeholder Satisfaction**:
- **Measurement**: <prompt>How stakeholder satisfaction is measured</prompt>
- **Targets**: <prompt>Satisfaction targets and thresholds</prompt>
- **Improvement**: <prompt>How satisfaction drives continuous improvement</prompt>
</prompt>

---

## Appendix A: Stakeholder Contact Directory

<prompt>
Create comprehensive stakeholder contact directory:

| Name | Role | Organization | Email | Phone | Preferred Contact Method | Availability |
|------|------|--------------|-------|-------|-------------------------|--------------|
| [Name] | [Role] | [Org] | [Email] | [Phone] | [Email/Phone/Slack] | [Timezone/Hours] |

Include all identified stakeholders with complete contact information.
</prompt>

---

## Appendix B: RACI Matrix

<prompt>
Create RACI matrix for key decisions and activities:

| Activity/Decision | [Stakeholder 1] | [Stakeholder 2] | [Stakeholder 3] | ... |
|-------------------|-----------------|-----------------|-----------------|-----|
| Architecture Approval | R | A | C | I |
| Sprint Planning | A | R | C | I |
| Budget Approval | I | A | R | C |
| Go-Live Decision | C | A | R | I |

Legend:
- R = Responsible (does the work)
- A = Accountable (final approval)
- C = Consulted (provides input)
- I = Informed (kept updated)

Include 15-20 key activities and decisions.
</prompt>

---

**Document Review and Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| AWS TPM | <prompt>Extract TPM name</prompt> | | |
| Customer Executive Sponsor | <prompt>Extract Executive Sponsor</prompt> | | |
| Customer Product Owner | <prompt>Extract Product Owner</prompt> | | |

**Change History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial Stakeholder Analysis per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This Stakeholder Analysis follows Build Like Amazon (BLA) prescriptive guidance.*

*For support: BLA Practice Team: bla-practice@amazon.com*
