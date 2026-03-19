# Working Backwards Press Release

<execution-notes>
This template generates a BLA-compliant Working Backwards Press Release following Amazon's innovation methodology.
The Press Release is written from the future state perspective, describing the product/service as if it has already launched successfully.
Process all prompt blocks systematically using specification package data as the exclusive source.
Follow BLA best practices: customer obsession, working backwards from customer needs, compelling future state vision.
The press release should be concise (typically 1-1.5 pages) and focus on customer benefits rather than technical details.
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Date**: <prompt>Use future date (typically 6 months from current date for BLA engagements)</prompt>  
**Version**: 1.0  
**Status**: Draft

---

## [Customer Name] Announces [Product/Service Name]

### [Compelling Subtitle Describing Customer Benefit]

<prompt>
Create compelling headline and subtitle from:
- Working Backwards vision and value proposition
- Customer Business Outcomes Canvas
- Product requirements and key features
- Customer success criteria

Headline format: "[Customer Name] Announces [Product/Service Name]"
Subtitle format: One sentence describing the primary customer benefit or transformation

Example: "Global Retailer Launches AI-Powered Personalization Engine, Transforming Customer Experience and Increasing Conversion Rates by 40%"
</prompt>

---

**[CITY, STATE/COUNTRY] – [FUTURE DATE]** – <prompt>
Generate opening paragraph (3-4 sentences) from:
- Customer Business Outcomes Canvas
- Product vision and value proposition
- Key customer benefits and business outcomes
- Target customer segments

The opening paragraph should:
- Announce the product/service launch
- Identify the target customer
- State the primary problem being solved
- Highlight the key benefit or transformation

Example format:
"[Customer Name], a leading [industry description], today announced the launch of [Product/Service Name], a [brief description] that [primary benefit]. This innovative solution addresses [key problem] faced by [target customers], enabling them to [key capability or outcome]. With [Product/Service Name], [target customers] can now [specific benefit], resulting in [quantified business outcome]."
</prompt>

<prompt>
Generate problem statement paragraph (2-3 sentences) from:
- Current state challenges and pain points
- Customer journey mapping current state issues
- Business requirements problem definition
- Customer Business Outcomes Canvas challenges

Describe the problem from the customer's perspective, focusing on business impact and customer pain.

Example format:
"Previously, [target customers] struggled with [specific problem], which resulted in [negative business impact]. The existing [current solution/process] was [limitation 1] and [limitation 2], leading to [quantified pain point]. This challenge prevented [target customers] from [desired outcome] and cost them [quantified cost or impact]."
</prompt>

<prompt>
Generate solution description paragraph (3-4 sentences) from:
- Product requirements and key features
- Architecture overview and capabilities
- Customer Business Outcomes Canvas solution approach
- Future state vision and capabilities

Describe the solution in customer-friendly terms, focusing on capabilities and benefits rather than technical implementation.

Example format:
"[Product/Service Name] solves this problem by [primary solution approach]. The solution provides [key capability 1], [key capability 2], and [key capability 3], enabling [target customers] to [desired outcome]. Built on [high-level technology approach], [Product/Service Name] delivers [key differentiator] while ensuring [important quality attribute like security, scalability, or reliability]."
</prompt>

**"[Customer Executive Quote]"**

<prompt>
Generate customer executive quote (2-3 sentences) from:
- Customer Business Outcomes Canvas customer success quote
- Stakeholder vision and success criteria
- Expected business outcomes and transformation impact

The quote should:
- Come from a senior customer executive (CEO, CTO, VP, etc.)
- Express enthusiasm about the transformation
- Highlight specific business benefits or outcomes
- Be authentic and credible

Format: "[Quote text]," said [Executive Name], [Title] of [Customer Name].

Example:
"This solution has transformed how we serve our customers. We've reduced order processing time by 80% and increased customer satisfaction scores from 3.2 to 4.7 out of 5. Our team can now focus on high-value activities instead of manual processes," said Jane Smith, Chief Operating Officer of Acme Corporation.
</prompt>

<prompt>
Generate technical details paragraph (2-3 sentences) from:
- Architecture overview and key technologies
- Integration approach and ecosystem
- Non-functional requirements (performance, scalability, security)
- AWS services and capabilities utilized

Provide high-level technical context without overwhelming non-technical readers.

Example format:
"[Product/Service Name] leverages [key technology 1] and [key technology 2] to deliver [capability]. The solution integrates seamlessly with [existing systems or platforms], ensuring [integration benefit]. With [performance characteristic], [Product/Service Name] can [scalability or performance benefit]."
</prompt>

**"[End User or Team Member Quote]"**

<prompt>
Generate end user or team member quote (2-3 sentences) from:
- User stories and persona feedback
- Expected user experience improvements
- Operational benefits and productivity gains

The quote should:
- Come from an end user, team member, or operational stakeholder
- Describe the day-to-day impact and user experience
- Be specific about workflow improvements or benefits
- Complement the executive quote with ground-level perspective

Format: "[Quote text]," said [User Name], [Title/Role] at [Customer Name].

Example:
"Before this solution, I spent 4 hours every day on manual data entry and reconciliation. Now, the system handles it automatically, and I can focus on analyzing insights and making strategic recommendations. It's completely changed how I work," said Michael Chen, Senior Analyst at Acme Corporation.
</prompt>

<prompt>
Generate availability and call-to-action paragraph (1-2 sentences) from:
- Implementation roadmap and launch timeline
- Deployment approach and rollout plan
- Access or onboarding information

Describe when and how customers can access the solution.

Example format:
"[Product/Service Name] is now available to [target audience] and can be accessed via [access method]. To learn more about [Product/Service Name] or to get started, visit [URL or contact information]."
</prompt>

---

## About [Customer Name]

<prompt>
Generate company background paragraph (2-3 sentences) from:
- Customer context and business model
- Industry position and market presence
- Strategic focus and mission

Provide brief company overview for context.

Example format:
"[Customer Name] is a [industry position] [company description] serving [customer base] across [geographic presence]. Founded in [year], the company [key business activities] and is committed to [mission or strategic focus]. With [size metric like revenue, employees, or customers], [Customer Name] is [market position or achievement]."
</prompt>

---

## About Amazon Web Services

Amazon Web Services (AWS) is the world's most comprehensive and broadly adopted cloud, offering over 200 fully featured services from data centers globally. Millions of customers—including the fastest-growing startups, largest enterprises, and leading government agencies—are using AWS to lower costs, become more agile, and innovate faster.

---

## Media Contact

**[Customer Name]:**  
[Contact Name]  
[Title]  
[Email]  
[Phone]

**Amazon Web Services:**  
[AWS Contact Name]  
[Title]  
[Email]  
[Phone]

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
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial Working Backwards Press Release per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This Working Backwards Press Release follows Amazon's innovation methodology and Build Like Amazon (BLA) prescriptive guidance.*

*For support: BLA Practice Team: bla-practice@amazon.com*
