# Spec Package Rewriter - Design Document

## Architecture Overview

This workflow implements a template-driven document generation system that transforms specification packages into custom documents through systematic template processing, content generation, and quality assurance with full source traceability.

The system operates through three main phases: Input Discovery and Validation, Template Processing and Content Generation, and Output Assembly with Quality Assurance.

## System Architecture

### Input Discovery and Validation Phase

**Specification Package Discovery**:
- Intelligent extraction from user prompt when specification package path is provided
- Default suggestion: `generated/design/specification-package-iteration-final` folder relative to workspace when not specified
- Fallback to highest numbered iteration if iteration-final not available
- User override capability for custom specification package locations
- Validation of specification package structure and completeness
- Inventory of available specification components (requirements, architecture, etc.)

**Template File Processing**:
- Intelligent extraction from user prompt when template file path is provided
- User must provide template file path (no default - templates are user-specific)
- Template format validation (markdown with embedded prompt blocks)
- Prompt block extraction and syntax validation
- Template structure analysis for processing planning

**Output Specification**:
- Intelligent extraction from user prompt when output destination is provided
- Default suggestion: `generated/spec-package-rewriter/` folder when not specified
- Output file destination determination based on template name or user specification
- Output format validation and path resolution
- Conflict detection and resolution (existing file handling)

### Template Processing Engine

**Template Parser**:
- Markdown template parsing with prompt block identification
- Syntax validation for `<prompt>...</prompt>` blocks
- Content segmentation (static text vs. dynamic prompt blocks)
- Processing order determination and dependency analysis

**Content Generation Engine**:
- Specification package data loading and indexing
- Prompt block processing using specification data as context
- Source traceability tracking for all generated content
- Fact-checking and validation against source materials

**Quality Assurance System**:
- Generated content verification against specification package files
- Hallucination detection and prevention
- Source mapping and audit trail generation
- Content accuracy scoring and validation

### Output Assembly and Validation

**Document Assembly**:
- Template structure preservation with prompt block replacement
- Formatting and markdown structure maintenance
- Content integration with source traceability annotations
- Final document generation and validation

**Audit Trail Generation**:
- Source file mapping for each generated section
- Processing step documentation and validation results
- Quality metrics and accuracy assessment
- Traceability report generation

## Component Design

### Input Discovery Component

**Specification Package Validator**:
```
Input: Folder path (default: generated/design)
Process: 
  - Verify folder exists and contains specification files
  - Inventory available components (requirements.md, architecture/, etc.)
  - Validate specification package completeness
  - Generate component availability map
Output: Validated specification package inventory
```

**Template Processor**:
```
Input: Template file path
Process:
  - Parse markdown template structure
  - Extract prompt blocks with syntax validation
  - Identify static content sections
  - Validate template format compliance
Output: Parsed template structure with prompt inventory
```

### Content Generation Component

**Prompt Processing Engine**:
```
Input: Prompt block + Specification package data
Process:
  - Load relevant specification files based on prompt context
  - Generate content using specification data as source
  - Track source files used for content generation
  - Validate generated content against source materials
Output: Generated content with source traceability
```

**Fact-Checking Validator**:
```
Input: Generated content + Source specification files
Process:
  - Verify all statements against source materials
  - Identify unsupported or hallucinated content
  - Generate accuracy score and validation report
  - Flag content requiring review or revision
Output: Validation results with accuracy assessment
```

### Output Assembly Component

**Document Generator**:
```
Input: Template structure + Generated content blocks
Process:
  - Replace prompt blocks with generated content
  - Preserve template formatting and structure
  - Integrate source traceability annotations
  - Generate final document with quality metadata
Output: Complete custom document with audit trail
```

## Processing Workflow

### Phase 1: Input Discovery and Validation

**Step 1.1: Specification Package Discovery**
- Check for default `generated/design` folder in workspace
- If not found or user specifies custom path, validate provided location
- Inventory specification package components and structure
- Generate availability map for template processing

**Step 1.2: Template File Validation**
- Load and parse template file from user-provided path
- Validate markdown format and prompt block syntax
- Extract all `<prompt>...</prompt>` blocks with content
- Verify template structure and processing requirements

**Step 1.3: Output Specification**
- Determine output file destination (user-provided or default)
- Validate output path and handle existing file conflicts
- Prepare output environment and processing context

### Phase 2: Template Processing and Content Generation

**Step 2.1: Specification Data Loading**
- Load all available specification package files
- Index content by type (requirements, architecture, security, etc.)
- Prepare data context for prompt processing
- Establish source traceability framework

**Step 2.2: Prompt Block Processing**
- Process each prompt block sequentially
- Generate content using specification package data as context
- Track source files and sections used for each response
- Validate generated content against source materials

**Step 2.3: Quality Assurance and Fact-Checking**
- Verify all generated content against specification sources
- Identify and flag any unsupported statements
- Generate accuracy scores and validation reports
- Create audit trail documentation

### Phase 3: Output Assembly and Validation

**Step 3.1: Document Assembly**
- Replace prompt blocks with validated generated content
- Preserve template structure and formatting
- Integrate source traceability annotations
- Generate complete custom document

**Step 3.2: Final Validation and Audit Trail**
- Validate final document completeness and accuracy
- Generate audit trail report
- Document source mapping and processing steps
- Provide quality assessment and recommendations

## Template Format Specification

### Supported Template Structure
```markdown
# Document Title

Static content preserved exactly as written in the template.

## Section with Generated Content

<prompt>
Generate a summary of functional requirements from the specification package.
Include requirement categories, key features, and acceptance criteria.
Focus on business value and user impact.
</prompt>

More static content that remains unchanged.

## Architecture Overview

<prompt>
Create an architecture overview based on the system architecture documentation.
Include high-level components, data flow, and technology stack.
Highlight key architectural decisions and their rationale.
</prompt>

Final static content preserved in output.
```

### Prompt Block Processing Rules

**Syntax Requirements**:
- Must use `<prompt>` and `</prompt>` tags exactly
- Prompt content should be clear, specific instructions
- Multiple lines supported within prompt blocks
- No nested prompt blocks allowed

**Content Generation Rules**:
- All generated content must be traceable to specification package files
- Prompt instructions guide content focus and format
- Generated content replaces entire prompt block including tags
- Source files used must be documented in audit trail

**Quality Validation Rules**:
- Generated content verified against source specification files
- Unsupported statements flagged and removed or revised
- Accuracy score calculated based on source traceability
- Audit trail documents all information sources

## Source Traceability System

### Traceability Framework
```
For each generated content block:
- Source Files: List of specification files used
- Source Sections: Specific sections or content referenced
- Generation Method: How content was derived from sources
- Accuracy Score: Validation score against source materials
- Review Status: Manual review required or auto-validated
```

### Audit Trail Structure
**File**: `audit-trail-[timestamp].md` (saved alongside generated document)

```markdown
# Audit Trail Report

## Processing Summary
- Template File: [path/to/template.md]
- Specification Package: [path/to/spec/package]
- Output Document: [path/to/output.md]
- Processing Date: [timestamp]

## Content Generation Details

### Prompt Block 1: [First 50 characters of prompt]
- **Source Files Used**: 
  - requirements/functional-requirements.md (sections 2.1-2.3)
  - requirements/user-stories.md (complete file)
- **Generated Content Length**: 247 words
- **Accuracy Score**: 95/100
- **Validation Status**: Auto-validated

### Prompt Block 2: [First 50 characters of prompt]
- **Source Files Used**:
  - architecture/system-architecture.md (sections 1.1, 3.2)
  - architecture/adrs/adr-001-technology-stack.md (complete file)
- **Generated Content Length**: 189 words
- **Accuracy Score**: 92/100
- **Validation Status**: Auto-validated

## Quality Assessment
- **Overall Accuracy Score**: 93.5/100
- **Source Coverage**: 8 of 12 available specification files used
- **Validation Issues**: None identified
- **Recommendations**: Document ready for use
```

## Error Handling and Recovery

### Input Validation Errors
- **Missing Specification Package**: Provide clear guidance on expected structure
- **Invalid Template Format**: Specific error messages for syntax issues
- **Inaccessible Files**: Permission and path resolution guidance

### Processing Errors
- **Insufficient Source Data**: Graceful handling when specification data is incomplete
- **Prompt Processing Failures**: Clear error messages and recovery options
- **Quality Validation Failures**: Detailed feedback on accuracy issues

### Output Generation Errors
- **File System Issues**: Path resolution and permission handling
- **Format Validation Failures**: Template structure and content validation
- **Audit Trail Generation Issues**: Fallback documentation options

## Quality Assurance Framework

### Content Accuracy Validation
- **Source Verification**: All statements must be traceable to specification files
- **Fact-Checking**: Systematic validation against source materials
- **Accuracy Scoring**: Numerical assessment of content reliability
- **Review Flagging**: Identification of content requiring manual review

### Template Processing Validation
- **Format Compliance**: Ensure output maintains template structure
- **Completeness Check**: Verify all prompt blocks were processed
- **Content Integration**: Validate seamless integration of generated content
- **Quality Metrics**: Assessment of processing success

### Audit Trail Validation
- **Source Documentation**: Complete mapping of information sources
- **Processing Steps**: Detailed documentation of generation process
- **Quality Assessment**: Accuracy scores and validation results
- **Traceability Verification**: Ensure all content is properly sourced

## Integration Patterns

### Upstream Integration
- **Design Agent Output**: Direct integration with specification packages
- **Template Management**: Support for organizational template libraries
- **User Context**: Integration with user preferences and requirements

### Downstream Integration
- **Document Management**: Integration with organizational document systems
- **Version Control**: Support for document versioning and updates
- **Quality Reporting**: Integration with quality assurance systems

## Success Metrics

### Processing Success
- **Template Processing Rate**: Percentage of prompt blocks successfully processed
- **Content Accuracy Score**: Average accuracy of generated content
- **Source Coverage**: Percentage of specification package utilized
- **Processing Time**: Efficiency of template processing workflow

### Quality Metrics
- **Traceability Score**: Percentage of content with clear source attribution
- **Validation Success Rate**: Percentage of content passing fact-checking
- **User Satisfaction**: Feedback on generated document quality
- **Template Reusability**: Success rate of template reuse across projects

## Scalability Considerations

### Template Complexity
- Support for complex templates with multiple prompt blocks
- Efficient processing of large specification packages
- Scalable source traceability for documentation

### Performance Optimization
- Efficient specification package indexing and search
- Optimized prompt processing for large content volumes
- Streamlined audit trail generation and validation

### Extensibility
- Support for additional template formats and structures
- Extensible prompt processing capabilities
- Flexible output format support and customization