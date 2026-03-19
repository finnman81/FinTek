# Working Backwards FAQ (Frequently Asked Questions)

<execution-notes>
This template generates a BLA-compliant Working Backwards FAQ following Amazon's innovation methodology.
The FAQ addresses customer, technical, business, and risk questions about the product/service from the future state perspective.
Process all prompt blocks systematically using specification package data as the exclusive source.
Follow BLA best practices: comprehensive question coverage, honest and direct answers, customer obsession focus.
Organize questions by category: Customer Questions, Technical Questions, Business Questions, Risk/Operational Questions.
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Date**: <prompt>Use current date</prompt>  
**Version**: 1.0  
**Status**: Draft

---

## Table of Contents

1. Customer Questions
2. Technical Questions
3. Business Questions
4. Risk and Operational Questions
5. Implementation and Timeline Questions

---

## 1. Customer Questions

<prompt>
Generate 8-12 customer-focused questions and answers from:
- User stories and customer personas
- Customer journey mapping and user experience
- Customer Business Outcomes Canvas
- Product requirements and features

Focus on questions that end customers or users would ask about the product/service.
Questions should cover: value proposition, user experience, benefits, access, support, and customer impact.

Format each Q&A as:
**Q: [Question from customer perspective]**

A: [Comprehensive answer addressing the question, typically 2-4 sentences]

Example questions:
- What problem does this solve for me?
- How will this improve my daily workflow?
- How easy is it to use?
- What makes this different from existing solutions?
- How quickly can I see results?
- What if I need help or support?
- Will this work with my existing tools/processes?
- How secure is my data?
</prompt>

---

## 2. Technical Questions

<prompt>
Generate 10-15 technical questions and answers from:
- Architecture documentation and technical approach
- Integration requirements and dependencies
- Non-functional requirements (performance, scalability, security)
- Technology stack and AWS services
- Development and deployment approach

Focus on questions that technical stakeholders, architects, and developers would ask.
Questions should cover: architecture, technology choices, integrations, performance, scalability, security, and technical feasibility.

Format each Q&A as:
**Q: [Technical question]**

A: [Detailed technical answer, typically 3-5 sentences with specific details]

Example questions:
- What is the overall technical architecture?
- What AWS services are being used and why?
- How does the solution integrate with existing systems?
- What are the performance characteristics (latency, throughput)?
- How does the solution scale to handle increased load?
- What security controls are implemented?
- How is data encrypted and protected?
- What is the disaster recovery approach?
- How are updates and deployments handled?
- What monitoring and observability capabilities are included?
- What are the API specifications and integration points?
- How is authentication and authorization handled?
- What database technology is used and why?
- How is the solution tested (unit, integration, performance)?
- What development tools and practices are used?
</prompt>

---

## 3. Business Questions

<prompt>
Generate 10-12 business questions and answers from:
- Business requirements and business case
- Customer Business Outcomes Canvas
- Success metrics and KPIs
- Cost analysis and ROI
- Implementation roadmap and timeline
- Resource requirements and team structure

Focus on questions that business stakeholders, executives, and product owners would ask.
Questions should cover: business value, ROI, costs, timeline, resources, success metrics, and strategic alignment.

Format each Q&A as:
**Q: [Business question]**

A: [Business-focused answer with quantified benefits where possible, typically 3-5 sentences]

Example questions:
- What business outcomes will this deliver?
- What is the expected ROI and payback period?
- What are the total costs (development, operational, ongoing)?
- How long will it take to implement?
- What resources are required (team, budget, time)?
- How will success be measured?
- What are the key performance indicators (KPIs)?
- How does this align with our strategic objectives?
- What is the competitive advantage this provides?
- What is the total cost of ownership (TCO)?
- How does this compare to alternative solutions?
- What is the implementation timeline and key milestones?
- What organizational changes are required?
- What training is needed for users and staff?
- How will this impact existing operations during implementation?
</prompt>

---

## 4. Risk and Operational Questions

<prompt>
Generate 8-10 risk and operational questions and answers from:
- RAID log (Risks, Assumptions, Issues, Dependencies)
- Risk assessment and mitigation strategies
- Operational readiness and support requirements
- Change management and adoption planning
- Compliance and regulatory considerations

Focus on questions about risks, challenges, operations, and mitigation strategies.
Questions should cover: risks, mitigation, operational support, compliance, change management, and contingency planning.

Format each Q&A as:
**Q: [Risk or operational question]**

A: [Honest answer addressing the risk/concern with mitigation strategy, typically 3-4 sentences]

Example questions:
- What are the main risks and how are they being mitigated?
- What happens if [key dependency] is not available?
- How will we handle operational support and maintenance?
- What compliance or regulatory requirements must be met?
- How will we manage the transition from current to new solution?
- What is the rollback plan if issues occur?
- What are the key dependencies and how are they managed?
- How will we ensure user adoption and change management?
- What assumptions are we making and how will they be validated?
- What happens if the timeline slips or scope changes?
</prompt>

---

## 5. Implementation and Timeline Questions

<prompt>
Generate 6-8 implementation and timeline questions and answers from:
- Implementation roadmap and delivery plan
- Sprint planning and milestone delivery
- Resource allocation and team structure
- Deployment approach and rollout strategy
- Knowledge transfer and capability building

Focus on questions about how the solution will be implemented and delivered.
Questions should cover: implementation approach, timeline, phases, team, deployment, and knowledge transfer.

Format each Q&A as:
**Q: [Implementation question]**

A: [Detailed answer about implementation approach, typically 3-4 sentences]

Example questions:
- What is the overall implementation approach?
- What are the key milestones and delivery phases?
- How is the work organized (sprints, workstreams, epics)?
- Who is on the implementation team and what are their roles?
- How will the solution be deployed to production?
- What is the rollout strategy (phased, big bang, pilot)?
- How will knowledge transfer occur?
- What training will be provided to users and support teams?
</prompt>

---

## Appendix: Open Questions and Decisions Needed

<prompt>
Identify open questions and decisions from:
- Requirements documents and assumptions
- RAID log open items
- Stakeholder feedback and concerns
- Architecture decision records pending decisions

List any questions that remain unanswered or decisions that need to be made:

Format:
**Open Question**: [Question description]  
**Owner**: [Person responsible for resolution]  
**Target Date**: [When answer/decision is needed]  
**Impact**: [Impact if not resolved]

Include 5-10 open items that require stakeholder input or decisions.
</prompt>

---

**Document Review and Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Customer Executive Sponsor | <prompt>Extract Executive Sponsor</prompt> | | |
| Customer Product Owner | <prompt>Extract Product Owner</prompt> | | |
| AWS TPM | <prompt>Extract TPM name</prompt> | | |
| AWS SDE3 | <prompt>Extract SDE3 name</prompt> | | |

**Change History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial Working Backwards FAQ per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This Working Backwards FAQ follows Amazon's innovation methodology and Build Like Amazon (BLA) prescriptive guidance.*

*For support: BLA Practice Team: bla-practice@amazon.com*
