# How Might We (HMW) Statements

<execution-notes>
This template generates BLA-compliant How Might We statements following Amazon's innovation methodology.
HMW statements frame transformation opportunities as actionable questions that inspire solution ideation.
Process all prompt blocks systematically using specification package data as the exclusive source.
Follow BLA best practices: opportunity framing, innovation focus, connection to customer challenges.
HMW statements should be specific, actionable, and inspire creative solutions.
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Date**: <prompt>Use current date</prompt>  
**Workshop**: <prompt>Extract workshop context (e.g., "LRP Workshop")</prompt>  
**Version**: 1.0  
**Status**: Draft

---

## Purpose

How Might We (HMW) statements are a powerful tool for framing challenges as opportunities and inspiring innovative solutions. Each HMW statement transforms a problem or constraint into an open-ended question that invites creative problem-solving while maintaining focus on customer value and business outcomes.

---

## HMW Statement Framework

**Format**: "How might we [action verb] [specific challenge/opportunity] [for whom] [to achieve what outcome]?"

**Characteristics of Good HMW Statements**:
- Specific enough to provide direction, broad enough to allow creativity
- Focused on opportunities rather than constraints
- Action-oriented and inspiring
- Connected to customer challenges and business outcomes
- Measurable success criteria implied

---

## Prioritized HMW Statements

<prompt>
Generate 8-12 prioritized How Might We statements from:
- Customer Business Outcomes Canvas challenges
- Problem/Solution Canvas problem statements
- Current state pain points and limitations
- Customer journey mapping opportunities
- Innovation opportunities and transformation goals

For each HMW statement, provide:
1. **HMW Statement**: The question itself
2. **Challenge Connection**: Which customer challenge this addresses
3. **Impact Assessment**: Potential business impact (High/Medium/Low)
4. **Feasibility Assessment**: Implementation feasibility (High/Medium/Low)
5. **Priority**: Overall priority (P0/P1/P2) based on impact and feasibility
6. **Success Criteria**: How we'll know if we've successfully addressed this HMW

Organize by priority (P0 first, then P1, then P2).

Example format:

### P0 - Critical Opportunities

#### HMW-001: [HMW Statement]
**Statement**: How might we [action] [challenge] [for whom] [to achieve outcome]?

**Challenge Connection**: <prompt>Link to specific challenge from CBO Canvas or problem statement</prompt>

**Impact Assessment**: High  
**Rationale**: <prompt>Explain why this has high business impact with quantified potential</prompt>

**Feasibility Assessment**: High  
**Rationale**: <prompt>Explain why this is feasible with available technology and resources</prompt>

**Priority**: P0 (High Impact + High Feasibility)

**Success Criteria**: <prompt>Define measurable success criteria for this HMW</prompt>

**Solution Ideas**: <prompt>List 2-3 potential solution approaches that could address this HMW</prompt>

---

Continue this format for all HMW statements, organizing by priority.
</prompt>

---

## HMW Impact-Feasibility Matrix

<prompt>
Create a visual representation of HMW statements plotted by impact and feasibility:

| Impact / Feasibility | High Feasibility | Medium Feasibility | Low Feasibility |
|---------------------|------------------|-------------------|-----------------|
| **High Impact** | [List HMW IDs] | [List HMW IDs] | [List HMW IDs] |
| **Medium Impact** | [List HMW IDs] | [List HMW IDs] | [List HMW IDs] |
| **Low Impact** | [List HMW IDs] | [List HMW IDs] | [List HMW IDs] |

**Priority Focus**: P0 statements are in the High Impact + High Feasibility quadrant.
**Quick Wins**: High Feasibility + Medium Impact statements can be addressed early.
**Strategic Bets**: High Impact + Low Feasibility statements may require longer-term investment.
</prompt>

---

## Connection to Customer Business Outcomes

<prompt>
Map HMW statements to CBO Canvas outcomes from:
- Customer Business Outcomes Canvas
- Success metrics and KPIs
- Business value categories (Agility, Cost, Resilience, Productivity)

Create mapping table:

| HMW ID | HMW Statement Summary | CBO Outcome | Value Category | Expected Impact |
|--------|----------------------|-------------|----------------|-----------------|
| HMW-001 | [Summary] | [CBO outcome] | [Agility/Cost/Resilience/Productivity] | [Quantified impact] |

This mapping ensures all HMW statements trace back to measurable business outcomes.
</prompt>

---

## Innovation Opportunities

<prompt>
Identify innovation opportunities from HMW statements:
- Technology innovation opportunities (AI/ML, automation, cloud-native)
- Process innovation opportunities (workflow optimization, automation)
- Experience innovation opportunities (user experience, customer journey)
- Business model innovation opportunities (new capabilities, revenue streams)

For each innovation opportunity:
**Opportunity**: [Description]  
**Related HMW Statements**: [List of HMW IDs]  
**Innovation Type**: [Technology/Process/Experience/Business Model]  
**Potential Value**: [Quantified or directional value]  
**Implementation Approach**: [High-level approach]
</prompt>

---

## Solution Ideation Framework

<prompt>
For top 3-5 priority HMW statements, provide solution ideation framework:

### HMW-[ID]: [Statement]

**Brainstorming Prompts**:
- What if we could [extreme scenario]?
- How do leading companies in [industry] solve similar challenges?
- What emerging technologies could enable new approaches?
- What constraints can we remove or challenge?

**Solution Concepts** (3-5 ideas per HMW):
1. **Concept Name**: [Brief description]
   - **Approach**: [How it works]
   - **Benefits**: [Key benefits]
   - **Challenges**: [Implementation challenges]
   - **Feasibility**: [Quick assessment]

2. [Continue for additional concepts]

**Recommended Approach**: <prompt>Based on solution concepts, recommend the most promising approach with rationale</prompt>
</prompt>

---

## Next Steps

<prompt>
Define next steps for HMW statements from:
- Implementation roadmap and sprint planning
- Solution validation and prototyping plans
- Stakeholder feedback and prioritization

Include:
1. **Validation Activities**: How to validate HMW priorities and solution concepts
2. **Prototyping Plans**: Which HMWs warrant rapid prototyping or proof-of-concept
3. **Roadmap Integration**: How HMW statements inform implementation roadmap
4. **Continuous Refinement**: Process for updating HMW statements as learning occurs
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
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial How Might We statements per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This How Might We document follows Build Like Amazon (BLA) prescriptive guidance for innovation opportunity framing.*

*For support: BLA Practice Team: bla-practice@amazon.com*
