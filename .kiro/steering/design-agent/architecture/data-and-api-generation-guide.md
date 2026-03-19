---
inclusion: manual
---

# Data and API Architecture Documentation Guide

## Purpose

This guide helps determine when to create specialized documentation files for data architecture and API specifications versus integrating content into technical-specifications.md. The goal is to prevent over-documentation while ensuring complex design decisions are properly captured.

## Validation Framework

**Scope**: This framework applies ONLY to data-architecture.md and api-specifications.md. No other specialized files should be created.

**Core Principle**: Create separate files only when you are making significant design decisions that require detailed documentation and evaluation of alternatives.

**Validation Questions:**

1. **Design Authority**: Are YOU making design decisions, or using existing services?
   - Designing → Separate file likely needed
   - Using existing → Integrate into technical-specifications.md

2. **Abstraction Level**: Design level or usage level?
   - Design level (schema, endpoints, patterns) → Separate file
   - Usage level (calling APIs, storing data) → Integrate

3. **Decision Complexity**: Multiple approaches to evaluate?
   - Multiple design options → Separate file
   - Single obvious approach → Integrate

**Decision Process:**

**If ANY answer suggests "Integrate":**
- [ ] Do NOT create the specialized file (data-architecture.md or api-specifications.md)
- [ ] Document skip decision in `architecture-integration-validation.md`:
  - State: "Separate [data-architecture.md OR api-specifications.md] not needed"
  - Rationale: Which validation question(s) led to skip
  - Services: List services being used
  - Location: "Details documented in technical-specifications.md"
- [ ] Include details in technical-specifications.md

**If ALL answers suggest "Separate file":**
- [ ] Query AWS Knowledge MCP: "What are best practices for [data modeling OR API design] with [services]?"
- [ ] Create the specialized file (data-architecture.md or api-specifications.md)
- [ ] Document creation decision in `architecture-integration-validation.md`:
  - State: "Separate [data-architecture.md OR api-specifications.md] created"
  - Rationale: Why separate documentation needed
  - Scope: Brief summary of content

## Integration with Architecture Generation

This guidance is referenced during Task 3.2 (Architecture Design) of the architecture generation workflow. The validation framework helps maintain appropriate documentation scope while ensuring complex design decisions are properly captured and justified.

**Documentation Requirements:**
- All decisions (create or skip) must be documented in `architecture-integration-validation.md`
- Include specific rationale based on validation questions
- Reference this guide when documenting the decision process