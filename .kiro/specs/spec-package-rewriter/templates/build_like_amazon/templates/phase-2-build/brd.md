# Business Requirements Document (BRD)

<execution-notes>
This template generates a BLA-compliant Business Requirements Document following official BLA BRD structure.
The BRD captures business requirements, objectives, and success criteria from a business perspective.
Process all prompt blocks systematically using specification package data as the exclusive source.
Maintain complete traceability to business outcomes and customer value.
Follow BLA best practices: customer obsession, working backwards, measurable outcomes.

**Integration with BLA Templates**:
- Reference CBO Canvas as primary source for business outcomes and challenges
- Extract business vision from Working Backwards Press Release
- Link to Working Backwards FAQ for business context and questions
- Connect to Success Metrics Canvas for business outcome measurement
- Reference Stakeholder Analysis for stakeholder engagement and communication
- Link to RAID Log for business risks and dependencies
- Ensure requirements support CBO Elevator Level 4-5 outcomes
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Version**: 1.0  
**Date**: <prompt>Use current date</prompt>  
**Status**: Draft  
**Author**: <prompt>Extract TPM or Business Analyst from team information or use "BLA Design Agent Workflow"</prompt>  
**Reviewers**: <prompt>Extract reviewers from specification package (SDM, Customer Business Owner, Customer PO)</prompt>

## Table of Contents

1. Executive Summary
2. Business Context
3. Business Vision and Strategy
4. Business Objectives
5. Stakeholder Analysis
6. Current State Assessment
7. Future State Vision
8. Business Requirements
   - 8.1 Business Capabilities
   - 8.2 Business Processes
   - 8.3 Business Rules
9. Success Metrics and KPIs
10. Business Case
11. Risks and Constraints
12. Implementation Approach
13. Appendices

---

## 1. Executive Summary

<prompt>
Provide executive summary including:
- Business problem or opportunity
- Proposed solution and approach
- Expected business outcomes and benefits
- Investment required and ROI
- Key success factors and risks

**CBO Canvas Integration**:
- Extract customer challenges from CBO Canvas
- Reference CBO Elevator Level 4-5 quantified outcomes
- Link to CBO Value Hierarchy (Agility, Cost, Resilience, Productivity)
- Connect to business capability outcomes

Keep summary concise (1 page maximum) and focused on business value.
Target executive audience with clear business case.
</prompt>

## 2. Business Context

<prompt>
Provide business context including:
- Industry and market context
- Competitive landscape and positioning
- Customer's business model and operations
- Strategic initiatives and priorities
- Regulatory and compliance environment
- Technology landscape and constraints

**CBO Canvas Integration**:
- Reference CBO Canvas for business context
- Link to customer's strategic objectives
- Connect to industry trends and challenges

Provide sufficient context for understanding business requirements.
</prompt>

## 3. Business Vision and Strategy

<prompt>
Define business vision and strategy including:
- Long-term business vision and goals
- Strategic objectives and priorities
- Value proposition and differentiation
- Target outcomes and success criteria
- Alignment with organizational strategy

**Working Backwards and CBO Canvas Integration**:
- Extract vision from Working Backwards Press Release
- Reference CBO Canvas for business capability outcomes
- Link to Success Metrics Canvas for measurable outcomes
- Connect to CBO Elevator Level 4-5 quantified results

Focus on customer value and measurable business impact.
</prompt>

## 4. Business Objectives

<prompt>
Define business objectives including:
- Primary business objectives and goals
- Measurable success criteria and targets
- Timeline and milestones
- Priority and dependencies
- Alignment with strategic initiatives

**CBO Canvas and Success Metrics Integration**:
- Reference CBO Canvas for business capability outcomes
- Link to Success Metrics Canvas for outcome metrics
- Connect objectives to CBO Value Hierarchy dimensions
- Ensure objectives are SMART (Specific, Measurable, Attainable, Relevant, Timely)

Include 3-7 key business objectives with quantified targets.
</prompt>

## 5. Stakeholder Analysis

<prompt>
Provide stakeholder analysis including:
- Key stakeholders and their roles
- Stakeholder interests and concerns
- Influence and impact assessment
- Engagement strategy and communication plan
- Decision-making authority and approval process

**Stakeholder Analysis Template Integration**:
- Reference Stakeholder Analysis template for comprehensive analysis
- Link to stakeholder engagement strategy
- Include power-interest grid and influence-impact matrix
- Connect to communication and change management plans

Identify all stakeholders who will be impacted or have influence.
</prompt>

## 6. Current State Assessment

<prompt>
Assess current state including:
- Current business processes and workflows
- Existing systems and technologies
- Current capabilities and limitations
- Pain points and inefficiencies
- Cost and resource utilization
- Performance metrics and baselines

**CBO Canvas and Problem/Solution Canvas Integration**:
- Reference CBO Canvas for current state challenges
- Link to Problem/Solution Canvas for detailed problem analysis
- Quantify current state metrics and costs
- Document business impact of current limitations

Provide objective, data-driven assessment of current state.
</prompt>

## 7. Future State Vision

<prompt>
Define future state vision including:
- Desired business capabilities and outcomes
- Improved processes and workflows
- Enhanced customer and user experience
- Expected benefits and value realization
- Success criteria and validation approach

**Working Backwards and CBO Canvas Integration**:
- Extract future state from Working Backwards Press Release
- Reference CBO Canvas for business capability outcomes
- Link to Problem/Solution Canvas for solution approach
- Connect to Success Metrics Canvas for outcome measurement

Focus on business value and customer impact, not technical implementation.
</prompt>

## 8. Business Requirements

### 8.1 Business Capabilities

<prompt>
Define business capabilities including:
- Core business capabilities required
- Capability maturity and gaps
- Capability priorities and dependencies
- Capability owners and stakeholders
- Success criteria for each capability

**CBO Canvas Integration**:
- Reference CBO Canvas for business capability outcomes
- Link capabilities to CBO Elevator Level 4-5 outcomes
- Connect to CBO Value Hierarchy dimensions

Organize capabilities by business domain or value stream.
</prompt>

### 8.2 Business Processes

<prompt>
Define business processes including:
- Key business processes and workflows
- Process inputs, outputs, and triggers
- Process owners and participants
- Process performance requirements
- Process improvements and optimization

Include process flows and swimlane diagrams where helpful.
Focus on business logic and rules, not technical implementation.
</prompt>

### 8.3 Business Rules

<prompt>
Define business rules including:
- Business logic and decision criteria
- Validation rules and constraints
- Calculation rules and formulas
- Approval workflows and authorities
- Compliance and regulatory rules

**Format**: Use rule IDs (BR-001, BR-002, etc.) for traceability.

Document rules clearly and unambiguously.
Include examples and edge cases where helpful.
</prompt>

## 9. Success Metrics and KPIs

<prompt>
Define success metrics and KPIs including:
- Business outcome metrics (lagging indicators)
- Operational metrics (leading indicators)
- Customer satisfaction metrics
- Financial metrics (cost savings, revenue impact)
- Performance metrics (efficiency, quality)
- Measurement approach and frequency

**Success Metrics Canvas Integration**:
- Reference Success Metrics Canvas for comprehensive metrics
- Link to controllable input metrics (leading indicators)
- Connect to business outcome metrics (lagging indicators)
- Use "measure forwards" approach
- Map metrics to CBO Value Hierarchy dimensions

Include baseline, target, and stretch goals for each metric.
</prompt>

## 10. Business Case

<prompt>
Provide business case including:
- Investment required (costs and resources)
- Expected benefits and value realization
- Return on investment (ROI) analysis
- Payback period and break-even analysis
- Cost-benefit analysis and financial projections
- Risk-adjusted value and sensitivity analysis

**CBO Canvas Integration**:
- Reference CBO Canvas for business value quantification
- Link to CBO Elevator Level 4-5 quantified outcomes
- Connect to Success Metrics Canvas for benefit measurement

Include both tangible and intangible benefits.
Provide realistic, data-driven financial projections.
</prompt>

## 11. Risks and Constraints

<prompt>
Identify risks and constraints including:
- Business risks and mitigation strategies
- Resource constraints (budget, timeline, people)
- Organizational constraints (policies, processes, culture)
- Market and competitive risks
- Regulatory and compliance constraints
- Change management risks

**RAID Log Integration**:
- Reference RAID Log for comprehensive risk management
- Link to risk mitigation strategies and owners
- Connect to assumptions and dependencies
- Track risk status and impact

Assess probability and impact for each risk.
Define clear mitigation strategies and owners.
</prompt>

## 12. Implementation Approach

<prompt>
Define implementation approach including:
- Implementation strategy and phasing
- Key milestones and deliverables
- Resource requirements and allocation
- Change management approach
- Training and enablement needs
- Go-live criteria and readiness assessment

**Implementation Roadmap and Change Management Integration**:
- Reference Implementation Roadmap for detailed delivery plan
- Link to Change Management Plan for adoption strategy
- Connect to 6-month BLA delivery timeline
- Show phasing and sprint alignment

Focus on business perspective of implementation.
Include change management and user adoption considerations.
</prompt>

## 13. Appendices

### Appendix A - Glossary

<prompt>
Provide glossary including:
- Business terms and definitions
- Acronyms and abbreviations
- Industry-specific terminology
- Customer-specific terminology

Define terms clearly for all stakeholders.
</prompt>

### Appendix B - Stakeholder Interview Summary

<prompt>
Provide stakeholder interview summary including:
- Interview participants and roles
- Key findings and insights
- Requirements and priorities
- Concerns and risks identified
- Recommendations and next steps

Document stakeholder input and validation.
</prompt>

### Appendix C - Process Diagrams

<prompt>
Provide process diagrams including:
- Current state process flows
- Future state process flows
- Swimlane diagrams showing roles and handoffs
- Decision trees and workflow diagrams

Include textual descriptions for diagram creation.
</prompt>

### Appendix D - References and Links

<prompt>
Provide references and links including:
- Related documentation and artifacts
- Industry research and benchmarks
- Regulatory and compliance references
- Customer documentation and standards

**BLA Template Integration**:
- Link to CBO Canvas
- Link to Working Backwards Press Release and FAQ
- Link to Success Metrics Canvas
- Link to Stakeholder Analysis
- Link to Implementation Roadmap
- Link to RAID Log

Organize links by category for easy navigation.
</prompt>

---

**Document Review and Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| TPM/BA (Author) | <prompt>Extract TPM or BA name from team information</prompt> | | |
| SDM (Reviewer) | <prompt>Extract SDM name from team information</prompt> | | |
| Customer Business Owner (Reviewer) | <prompt>Extract Business Owner from stakeholder information</prompt> | | |
| Customer PO (Approver) | <prompt>Extract Customer PO from stakeholder information</prompt> | | |

**Change History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial BRD creation from business discovery per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This document follows Build Like Amazon (BLA) prescriptive guidance for Business Requirements Documents.*

*For support: BLA Practice Team: bla-practice@amazon.com*
