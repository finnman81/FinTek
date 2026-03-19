# Spec Package Rewriter Workflow

## Overview

**Purpose**: Template-driven document generation workflow that transforms specification packages into custom documents through systematic template processing, content generation, and quality assurance with full source traceability.

**Key Benefits**: 
- Flexible document creation from existing specification packages
- Template-driven approach for organizational consistency
- Source traceability and fact-checking for content accuracy
- Reusable templates for multiple projects and audiences

## Prerequisites

### Context Sources and Discovery Protocol
**Every task must load context from these standardized locations in this order:**

1. **Current User Prompt** - Intelligent extraction of parameters
   - Extract specification package folder path if provided (default: `generated/design/specification-package-iteration-final`)
   - Extract template file location if provided (required - user must specify template)
   - Extract output destination if provided (default: `generated/spec-package-rewriter/`)
   - Extract any additional context or requirements
   - **CRITICAL**: Only request missing parameters that weren't provided in the prompt

2. **Specification Package Folder** - Source data for content generation
   - Validate folder exists and contains specification files
   - Inventory available components (requirements, architecture, security, etc.)
   - Load specification data for template processing
   - Establish source traceability framework

3. **Template File** - Document structure and prompt instructions
   - Load and parse template file from provided path
   - Extract prompt blocks and static content sections
   - Validate template format and syntax
   - Prepare template processing plan

## Execution Instructions

### Core Execution Rules

**CRITICAL CONSTRAINTS**:
- **Source-traceable information only** - All generated content must be traceable to specification package files
- **Never invent or assume** - Do not add information not present in specification package
- **Flag missing data explicitly** - When required data is not in sources, use "[Data not available in specification package]" or "[TBD - requires stakeholder input]" rather than inventing values
- **Template fidelity** - Preserve template structure and static content exactly
- **Fact-checking required** - Validate all generated content against source materials
- **Audit trail mandatory** - Document all information sources and processing steps

**EXECUTION PATTERN**:
1. **DISCOVER** inputs (specification package, template file, output destination)
2. **VALIDATE** all inputs for completeness and format compliance
3. **PROCESS** template systematically with source traceability
4. **VERIFY** generated content against specification package data
5. **ASSEMBLE** final document with audit trail documentation

**QUALITY ASSURANCE**:
- **Source verification** - Every statement must be traceable to specification files
- **Accuracy scoring** - Numerical assessment of content reliability
- **Audit documentation** - Complete trail of information sources and processing steps
- **Review flagging** - Identification of content requiring manual validation

### Focus Areas by Input Type

**When working with complete specification packages**:
- Focus on content extraction and synthesis
- Utilize all available specification components for rich content generation
- Ensure balanced coverage across requirements, architecture, and security domains
- Leverage detailed documentation for accurate responses

**When working with partial specification packages**:
- Identify available components and adapt template processing accordingly
- Clearly document limitations and missing information
- Focus on available data while noting gaps in audit trail
- Provide recommendations for completing missing specification components

**When working with complex templates**:
- Process prompt blocks systematically in document order
- Maintain clear separation between static and generated content
- Ensure consistent tone and style across generated sections
- Validate template structure preservation throughout processing

### Escalation Triggers

**Immediate escalation required when**:
- Specification package missing or incomplete for template requirements
- Template format invalid or contains unsupported syntax
- Generated content cannot be verified against specification sources
- Quality validation fails below acceptable thresholds
- Output destination inaccessible or conflicts with existing files

**Escalation process**:
1. Document specific issue and attempted resolution approaches
2. Identify minimum information needed to proceed
3. Present clear options and alternatives to user
4. Obtain explicit user decision before proceeding
5. Document decision rationale and continue processing

### Success Criteria

**Overall workflow success**:
- Complete custom document generated following template structure
- All prompt blocks processed with traceable content
- Audit trail documenting information sources
- Quality validation passing with acceptable accuracy scores

**Per-task success criteria**:
- Input discovery and validation completed successfully
- Template processing with full source traceability
- Content generation verified against specification package
- Final document assembly with quality assurance validation

## Workflow Structure

### Task 1: Input Discovery and Validation
**Purpose**: Discover and validate all required inputs for template processing
**Key Activities**: Specification package discovery, template file validation, output specification
**Deliverables**: Validated inputs with processing plan and component inventory

### Task 2: Template Processing and Content Generation
**Purpose**: Process template systematically with source-traceable content generation
**Key Activities**: Template parsing, prompt block processing, content generation with traceability
**Deliverables**: Generated content blocks with source documentation and accuracy validation

### Task 3: Quality Assurance and Fact-Checking
**Purpose**: Validate generated content accuracy and source traceability
**Key Activities**: Content verification, fact-checking, accuracy scoring, audit trail generation
**Deliverables**: Validated content with quality assessment and audit trail

### Task 4: Document Assembly and Output Generation
**Purpose**: Assemble final document with quality validation and audit documentation
**Key Activities**: Document assembly, format validation, audit trail integration, final output generation
**Deliverables**: Complete custom document with audit trail and quality assessment

## Key Features

### Template-Driven Processing
Systematic processing of markdown templates with embedded prompt blocks, preserving template structure while generating custom content based on specification package data.

### Source Traceability System
Tracking of information sources for all generated content, ensuring accuracy and enabling verification of all statements against specification package files.

### Quality Assurance Framework
Multi-layered validation including fact-checking, accuracy scoring, and audit trail generation to ensure content reliability and organizational compliance.

### Flexible Input Handling
Support for various specification package structures and template formats, with graceful handling of incomplete data and clear error reporting.

## Usage Recommendations

**Organizational Templates**: Use for consistent document formats across projects and teams
**Audience-Specific Documents**: Generate executive summaries, technical deep-dives, or compliance reports
**Custom Reporting**: Create project-specific reports following organizational standards
**Documentation Standardization**: Ensure consistent format and content across project deliverables

## Task Checklist

- [ ] **Task 1: Input Discovery and Validation**
  - [ ] Intelligent parameter extraction from user prompt
    - [ ] Extract specification package folder path from prompt (if provided)
    - [ ] Extract template file location from prompt (if provided)
    - [ ] Extract output destination from prompt (if provided)
    - [ ] **ONLY request missing parameters not provided in prompt**
  - [ ] Specification package folder discovery and validation
    - [ ] Use extracted path or default location (`generated/design`)
    - [ ] Validate folder exists and contains specification files
    - [ ] Inventory available specification components (requirements, architecture, security, etc.)
    - [ ] Generate component availability map for template processing
  - [ ] Template file processing and validation
    - [ ] Use extracted template file path (required - user must provide template)
    - [ ] Load template file and validate markdown format and structure
    - [ ] Extract all `<prompt>...</prompt>` blocks for content generation
    - [ ] Extract all `<execution-notes>...</execution-notes>` blocks for processing guidance
    - [ ] Identify static content sections for preservation
    - [ ] Generate template processing plan with tag type mapping
  - [ ] Output specification and environment preparation
    - [ ] Use extracted destination or default location (`generated/spec-package-rewriter/`)
    - [ ] Validate output path and resolve any conflicts
    - [ ] Prepare processing environment and context
    - [ ] Document input validation results

- [ ] **Task 2: Template Processing and Content Generation**
  - [ ] Specification package data loading and indexing
    - [ ] Load all available specification files systematically
    - [ ] Index content by type and section for efficient access
    - [ ] Establish source traceability framework
    - [ ] Prepare data context for prompt processing
  - [ ] Tag processing with source traceability
    - [ ] Process each `<prompt>` block in document order for content generation
    - [ ] Follow `<execution-notes>` instructions for processing guidance (do not generate content)
    - [ ] Generate content using specification package data as exclusive source
    - [ ] Track source files and sections used for each response
    - [ ] Maintain clear separation between tag instructions and generated content
    - [ ] Document processing steps and source attribution for each content block
  - [ ] Content generation quality control
    - [ ] Validate generated content against source materials
    - [ ] Ensure all statements are traceable to specification files
    - [ ] Flag any content that cannot be verified from sources
    - [ ] Generate preliminary accuracy assessment for each content block

- [ ] **Task 3: Quality Assurance and Fact-Checking**
  - [ ] Content verification
    - [ ] Systematically verify all generated statements against specification sources
    - [ ] Identify and document any unsupported or questionable content
    - [ ] Calculate accuracy scores for each generated content block
    - [ ] Generate detailed validation report with findings
  - [ ] Source traceability validation
    - [ ] Verify complete source attribution for all generated content
    - [ ] Validate source file references and section citations
    - [ ] Ensure traceability documentation is complete and accurate
    - [ ] Generate source mapping report for audit trail
  - [ ] Audit trail generation
    - [ ] Document all specification files used in content generation
    - [ ] Record processing steps and decision points
    - [ ] Generate audit trail with source mapping
    - [ ] Include quality assessment and validation results
    - [ ] Prepare audit trail file for output (markdown format with timestamp)

- [ ] **Task 4: Document Assembly and Output Generation**
  - [ ] Document assembly with template preservation
    - [ ] Replace `<prompt>` blocks with validated generated content
    - [ ] Remove all `<execution-notes>` blocks entirely (no content replacement)
    - [ ] Preserve template structure, formatting, and static content exactly
    - [ ] Integrate generated content seamlessly with template structure
    - [ ] Validate final document format and completeness
  - [ ] Final quality validation and review
    - [ ] Verify all `<prompt>` blocks have been processed and replaced with content
    - [ ] Verify all `<execution-notes>` blocks have been completely removed
    - [ ] Confirm template structure and formatting preservation
    - [ ] Validate content integration and document flow
    - [ ] Perform final accuracy and completeness check
  - [ ] Output generation and audit trail integration
    - [ ] Generate final custom document at specified output location
    - [ ] Create audit trail report file with enhanced timestamp: `audit-trail-[YYYY-MM-DD-HH-MM-SS].md`
    - [ ] Include quality assessment summary and recommendations in audit file
    - [ ] Provide processing summary and validation results in audit file
    - [ ] Document any limitations or areas requiring manual review
    - [ ] Save audit trail file to `audit/spec-rewriter/` directory with timestamp filename

- [ ] **Task 5: Final Document Cleanup and Quality Assurance**
  - [ ] Tag system cleanup
    - [ ] Remove ALL `<execution-notes>` sections from final document
    - [ ] Verify all `<prompt>` tags have been replaced with generated content
    - [ ] Ensure no template processing tags remain in output
    - [ ] Verify document is ready for customer/stakeholder presentation
  - [ ] TBD and placeholder review
    - [ ] Search entire document for "TBD" text and replace with actual values
    - [ ] Identify and resolve any remaining placeholder content
    - [ ] Ensure all cost figures, dates, and technical details are finalized
  - [ ] Consistency validation
    - [ ] Verify all numerical data is consistent across document sections
    - [ ] Cross-check totals and calculations for mathematical accuracy
    - [ ] Ensure terminology and naming conventions are consistent throughout
    - [ ] Validate that all references and citations are accurate
  - [ ] MCP integration audit (for pricing templates)
    - [ ] Verify MCP server responses match data presented in document
    - [ ] Cross-reference pricing data with state files in `pricing-state/` folder
    - [ ] Document all MCP calls made and data sources used in audit trail
    - [ ] Ensure pricing assumptions and limitations are clearly stated
  - [ ] Final completeness check
    - [ ] Confirm all identified services/components have corresponding analysis
    - [ ] Verify no sections are incomplete or missing critical information
    - [ ] Ensure document meets template objectives and user requirements
    - [ ] Validate document is ready for final delivery without further edits

- [ ] **Critical Execution Rules Compliance**
  - [ ] NEVER generate content not traceable to specification package files
  - [ ] ALWAYS preserve template structure and static content exactly
  - [ ] ALWAYS document source files used for each generated content block
  - [ ] ALWAYS validate generated content against specification sources
  - [ ] NEVER proceed with content that fails fact-checking validation
  - [ ] ALWAYS create audit trail file as concrete deliverable
  - [ ] ONLY use information present in specification package files
  - [ ] ALWAYS flag content requiring manual review or validation