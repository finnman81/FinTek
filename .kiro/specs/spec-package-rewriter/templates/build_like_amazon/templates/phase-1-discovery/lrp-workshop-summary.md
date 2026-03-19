# Launch Ready Planning (LRP) Workshop Summary

<execution-notes>
This template generates a BLA-compliant Launch Ready Planning Workshop Summary document.
The LRP Workshop is the foundation for BLA engagements, aligning stakeholders on customer business outcomes and creating detailed implementation roadmaps.
Process all prompt blocks systematically using specification package data as the exclusive source.
Follow BLA best practices: Working Backwards methodology, stakeholder alignment, granular traceability to business outcomes.
</execution-notes>

**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Workshop Date**: <prompt>Extract workshop date or use current date</prompt>  
**Workshop Duration**: <prompt>Extract workshop duration (typically 2-3 days)</prompt>  
**Facilitators**: <prompt>Extract AWS facilitator names (TPM + SDE3 pairing)</prompt>  
**Participants**: <prompt>Extract participant count and key stakeholder names</prompt>  
**Project**: <prompt>Extract project name from specification package</prompt>  
**Version**: 1.0  
**Status**: <prompt>Assign status: Draft/Under Review/Approved</prompt>

## Table of Contents

1. Executive Summary
2. Workshop Objectives and Outcomes
3. Participant Overview
4. Workshop Agenda and Activities
5. Key Deliverables Summary
6. Stakeholder Alignment and Confidence Voting
7. Next Steps and Action Items
8. Appendices

---

## 1. Executive Summary

<prompt>
Generate executive summary (2-3 paragraphs) from:
- Workshop objectives and outcomes achieved
- Customer Business Outcomes Canvas summary
- Implementation roadmap overview
- Stakeholder alignment and confidence levels
- Critical success factors and next steps

Focus on business value, stakeholder alignment, and readiness to proceed with BLA engagement.
</prompt>

---

## 2. Workshop Objectives and Outcomes

### 2.1 Workshop Objectives

<prompt>
Extract workshop objectives from:
- LRP workshop planning and goals
- Stakeholder expectations and success criteria
- BLA engagement scope and deliverables

List 5-7 key objectives for the LRP workshop:
1. Stakeholder Alignment: Achieve consensus on business outcomes and success metrics
2. Customer Business Outcome (CBO) Canvas Creation: Develop comprehensive understanding of challenges and solutions
3. Implementation Roadmap: Create detailed, time-bound plan for BLA implementation
4. Risk Identification: Capture and assess RAID (Risks, Assumptions, Issues, Dependencies)
5. Success Metrics Definition: Establish measurable criteria for engagement success
6. Team Ownership: Ensure all participants feel ownership of the plan and outcomes
</prompt>

### 2.2 Outcomes Achieved

<prompt>
Summarize outcomes achieved from:
- Completed workshop deliverables
- Stakeholder feedback and validation
- Confidence voting results
- Action items and commitments

Describe what was accomplished during the workshop and validation of objectives met.
</prompt>

---

## 3. Participant Overview

### 3.1 AWS Team

<prompt>
Extract AWS team composition from:
- Team structure and resource allocation
- Facilitator and participant information

- BLA engagement team roles and responsibilities

List AWS team members with roles:
- Technical Program Manager (TPM): Workshop facilitation, timeline management, deliverable quality
- Senior Software Development Engineer (SDE3): Technical leadership, architecture guidance
- Solutions Architect: AWS best practices, service selection
- Additional team members as applicable
</prompt>

### 3.2 Customer Team

<prompt>
Extract customer team composition from:
- Stakeholder analysis and governance framework
- Workshop participant information
- Decision-making authority documentation

List customer team members with roles:
- Executive Sponsor: Strategic alignment, resource commitment
- Product Owner: Product vision, requirements prioritization
- Technical Lead: Architecture decisions, technical feasibility
- Business Stakeholders: Business requirements, success criteria
- Development Team Representatives: Implementation planning, capacity assessment
</prompt>

### 3.3 Stakeholder Engagement Assessment

<prompt>
Assess stakeholder engagement from:
- Workshop participation and contribution levels
- Confidence voting results
- Feedback and validation sessions

Describe engagement quality, participation levels, and stakeholder commitment to outcomes.
</prompt>

---

## 4. Workshop Agenda and Activities

### Day 1: Foundation and Discovery

#### Session 1: Workshop Introduction and Working Backwards Overview (2 hours)

<prompt>
Summarize introduction session from:
- Workshop kickoff materials
- Working Backwards methodology training
- BLA engagement overview and expectations

Include:
- Workshop objectives and agenda overview
- Working Backwards methodology explanation
- Amazon Leadership Principles and customer obsession focus
- BLA 6-month delivery commitment and approach
- Participant introductions and expectations setting
</prompt>

#### Session 2: Customer Business Outcome (CBO) Canvas Development (3 hours)

<prompt>
Summarize CBO Canvas development from:
- Customer Business Outcomes Canvas
- Customer profile and business model discussion
- Challenge quantification and pain point analysis
- Solution approach and expected results

Include key discussions, insights, and CBO Canvas outcomes.
</prompt>

#### Session 3: How Might We Statements and Problem/Solution Framing (2 hours)

<prompt>
Summarize How Might We and Problem/Solution work from:
- How Might We statements canvas
- Problem/Solution Canvas
- Innovation opportunity framing
- Solution ideation and prioritization

Include prioritized HMW statements and problem/solution definitions.
</prompt>

### Day 2: Planning and Roadmap Development

#### Session 4: Working Backwards Press Release and FAQ (2 hours)

<prompt>
Summarize Working Backwards artifacts from:
- Working Backwards Press Release
- Working Backwards FAQ
- Future state vision and customer testimonial
- Customer questions and clarifications

Include press release highlights and key FAQ themes.
</prompt>

#### Session 5: Implementation Roadmap Development (3 hours)

<prompt>
Summarize roadmap development from:
- Implementation Roadmap Canvas
- Workstream organization and epic breakdown
- Timeline with milestones and dependencies
- Resource allocation and capacity planning

Include roadmap structure, key milestones, and critical path.
</prompt>

#### Session 6: RAID Log and Risk Assessment (2 hours)

<prompt>
Summarize risk assessment from:
- RAID Log Canvas
- Risk identification and impact assessment
- Mitigation strategies and ownership
- Assumptions, issues, and dependencies

Include high-priority risks and mitigation approaches.
</prompt>

### Day 3: Validation and Commitment

#### Session 7: Success Metrics Definition (2 hours)

<prompt>
Summarize success metrics work from:
- Success Metrics Canvas
- Controllable input metrics (leading indicators)
- Business outcome metrics (lagging indicators)
- Measurement plan and ownership

Include key metrics, baselines, and targets.
</prompt>

#### Session 8: Workstream Presentations and Integration (2 hours)

<prompt>
Summarize workstream presentations from:
- Workstream roadmap presentations
- Cross-team feedback and dependency validation
- Integration and sequencing adjustments
- End-to-end roadmap review

Include integration outcomes and adjustments made.
</prompt>

#### Session 9: Stakeholder Alignment and Confidence Voting (1 hour)

<prompt>
Summarize alignment session from:
- Fist of Five confidence voting results
- Stakeholder concerns and mitigation actions
- Commitment levels and sign-off
- Governance structure establishment

Include confidence scores and commitment outcomes.
</prompt>

---

## 5. Key Deliverables Summary

### 5.1 Customer Business Outcome (CBO) Canvas

<prompt>
Provide high-level summary of CBO Canvas from:
- Customer Business Outcomes Canvas document
- Customer profile, challenges, solutions, and results
- CBO Elevator Level achieved (target Level 4-5)
- Quantified business outcomes and success metrics

Include link to full CBO Canvas document.
</prompt>

### 5.2 Implementation Roadmap

<prompt>
Provide high-level summary of Implementation Roadmap from:
- Implementation Roadmap Canvas document
- Workstream organization and timeline
- Key milestones and delivery phases
- Resource allocation and dependencies

Include link to full Implementation Roadmap document.
</prompt>

### 5.3 RAID Log

<prompt>
Provide summary of RAID Log from:
- RAID Log Canvas document
- High-priority risks and mitigation strategies
- Critical assumptions requiring validation
- Key dependencies and issues

Include link to full RAID Log document.
</prompt>

### 5.4 Working Backwards Artifacts

<prompt>
Provide summary of Working Backwards artifacts from:
- Working Backwards Press Release
- Working Backwards FAQ
- Future state vision and customer value proposition

Include links to full Working Backwards documents.
</prompt>

### 5.5 Success Metrics Framework

<prompt>
Provide summary of Success Metrics from:
- Success Metrics Canvas document
- Controllable input metrics and business outcome metrics
- Measurement plan and ownership
- Baseline and target definitions

Include link to full Success Metrics document.
</prompt>

### 5.6 Additional Artifacts

<prompt>
List additional artifacts created from:
- How Might We statements
- Problem/Solution Canvas
- Stakeholder Analysis
- Customer Journey Maps (if created)

Include links to all supporting documents.
</prompt>

---

## 6. Stakeholder Alignment and Confidence Voting

### 6.1 Fist of Five Confidence Voting Results

<prompt>
Extract confidence voting results from:
- Alignment/Confidence Voting Canvas
- Fist of Five voting by stakeholder
- Confidence levels and concerns raised

Present voting results in table format:
| Stakeholder | Role | Confidence Score (0-5) | Concerns/Comments |
|-------------|------|------------------------|-------------------|
| [Name] | [Role] | [Score] | [Concerns if any] |

Include average confidence score and distribution.
</prompt>

### 6.2 Concerns and Mitigation Actions

<prompt>
Extract concerns and mitigations from:
- Confidence voting feedback
- Risk assessment and RAID log
- Stakeholder feedback sessions

For each concern raised:
- **Concern**: Description of stakeholder concern
- **Impact**: Potential impact on engagement success
- **Mitigation Action**: Specific action to address concern
- **Owner**: Person responsible for mitigation
- **Timeline**: When mitigation will be completed
</prompt>

### 6.3 Commitment and Sign-off

<prompt>
Document stakeholder commitment from:
- Formal sign-off and approval records
- Governance structure establishment
- Communication protocols and escalation paths

Include commitment statements and governance framework established.
</prompt>

---

## 7. Next Steps and Action Items

### 7.1 Immediate Actions (Next 2 Weeks)

<prompt>
Extract immediate actions from:
- Workshop action items and commitments
- Next steps planning and timeline
- Stakeholder responsibilities and deadlines

List 5-10 immediate actions with:
- **Action**: Specific action to be taken
- **Owner**: Person responsible
- **Due Date**: Completion deadline
- **Dependencies**: Any prerequisites or dependencies
- **Success Criteria**: How completion will be validated
</prompt>

### 7.2 Short-Term Actions (Next 30 Days)

<prompt>
Extract short-term actions from:
- Implementation roadmap first sprint planning
- Artifact refinement and validation activities
- Team formation and onboarding activities

List key actions for the first month of engagement.
</prompt>

### 7.3 Transition to Build Phase

<prompt>
Define transition approach from:
- Implementation roadmap and sprint planning
- Team onboarding and knowledge transfer
- Development environment setup and tooling
- First sprint objectives and deliverables

Describe the transition from LRP workshop to active build phase.
</prompt>

---

## 8. Appendices

### Appendix A: Workshop Participants

<prompt>
Create comprehensive participant list from:
- Workshop attendance records
- Stakeholder information and contact details

Include:
- Name, Role, Organization, Email, Participation Level
</prompt>

### Appendix B: Workshop Materials and Resources

<prompt>
List workshop materials from:
- Presentation decks and training materials
- Canvas templates and collaboration tools
- Reference documentation and BLA guidance

Include links to all workshop materials and resources.
</prompt>

### Appendix C: Detailed Workshop Notes

<prompt>
Include detailed workshop notes from:
- Session-by-session discussion summaries
- Key decisions and rationale
- Parking lot items and future considerations

Provide comprehensive record of workshop discussions and outcomes.
</prompt>

### Appendix D: LRP Website Output

<prompt>
Describe LRP website deliverable from:
- LRP website structure and content
- Professional HTML website with multiple tabs
- Executive presentation materials

The LRP website includes:
- How Might We statements
- Working Backwards (future state vision)
- Press Release (future state press release)
- Customer FAQs
- ROI & Investment Analysis
- Implementation Roadmap
- High-Level Architecture

Include link to LRP website and access instructions.
</prompt>

---

**Document Review and Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| AWS TPM (Facilitator) | <prompt>Extract TPM name</prompt> | | |
| AWS SDE3 (Co-Facilitator) | <prompt>Extract SDE3 name</prompt> | | |
| Customer Executive Sponsor | <prompt>Extract Executive Sponsor</prompt> | | |
| Customer Product Owner | <prompt>Extract Product Owner</prompt> | | |

**Change History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial LRP Workshop Summary per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This LRP Workshop Summary follows Build Like Amazon (BLA) prescriptive guidance for Launch Ready Planning.*

*For support: BLA Practice Team: bla-practice@amazon.com*
