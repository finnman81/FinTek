# Customer Business Outcomes (CBO) Canvas

<execution-notes>
This template generates a BLA-compliant Customer Business Outcomes Canvas following the official BLA CBO methodology.
The CBO Canvas is the north star document for BLA engagements, capturing customer challenges, solutions, and measurable results.
Process all prompt blocks systematically using specification package data as the exclusive source.
Target CBO Elevator Level 4-5 (business capability quantified or business outcome quantified).
Follow BLA best practices: customer obsession, working backwards methodology, measurable outcomes focus.

CRITICAL: CBO Canvas requires quantified metrics (baselines, targets, timeframes). When quantitative data is not available in specification package:
- Use "[Baseline metric TBD - requires measurement]" for missing current state data
- Use "[Target metric TBD - requires stakeholder input]" for missing future state goals
- Use qualitative descriptions where available, but flag that quantification is needed
- Document missing data in audit trail as gaps requiring stakeholder validation
- NEVER invent or estimate numerical values not present in source materials
</execution-notes>

**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Date**: <prompt>Use current date</prompt>  
**Workstream**: <prompt>Extract workstream or project name from specification package</prompt>  
**Customer Lead**: <prompt>Extract customer lead name from stakeholder information</prompt>  
**AWS Lead**: <prompt>Extract AWS lead or TPM name from team information</prompt>  
**CBO Elevator Level**: <prompt>Assess and assign Level 4-5 based on quantification of business capabilities/outcomes</prompt>  
**Industry**: <prompt>Extract industry sector from customer context</prompt>  
**Canvas Version**: 1.0

---

## 1. Customer Profile

### 1.1 Who is the external customer?

**Primary Customer Segments**:
<prompt>
Extract primary customer segments from:
- User personas and customer context documentation
- Target audience definitions
- Market analysis and customer demographics

Provide 2-4 specific customer segments with characteristics, demographics, and behaviors.
</prompt>
**Who is the customer's customer?**
<prompt>
Describe the end customers/users from:
- User stories and persona definitions
- Customer journey mapping
- Target audience analysis

Be specific about personas, needs, behaviors, and pain points of the end users.
</prompt>

**What is the business model? How does this team/product make money or add customer value?**
<prompt>
Extract business model information from:
- Business requirements and opportunity summary
- Value proposition and business case
- Revenue model and monetization strategy

Include:
- Revenue Streams: Primary revenue sources and business model
- Value Proposition: Core value delivered to customers
- Market Position: Competitive positioning and differentiation
- Growth Strategy: How the business plans to scale
</prompt>

### 1.2 Who is the internal customer?

**Internal Stakeholders and Teams**:
<prompt>
Identify internal customers from:
- Stakeholder analysis and governance framework
- Team structure and organizational context
- Internal user groups and departments

Describe internal teams, departments, or roles that will use or benefit from this solution.
</prompt>

---

## 2. Business Challenges and Pain Points

### 2.1 What are the customer's pain points?

**Challenge Quantification** (Target: Level 4-5 CBO):
<prompt>
Extract and quantify business challenges from:
- Current state analysis and pain points
- Customer journey mapping current state issues
- Business requirements and problem statements
- Working Backwards problem definition

For each challenge, provide:
- **Challenge Description**: Specific business problem or pain point
- **Current State Baseline**: Quantified current performance (e.g., "Manual process takes 4 hours per transaction")
- **Business Impact**: Quantified cost or impact (e.g., "$2M annual operational cost", "30% customer churn")
- **Frequency/Scale**: How often or widespread the problem occurs

Prioritize challenges by business impact and quantify wherever possible to achieve Level 4-5 CBO.
</prompt>

### 2.2 Root Cause Analysis

<prompt>
Identify root causes of challenges from:
- Problem/Solution Canvas analysis
- Current state technical and process limitations
- Stakeholder feedback and pain point analysis

Describe underlying causes rather than symptoms, focusing on systemic issues.
</prompt>

---

## 3. Proposed Solutions and Approach

### 3.1 What is the proposed solution?

**Solution Overview**:
<prompt>
Extract solution approach from:
- Working Backwards press release and vision
- Architecture overview and technical approach
- Product requirements and feature descriptions
- Future state vision and capabilities

Describe the solution in business terms, focusing on capabilities and outcomes rather than technical implementation details.
</prompt>

### 3.2 How does the solution address the challenges?

**Challenge-Solution Mapping**:
<prompt>
Create a mapping between challenges and solutions from:
- Requirements traceability matrix
- Problem/Solution Canvas
- Architecture decision rationale
- Feature descriptions and acceptance criteria

For each major challenge identified in section 2.1, explain how the proposed solution addresses it.
Use format:
- **Challenge**: [Challenge description]
- **Solution Approach**: [How solution addresses this challenge]
- **Expected Improvement**: [Quantified improvement target]
</prompt>

---

## 4. Expected Results and Benefits

### 4.1 What are the expected business outcomes?

**Quantified Business Outcomes** (Target: Level 4-5 CBO):
<prompt>
Extract and quantify expected outcomes from:
- Success metrics and KPI definitions
- Business case and ROI analysis
- Working Backwards press release benefits
- Customer Business Outcomes Canvas results framework

Organize outcomes by CBO Value Hierarchy categories:
- **Agility**: Speed, flexibility, time-to-market improvements (quantified)
- **Cost**: Cost reduction, efficiency gains, resource optimization (quantified)
- **Resilience**: Reliability, availability, risk reduction (quantified)
- **Productivity**: Output improvements, automation benefits (quantified)

For each outcome, provide:
- **Outcome Description**: Specific business result
- **Baseline**: Current state measurement
- **Target**: Future state goal with timeframe
- **Measurement Method**: How success will be measured

Example format:
- **Agility - Time to Market**: Reduce feature deployment time from 4 weeks to 2 days (95% reduction) within 6 months
- **Cost - Operational Efficiency**: Reduce manual processing costs from $2M to $500K annually (75% reduction)
</prompt>

### 4.2 Customer Success Quote (Future State)

<prompt>
Create a compelling future state customer quote (20-30 words) from:
- Working Backwards press release customer testimonial
- Stakeholder vision and success criteria
- Expected business outcomes and benefits

Format as a quote from a customer executive describing the transformation impact.
Example: "This solution transformed our customer experience, reducing order processing time by 80% and increasing customer satisfaction scores from 3.2 to 4.7 out of 5."
</prompt>

---

## 5. Success Metrics and Measurement

### 5.1 Controllable Input Metrics (Leading Indicators)

<prompt>
Define controllable input metrics from:
- KPI scorecard and measurement framework
- Success metrics canvas
- Performance requirements and SLAs

Focus on metrics the team can directly control and measure frequently for immediate decisions.
Include:
- **Metric Name**: Specific measurable indicator
- **Current Baseline**: Current state measurement
- **Target**: Goal with timeframe
- **Measurement Frequency**: How often measured (daily, weekly, sprint)
- **Owner**: Team or role responsible

Examples:
- API response time: Current 2000ms → Target <200ms (90th percentile) - Measured continuously
- Deployment frequency: Current 1/month → Target 10/day - Measured daily
- Code coverage: Current 45% → Target 80% - Measured per sprint
</prompt>

### 5.2 Business Outcome Metrics (Lagging Indicators)

<prompt>
Define business outcome metrics from:
- Customer Business Outcomes Canvas results framework
- KPI scorecard business metrics
- Success criteria and business case ROI

Align with CBO Value Hierarchy (Agility, Cost, Resilience, Productivity).
Include:
- **Metric Name**: Business outcome indicator
- **Current Baseline**: Current state measurement
- **Target**: Goal with timeframe
- **Measurement Frequency**: How often measured (monthly, quarterly)
- **Owner**: Business stakeholder responsible

Examples:
- Customer acquisition cost: Current $150 → Target $75 - Measured monthly
- Revenue per user: Current $25 → Target $45 - Measured quarterly
- Customer satisfaction (NPS): Current 32 → Target 65 - Measured quarterly
</prompt>

### 5.3 Measurement Plan and "Measure Forwards" Approach

<prompt>
Define measurement approach from:
- KPI scorecard measurement methodology
- Success metrics canvas reporting schedule
- Governance framework monitoring and reporting

Include:
- **Baseline Establishment**: How current state will be measured
- **Regular Review Cycles**: Frequency of metric review (sprint, monthly, quarterly)
- **Reporting Mechanism**: How metrics will be communicated to stakeholders
- **Ownership and Accountability**: Who owns each metric and review process
- **Course Correction Process**: How team will respond to metric trends
</prompt>

---

## 6. Implementation Context

### 6.1 BLA Engagement Specifics

**Engaging Title**:
<prompt>
Create a compelling one-line summary of the transformation from:
- Working Backwards press release headline
- Project vision and value proposition
- Customer success quote

Example: "Transforming Customer Experience Through AI-Powered Personalization at Scale"
</prompt>

**6-Month Delivery Target**:
<prompt>
Extract delivery commitment from:
- Implementation roadmap and timeline
- Sprint planning and milestone delivery
- Project delivery plan

Specify the market delivery commitment and key milestones within 6-month BLA timeframe.
</prompt>

**Amazon Team Embedding Plan**:
<prompt>
Extract team integration approach from:
- Team composition and resource allocation
- Collaboration model and working arrangements
- Knowledge transfer and capability building plans

Describe how battle-hardened Amazon teams will integrate with customer organization.
</prompt>

**Voice of Customer Representation**:
<prompt>
Define customer advocacy approach from:
- Stakeholder engagement and communication plans
- Feedback collection and validation processes
- Customer journey mapping and user research

Describe customer advocacy mechanisms and feedback loops.
</prompt>

**Early Drift Detection**:
<prompt>
Extract requirement validation approach from:
- Quality assurance and validation procedures
- Sprint review and acceptance criteria validation
- Governance framework monitoring and escalation

Describe requirement validation and course correction approach.
</prompt>

**Proactive Communication**:
<prompt>
Define communication strategy from:
- Governance framework communication protocols
- Stakeholder engagement and reporting cadence
- Escalation procedures and touchpoint schedule

Describe regular touchpoints and escalation paths.
</prompt>

### 6.2 Strategic Alignment

<prompt>
Describe strategic alignment from:
- Business objectives and strategic priorities
- Market positioning and competitive advantages
- Long-term vision and transformation goals

Explain how this BLA engagement aligns with broader business strategy and transformation objectives.
</prompt>

---

## 7. CBO Canvas Quality Assessment

### 7.1 CBO Elevator Level Achieved

<prompt>
Assess the CBO Elevator Level achieved based on quantification:
- **Level 1**: Technology benefit identified (e.g., "faster processing")
- **Level 2**: Technology benefit quantified (e.g., "50% faster processing")
- **Level 3**: Business capability identified (e.g., "improved customer service")
- **Level 4**: Business capability quantified (e.g., "reduce customer service costs by $500K annually") ⭐ **Target Level**
- **Level 5**: Business outcome quantified (e.g., "increase revenue by $2M through 20% improvement in customer retention") ⭐ **Stretch Goal**

Provide assessment with supporting evidence from the canvas content.
Target: Level 4-5 for BLA engagements.
</prompt>

### 7.2 Canvas Completeness Checklist

<prompt>
Validate canvas completeness:
- [ ] Customer profile clearly defined with business model
- [ ] Pain points quantified with baseline data
- [ ] Solution focuses on outcomes, not activities
- [ ] Benefits are directional and measurable
- [ ] Metrics include controllable input indicators
- [ ] Industry-specific context included
- [ ] Future state quote is compelling (20-30 words)
- [ ] BLA transformation components addressed
- [ ] CBO Elevator Level 4-5 achieved with quantified outcomes

Identify any gaps or areas requiring additional quantification.
</prompt>

---

## 8. Next Steps and Governance

### 8.1 Stakeholder Validation

<prompt>
Define validation approach from:
- Governance framework approval processes
- Stakeholder engagement and sign-off requirements
- LRP workshop alignment and confidence voting

Schedule review with key stakeholders and obtain formal validation.
</prompt>

### 8.2 Regular Review Cadence

<prompt>
Establish review schedule from:
- Governance framework monitoring and reporting
- Sprint review and retrospective cadence
- Quarterly business review planning

Schedule quarterly CBO canvas updates and metric reviews.
</prompt>

### 8.3 Integration with Implementation Roadmap

<prompt>
Connect CBO to implementation from:
- Implementation roadmap canvas
- Sprint planning and epic breakdown
- Requirements traceability matrix

Use CBO Canvas as foundation for roadmap development and ensure all implementation activities trace back to business outcomes.
</prompt>

---

**Canvas Status**: <prompt>Assign status: Draft/Under Review/Approved/Active</prompt>  
**Last Updated**: <prompt>Use current date</prompt>  
**Next Review**: <prompt>Calculate quarterly review date</prompt>  
**BLA Engagement Phase**: <prompt>Identify phase: Envisioning & Discovery/Build/Launch</prompt>

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This CBO Canvas follows D1D Customer Business Outcomes methodology and Build Like Amazon (BLA) prescriptive guidance.*

*BLA Focus: Accelerate customer business outcomes through Amazon's product & software engineering approach*

*For support: #customer-business-outcomes-cbo Slack channel | BLA Practice Team: bla-practice@amazon.com*
