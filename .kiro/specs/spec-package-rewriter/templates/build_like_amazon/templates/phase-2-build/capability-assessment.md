# Capability Assessment

<execution-notes>
This template generates a BLA-compliant Capability Assessment document.
The assessment analyzes current state technical and business capabilities to inform solution design.
Process all prompt blocks systematically using specification package data as the exclusive source.
Follow BLA best practices: comprehensive capability analysis, gap identification, readiness assessment.
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Assessment Date**: <prompt>Use current date</prompt>  
**Version**: 1.0  
**Status**: Draft

---

## Table of Contents

1. Executive Summary
2. Technical Capability Assessment
3. Business Capability Assessment
4. Organizational Capability Assessment
5. Gap Analysis
6. Readiness Assessment
7. Recommendations

---

## 1. Executive Summary

<prompt>
Generate executive summary (2-3 paragraphs) from:
- Overall capability assessment findings
- Critical gaps and strengths
- Readiness for transformation
- Key recommendations

Focus on strategic implications and readiness for BLA engagement.
</prompt>

---

## 2. Technical Capability Assessment

### 2.1 Current Technology Landscape

<prompt>
Assess current technology landscape from:
- Current state architecture and systems
- Technology stack and platforms
- Infrastructure and deployment
- Integration landscape

**Application Portfolio**:
<prompt>List current applications and systems:
- Application name, purpose, technology stack, age, condition
- Integration points and dependencies
- Performance and scalability characteristics
- Maintenance and support status
</prompt>

**Infrastructure**:
<prompt>Assess current infrastructure:
- On-premises vs. cloud deployment
- Server and compute resources
- Network architecture and connectivity
- Storage and database systems
- Disaster recovery and backup
</prompt>

**Integration Architecture**:
<prompt>Assess integration capabilities:
- Integration patterns and technologies
- API management and governance
- Data exchange formats and protocols
- Integration complexity and challenges
</prompt>
</prompt>

### 2.2 Technical Capabilities by Domain

<prompt>
Assess technical capabilities across domains from:
- Architecture documentation and current state
- Technical requirements and constraints
- Team skills and expertise

For each domain:

#### [Domain Name] (e.g., Cloud Infrastructure, Application Development, Data Management)

**Current Capability Level**: <prompt>Assess level: Advanced/Intermediate/Basic/None</prompt>

**Strengths**:
<prompt>List technical strengths in this domain:
- Specific capabilities that are mature
- Technologies or practices that work well
- Areas of expertise
</prompt>

**Weaknesses**:
<prompt>List technical weaknesses:
- Capability gaps or limitations
- Outdated technologies or practices
- Areas lacking expertise
</prompt>

**Tools and Technologies**:
<prompt>List current tools and technologies in this domain</prompt>

**Maturity Assessment**: <prompt>Assess maturity: Optimized/Managed/Defined/Repeatable/Initial</prompt>

Assess domains including:
- Cloud Infrastructure and Services
- Application Development and Frameworks
- Data Management and Analytics
- Security and Compliance
- DevOps and Automation
- Monitoring and Observability
- API and Integration
- Testing and Quality Assurance
</prompt>

### 2.3 Technical Debt Assessment

<prompt>
Assess technical debt from:
- Current state limitations and constraints
- Legacy systems and outdated technologies
- Architecture and code quality issues

**Technical Debt Inventory**:
<prompt>List major technical debt items:
- Legacy systems requiring modernization
- Outdated frameworks or libraries
- Architecture limitations
- Code quality issues
- Missing automation or tooling
</prompt>

**Impact Assessment**:
<prompt>Assess impact of technical debt:
- Development velocity impact
- Maintenance cost and effort
- Risk and reliability impact
- Innovation constraints
</prompt>

**Remediation Priority**:
<prompt>Prioritize technical debt remediation:
- Critical items blocking transformation
- High-value items enabling capabilities
- Lower priority items for future consideration
</prompt>
</prompt>

---

## 3. Business Capability Assessment

### 3.1 Business Process Maturity

<prompt>
Assess business process maturity from:
- Current state business processes
- Process documentation and standardization
- Automation and efficiency levels

For each major business process:

#### [Process Name]

**Current State**: <prompt>Describe current process and how it works</prompt>

**Maturity Level**: <prompt>Assess: Optimized/Managed/Defined/Repeatable/Initial</prompt>

**Automation Level**: <prompt>Assess: Fully Automated/Partially Automated/Manual</prompt>

**Pain Points**: <prompt>List process pain points and inefficiencies</prompt>

**Performance Metrics**: <prompt>Current performance metrics (time, cost, quality)</prompt>

**Improvement Opportunity**: <prompt>Potential for improvement (High/Medium/Low)</prompt>

Assess key business processes relevant to the solution.
</prompt>

### 3.2 Data and Analytics Capabilities

<prompt>
Assess data and analytics capabilities from:
- Current data management practices
- Analytics and reporting capabilities
- Data quality and governance

**Data Management**:
<prompt>Assess data management maturity:
- Data collection and storage
- Data quality and accuracy
- Data governance and stewardship
- Master data management
</prompt>

**Analytics and Reporting**:
<prompt>Assess analytics capabilities:
- Reporting tools and dashboards
- Analytics sophistication
- Data-driven decision making
- Real-time vs. batch analytics
</prompt>

**Data Quality**:
<prompt>Assess data quality:
- Accuracy and completeness
- Consistency and standardization
- Timeliness and freshness
- Data quality issues and impact
</prompt>
</prompt>

### 3.3 Business Agility

<prompt>
Assess business agility from:
- Speed of change and adaptation
- Innovation culture and practices
- Decision-making processes

**Change Velocity**:
<prompt>Assess how quickly business can adapt:
- Time to implement changes
- Flexibility to respond to market
- Innovation cycle time
</prompt>

**Decision-Making**:
<prompt>Assess decision-making effectiveness:
- Decision speed and quality
- Data-driven vs. intuition-based
- Empowerment and autonomy
</prompt>

**Innovation Culture**:
<prompt>Assess innovation maturity:
- Experimentation and learning
- Risk tolerance
- Customer-centric mindset
</prompt>
</prompt>

---

## 4. Organizational Capability Assessment

### 4.1 Team Skills and Expertise

<prompt>
Assess team skills from:
- Team composition and roles
- Skill inventory and expertise levels
- Training and development programs

**Current Team Composition**:
<prompt>Describe current team structure:
- Roles and responsibilities
- Team size and allocation
- Skill distribution
</prompt>

**Skill Assessment by Area**:
<prompt>For each skill area, assess current capability:

| Skill Area | Current Level | Team Members with Skill | Gap vs. Required | Priority |
|------------|---------------|------------------------|------------------|----------|
| Cloud (AWS) | [Basic/Int/Adv] | [Count] | [High/Med/Low] | [P0/P1/P2] |
| Serverless | [Basic/Int/Adv] | [Count] | [High/Med/Low] | [P0/P1/P2] |
| Microservices | [Basic/Int/Adv] | [Count] | [High/Med/Low] | [P0/P1/P2] |
| DevOps/CI/CD | [Basic/Int/Adv] | [Count] | [High/Med/Low] | [P0/P1/P2] |
| Security | [Basic/Int/Adv] | [Count] | [High/Med/Low] | [P0/P1/P2] |

Include 10-15 relevant skill areas.
</prompt>

**Skill Gaps**:
<prompt>Identify critical skill gaps:
- Skills required but not present
- Skills present but insufficient depth
- Skills needed for future state
</prompt>
</prompt>

### 4.2 Organizational Structure and Culture

<prompt>
Assess organizational factors from:
- Organizational structure and reporting
- Culture and ways of working
- Change readiness and adaptability

**Organizational Structure**:
<prompt>Assess structure effectiveness:
- Alignment with business objectives
- Decision-making authority and speed
- Cross-functional collaboration
- Silos and barriers
</prompt>

**Culture Assessment**:
<prompt>Assess cultural factors:
- Innovation and experimentation
- Customer obsession
- Ownership and accountability
- Learning and growth mindset
- Collaboration and transparency
</prompt>

**Ways of Working**:
<prompt>Assess current practices:
- Development methodology (Agile, Waterfall, hybrid)
- Collaboration tools and practices
- Meeting culture and effectiveness
- Documentation and knowledge sharing
</prompt>
</prompt>

### 4.3 Leadership and Governance

<prompt>
Assess leadership and governance from:
- Leadership engagement and support
- Governance structures and processes
- Decision-making effectiveness

**Leadership Engagement**:
<prompt>Assess leadership support:
- Executive sponsorship strength
- Leadership visibility and involvement
- Resource commitment
- Strategic alignment
</prompt>

**Governance Maturity**:
<prompt>Assess governance effectiveness:
- Governance structures and forums
- Decision-making processes
- Risk management
- Compliance and controls
</prompt>
</prompt>

---

## 5. Gap Analysis

### 5.1 Technical Capability Gaps

<prompt>
Identify technical gaps from capability assessment:

| Capability | Current State | Required State | Gap Size | Impact | Priority |
|------------|---------------|----------------|----------|--------|----------|
| [Capability] | [Level] | [Level] | [High/Med/Low] | [High/Med/Low] | [P0/P1/P2] |

Focus on gaps that must be closed for successful BLA engagement.
</prompt>

### 5.2 Business Capability Gaps

<prompt>
Identify business capability gaps:

| Capability | Current State | Required State | Gap Size | Impact | Priority |
|------------|---------------|----------------|----------|--------|----------|
| [Capability] | [Level] | [Level] | [High/Med/Low] | [High/Med/Low] | [P0/P1/P2] |

Focus on business process and data capability gaps.
</prompt>

### 5.3 Organizational Capability Gaps

<prompt>
Identify organizational gaps:

| Capability | Current State | Required State | Gap Size | Impact | Priority |
|------------|---------------|----------------|----------|--------|----------|
| [Capability] | [Level] | [Level] | [High/Med/Low] | [High/Med/Low] | [P0/P1/P2] |

Focus on skills, culture, and organizational structure gaps.
</prompt>

---

## 6. Readiness Assessment

### 6.1 Overall Readiness Score

<prompt>
Calculate overall readiness from capability assessment:

| Dimension | Score (0-100) | Weight | Weighted Score | Status |
|-----------|---------------|--------|----------------|--------|
| Technical Capability | [Score] | 35% | [Calc] | [Red/Yellow/Green] |
| Business Capability | [Score] | 25% | [Calc] | [Red/Yellow/Green] |
| Organizational Capability | [Score] | 25% | [Calc] | [Red/Yellow/Green] |
| Leadership & Governance | [Score] | 15% | [Calc] | [Red/Yellow/Green] |
| **Overall Readiness** | **[Total]** | **100%** | **[Total]** | **[Status]** |

Scoring:
- 80-100: Green (Ready)
- 60-79: Yellow (Ready with mitigation)
- <60: Red (Not ready, significant gaps)
</prompt>

### 6.2 Readiness by Phase

<prompt>
Assess readiness for each BLA phase:

**Envisioning & Discovery Phase**:
- **Readiness**: <prompt>Ready/Ready with mitigation/Not ready</prompt>
- **Gaps**: <prompt>List critical gaps for this phase</prompt>
- **Mitigation**: <prompt>How gaps will be addressed</prompt>

**Build Phase**:
- **Readiness**: <prompt>Ready/Ready with mitigation/Not ready</prompt>
- **Gaps**: <prompt>List critical gaps for this phase</prompt>
- **Mitigation**: <prompt>How gaps will be addressed</prompt>

**Launch Phase**:
- **Readiness**: <prompt>Ready/Ready with mitigation/Not ready</prompt>
- **Gaps**: <prompt>List critical gaps for this phase</prompt>
- **Mitigation**: <prompt>How gaps will be addressed</prompt>
</prompt>

### 6.3 Risk Assessment

<prompt>
Assess risks from capability gaps:

**High-Risk Areas**:
<prompt>Identify high-risk capability gaps:
- Gap description
- Risk to engagement success
- Mitigation strategy
- Contingency plan
</prompt>

**Medium-Risk Areas**:
<prompt>Identify medium-risk capability gaps with mitigation</prompt>

**Risk Mitigation Summary**:
<prompt>Summarize overall risk mitigation approach</prompt>
</prompt>

---

## 7. Recommendations

### 7.1 Immediate Actions (Pre-Engagement)

<prompt>
Recommend immediate actions from gap analysis:

**Priority 1 (Critical)**:
<prompt>List P0 actions required before engagement starts:
- Action description
- Rationale and impact
- Owner and timeline
- Success criteria
</prompt>

**Priority 2 (High)**:
<prompt>List P1 actions that should be addressed early</prompt>
</prompt>

### 7.2 Capability Building Plan

<prompt>
Recommend capability building approach:

**Training and Development**:
<prompt>Recommend training programs:
- Skill areas requiring training
- Training approach (formal, hands-on, mentoring)
- Timeline and resources
- Success metrics
</prompt>

**Knowledge Transfer**:
<prompt>Recommend knowledge transfer approach:
- AWS team to customer team transfer
- Documentation and enablement
- Hands-on collaboration
- Sustainability planning
</prompt>

**Hiring and Augmentation**:
<prompt>Recommend staffing changes if needed:
- Critical skill gaps requiring hiring
- Temporary augmentation needs
- Partner or contractor engagement
</prompt>
</prompt>

### 7.3 Organizational Changes

<prompt>
Recommend organizational changes from assessment:

**Structure Changes**:
<prompt>Recommend structure adjustments if needed</prompt>

**Process Changes**:
<prompt>Recommend process improvements</prompt>

**Cultural Changes**:
<prompt>Recommend cultural shifts needed for success</prompt>

**Governance Changes**:
<prompt>Recommend governance improvements</prompt>
</prompt>

---

**Document Review and Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| AWS TPM | <prompt>Extract TPM name</prompt> | | |
| AWS SDE3 | <prompt>Extract SDE3 name</prompt> | | |
| Customer Executive Sponsor | <prompt>Extract Executive Sponsor</prompt> | | |
| Customer Technical Lead | <prompt>Extract Technical Lead</prompt> | | |

**Change History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial Capability Assessment per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This Capability Assessment follows Build Like Amazon (BLA) prescriptive guidance.*

*For support: BLA Practice Team: bla-practice@amazon.com*
