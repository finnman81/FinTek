# Success Metrics Canvas

<execution-notes>
This template generates a BLA-compliant Success Metrics Canvas.
The canvas defines measurable criteria for engagement success with controllable input metrics and business outcome metrics.
Process all prompt blocks systematically using specification package data as the exclusive source.
Follow BLA best practices: CBO Value Hierarchy alignment, "measure forwards" approach, controllable input focus.
</execution-notes>

**Project**: <prompt>Extract project name from specification package</prompt>  
**Customer**: <prompt>Extract customer name from specification package</prompt>  
**Date**: <prompt>Use current date</prompt>  
**Version**: 1.0  
**Status**: Draft

---

## Table of Contents

1. Success Metrics Framework
2. Controllable Input Metrics (Leading Indicators)
3. Business Outcome Metrics (Lagging Indicators)
4. Measurement Methodology
5. Baseline and Target Definition
6. Reporting and Ownership

---

## 1. Success Metrics Framework

### 1.1 Measurement Philosophy

**"Measure Forwards" Approach**:
<prompt>
Describe the measurement approach from:
- Customer Business Outcomes Canvas measurement framework
- KPI scorecard methodology
- Success criteria and validation approach

Explain the "measure forwards" philosophy:
- Focus on controllable input metrics that teams can act on immediately
- Link input metrics to business outcome metrics
- Regular measurement and course correction
- Data-driven decision making
</prompt>

### 1.2 CBO Value Hierarchy Alignment

<prompt>
Align metrics with CBO Value Hierarchy from:
- Customer Business Outcomes Canvas
- Business value categories and outcomes

Map metrics to four value categories:
- **Agility**: Speed, flexibility, time-to-market metrics
- **Cost**: Cost reduction, efficiency, resource optimization metrics
- **Resilience**: Reliability, availability, risk reduction metrics
- **Productivity**: Output, automation, effectiveness metrics

Ensure metrics cover all relevant value categories.
</prompt>

### 1.3 Success Criteria Overview

<prompt>
Define overall success criteria from:
- Stakeholder expectations and commitments
- Customer Business Outcomes Canvas
- Business case and ROI targets

Describe what constitutes overall engagement success:
- Quantitative success thresholds
- Qualitative success indicators
- Stakeholder satisfaction criteria
- Business outcome achievement
</prompt>

---

## 2. Controllable Input Metrics (Leading Indicators)

<prompt>
Define controllable input metrics from:
- Technical performance requirements
- Development and delivery metrics
- Quality and testing metrics
- Operational metrics

For each controllable input metric:

### Metric [#]: [Metric Name]

**Description**: <prompt>Describe what this metric measures and why it matters</prompt>

**Category**: <prompt>Assign category: Performance/Quality/Delivery/Operations/Security</prompt>

**CBO Value Alignment**: <prompt>Which CBO value category this supports (Agility/Cost/Resilience/Productivity)</prompt>

**Current Baseline**: <prompt>Current state measurement with date</prompt>

**Target**: <prompt>Future state goal with timeframe (e.g., "< 200ms by Sprint 6")</prompt>

**Measurement Method**: <prompt>How this metric is measured (tools, process, frequency)</prompt>

**Measurement Frequency**: <prompt>How often measured (continuous, daily, per sprint, weekly)</prompt>

**Owner**: <prompt>Team or role responsible for this metric</prompt>

**Action Threshold**: <prompt>When action is required (e.g., "Alert if > 500ms")</prompt>

**Link to Business Outcome**: <prompt>Which business outcome metric this input metric influences</prompt>

**Data Source**: <prompt>Where measurement data comes from (monitoring tool, dashboard, report)</prompt>

Identify 10-15 controllable input metrics covering:
- **Performance Metrics**: Response time, throughput, latency, resource utilization
- **Quality Metrics**: Code coverage, defect density, test pass rate, technical debt
- **Delivery Metrics**: Deployment frequency, lead time, cycle time, velocity
- **Operations Metrics**: Availability, error rate, incident count, MTTR
- **Security Metrics**: Vulnerability count, security scan results, compliance checks

Example metrics:
- API Response Time (P95): Current 2000ms → Target < 200ms - Measured continuously
- Deployment Frequency: Current 1/month → Target 10/day - Measured daily
- Code Coverage: Current 45% → Target 80% - Measured per sprint
- System Availability: Current 99.5% → Target 99.9% - Measured continuously
- Defect Escape Rate: Current 15% → Target < 5% - Measured per sprint
</prompt>

---

## 3. Business Outcome Metrics (Lagging Indicators)

<prompt>
Define business outcome metrics from:
- Customer Business Outcomes Canvas results framework
- KPI scorecard business metrics
- Success criteria and business case ROI
- Stakeholder success definitions

For each business outcome metric:

### Metric [#]: [Metric Name]

**Description**: <prompt>Describe what this metric measures and its business significance</prompt>

**CBO Value Category**: <prompt>Assign to Agility/Cost/Resilience/Productivity</prompt>

**Current Baseline**: <prompt>Current state measurement with date and source</prompt>

**Target**: <prompt>Future state goal with timeframe (e.g., "Reduce from $2M to $500K annually by Month 6")</prompt>

**Stretch Goal**: <prompt>Aspirational target beyond primary goal (optional)</prompt>

**Measurement Method**: <prompt>How this metric is measured (business reports, analytics, surveys)</prompt>

**Measurement Frequency**: <prompt>How often measured (monthly, quarterly, annually)</prompt>

**Owner**: <prompt>Business stakeholder responsible for this metric</prompt>

**Success Threshold**: <prompt>Minimum acceptable achievement to consider success</prompt>

**Influenced By**: <prompt>Which controllable input metrics influence this outcome</prompt>

**Data Source**: <prompt>Where measurement data comes from (business systems, reports, surveys)</prompt>

**Validation Method**: <prompt>How achievement will be validated with stakeholders</prompt>

Identify 8-12 business outcome metrics covering:
- **Agility Outcomes**: Time-to-market, feature velocity, innovation speed, adaptability
- **Cost Outcomes**: Operational cost reduction, resource efficiency, TCO reduction
- **Resilience Outcomes**: System reliability, business continuity, risk reduction
- **Productivity Outcomes**: Output per resource, automation benefits, efficiency gains
- **Customer Outcomes**: Satisfaction, retention, acquisition, lifetime value
- **Revenue Outcomes**: Revenue growth, conversion rate, average order value

Example metrics:
- Customer Acquisition Cost: Current $150 → Target $75 - Measured monthly
- Order Processing Time: Current 4 hours → Target 15 minutes - Measured daily
- Customer Satisfaction (NPS): Current 32 → Target 65 - Measured quarterly
- Operational Cost: Current $2M/year → Target $500K/year - Measured monthly
- Revenue Per User: Current $25 → Target $45 - Measured quarterly
- Employee Productivity: Current 10 orders/day → Target 50 orders/day - Measured weekly
</prompt>

---

## 4. Measurement Methodology

### 4.1 Baseline Establishment

<prompt>
Define baseline establishment approach from:
- Current state analysis and metrics
- Measurement tools and data sources
- Baseline validation process

For each metric category:
**Category**: [Performance/Quality/Delivery/Operations/Business]

**Baseline Data Collection**: <prompt>How baseline data will be collected</prompt>

**Baseline Period**: <prompt>Time period for baseline measurement (e.g., "Last 3 months average")</prompt>

**Data Validation**: <prompt>How baseline data will be validated for accuracy</prompt>

**Baseline Documentation**: <prompt>Where baseline data is documented</prompt>

Include approach for metrics where baseline doesn't currently exist.
</prompt>

### 4.2 Measurement Tools and Infrastructure

<prompt>
Define measurement infrastructure from:
- Monitoring and observability requirements
- Analytics and reporting tools
- Data collection and aggregation systems

**Technical Metrics**:
- **Tools**: <prompt>List monitoring and observability tools (CloudWatch, Datadog, New Relic, etc.)</prompt>
- **Dashboards**: <prompt>Dashboard locations and access</prompt>
- **Automation**: <prompt>Automated data collection and alerting</prompt>

**Business Metrics**:
- **Tools**: <prompt>List business analytics and reporting tools</prompt>
- **Reports**: <prompt>Report locations and access</prompt>
- **Data Sources**: <prompt>Business systems providing data</prompt>

**Integration**:
- **Data Pipeline**: <prompt>How metrics data flows from sources to dashboards</prompt>
- **Aggregation**: <prompt>How data is aggregated and calculated</prompt>
</prompt>

### 4.3 Data Quality and Validation

<prompt>
Define data quality approach from:
- Measurement accuracy requirements
- Validation and verification processes
- Data governance and ownership

Include:
- **Accuracy Standards**: Required accuracy levels for different metric types
- **Validation Process**: How metric data is validated for correctness
- **Data Governance**: Who owns data quality for each metric
- **Issue Resolution**: Process for addressing data quality issues
</prompt>

---

## 5. Baseline and Target Definition

### 5.1 Baseline Summary

<prompt>
Create baseline summary table:

| Metric | Category | Current Baseline | Baseline Date | Data Source |
|--------|----------|------------------|---------------|-------------|
| [Metric name] | [Input/Outcome] | [Value] | [Date] | [Source] |

Include all controllable input and business outcome metrics.
</prompt>

### 5.2 Target Summary

<prompt>
Create target summary table:

| Metric | Category | Target | Target Date | Improvement | Success Threshold |
|--------|----------|--------|-------------|-------------|-------------------|
| [Metric name] | [Input/Outcome] | [Value] | [Date] | [%/Δ] | [Minimum acceptable] |

Calculate improvement percentage or delta for each metric.
Define success threshold (minimum acceptable improvement).
</prompt>

### 5.3 Target Validation

<prompt>
Validate targets from:
- Industry benchmarks and best practices
- Stakeholder expectations and commitments
- Technical feasibility assessment
- Resource and timeline constraints

For each target:
- **Rationale**: Why this target was chosen
- **Feasibility**: Assessment of achievability
- **Benchmark**: Industry or internal benchmark comparison
- **Risk**: Risks to achieving target
- **Mitigation**: How risks will be mitigated
</prompt>

---

## 6. Reporting and Ownership

### 6.1 Metric Ownership

<prompt>
Assign ownership for each metric from:
- Team structure and responsibilities
- Governance framework and accountability
- Stakeholder roles and commitments

Create ownership matrix:

| Metric | Owner | Backup Owner | Review Frequency | Escalation Path |
|--------|-------|--------------|------------------|-----------------|
| [Metric name] | [Name/Role] | [Name/Role] | [Frequency] | [Escalation process] |

Ensure every metric has clear ownership and accountability.
</prompt>

### 6.2 Reporting Cadence

<prompt>
Define reporting schedule from:
- Governance framework reporting requirements
- Stakeholder communication needs
- Sprint and milestone review cadence

**Daily Reports**:
- **Metrics**: <prompt>List metrics reported daily (typically operational and performance)</prompt>
- **Audience**: <prompt>Who receives daily reports</prompt>
- **Format**: <prompt>Report format and delivery method</prompt>

**Sprint/Weekly Reports**:
- **Metrics**: <prompt>List metrics reported per sprint or weekly</prompt>
- **Audience**: <prompt>Who receives sprint/weekly reports</prompt>
- **Format**: <prompt>Report format and delivery method</prompt>

**Monthly Reports**:
- **Metrics**: <prompt>List metrics reported monthly (typically business outcomes)</prompt>
- **Audience**: <prompt>Who receives monthly reports</prompt>
- **Format**: <prompt>Report format and delivery method</prompt>

**Quarterly Business Reviews**:
- **Metrics**: <prompt>List metrics reviewed quarterly with executives</prompt>
- **Audience**: <prompt>Who attends quarterly reviews</prompt>
- **Format**: <prompt>Review format and presentation approach</prompt>
</prompt>

### 6.3 Review and Action Process

<prompt>
Define review and action process from:
- Governance framework monitoring and escalation
- Sprint review and retrospective processes
- Continuous improvement approach

**Regular Reviews**:
- **Sprint Reviews**: <prompt>How metrics are reviewed in sprint reviews</prompt>
- **Retrospectives**: <prompt>How metrics inform retrospective discussions</prompt>
- **Steering Committee**: <prompt>How metrics are presented to steering committee</prompt>

**Action Triggers**:
- **Threshold Breaches**: <prompt>What happens when metrics breach thresholds</prompt>
- **Trend Analysis**: <prompt>How trends trigger proactive actions</prompt>
- **Course Correction**: <prompt>Process for adjusting approach based on metrics</prompt>

**Continuous Improvement**:
- **Metric Refinement**: <prompt>How metrics are refined based on learning</prompt>
- **Target Adjustment**: <prompt>Process for adjusting targets if needed</prompt>
- **New Metrics**: <prompt>How new metrics are added</prompt>
</prompt>

### 6.4 Success Celebration Criteria

<prompt>
Define success celebration approach from:
- Milestone achievements and targets
- Team motivation and recognition
- Stakeholder engagement and communication

**Celebration Triggers**:
- **Milestone Achievements**: <prompt>Which milestones warrant celebration</prompt>
- **Target Achievements**: <prompt>When targets are met or exceeded</prompt>
- **Team Recognition**: <prompt>How team achievements are recognized</prompt>

**Celebration Approach**:
- **Internal**: <prompt>How team celebrates internally</prompt>
- **Stakeholder**: <prompt>How achievements are communicated to stakeholders</prompt>
- **Customer**: <prompt>How customer is engaged in success celebration</prompt>
</prompt>

---

## Appendix A: Metric Definitions and Calculations

<prompt>
Provide detailed definitions and calculation methods for each metric:

### [Metric Name]

**Definition**: <prompt>Precise definition of what is measured</prompt>

**Calculation**: <prompt>Formula or method for calculating the metric</prompt>

**Units**: <prompt>Units of measurement (ms, %, $, count, etc.)</prompt>

**Aggregation**: <prompt>How data is aggregated (average, median, P95, sum, etc.)</prompt>

**Exclusions**: <prompt>What is excluded from the measurement</prompt>

**Example**: <prompt>Example calculation with sample data</prompt>

Provide for all key metrics to ensure consistent measurement.
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
| 1.0 | <prompt>Use current date</prompt> | <prompt>Extract author</prompt> | Initial Success Metrics Canvas per BLA standards |

---

*© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.*

*This Success Metrics Canvas follows Build Like Amazon (BLA) prescriptive guidance and CBO Value Hierarchy.*

*For support: BLA Practice Team: bla-practice@amazon.com*
