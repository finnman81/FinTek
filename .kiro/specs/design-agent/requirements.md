# Design Agent Workflow - Requirements

## Purpose

Transform project documents into implementation-ready specification packages through a systematic, quality-driven workflow that ensures enterprise-grade standards and comprehensive security assessment.

## Business Problem

Traditional specification development suffers from:
- **Incomplete Requirements**: Teams proceed with poorly structured requirements, causing implementation delays
- **Poor Design Quality**: Specifications lack depth, contain inconsistencies, fail enterprise standards  
- **Security Gaps**: Security considerations added as afterthought, leading to vulnerabilities
- **Quality Inconsistency**: No systematic approach to ensure implementation readiness

## Solution Approach

### Orchestrated Workflow with Modular Architecture

The workflow transforms project documents into enterprise-grade specification packages through systematic progression from context capture to final delivery:

**Stage 0: Session Management**
- Execution mode detection (new session, continuation, recovery)
- Customer context capture (project goals, technical preferences, organizational context)
- Workflow state initialization and context source establishment
- Handoff protocols for seamless workflow progression

**Stage 1: Project Analysis**
- Assess project complexity and provide workflow recommendations
- Analyze document count, size, and types to determine execution strategy
- Provide time estimates and session management guidance
- Document project characteristics for context-aware execution

**Stage 2: Requirements Generation**
- Conduct comprehensive three-category input assessment analysis across project-context, technical-knowledge, and organization-context folders
- Extract integration requirements from external reference materials without misinterpreting them as build targets
- Apply organizational policies and standards as architectural constraints
- Transform project-specific context into structured requirements packages based purely on business needs
- Generate functional/non-functional requirements with category-specific traceability matrix
- Establish foundation for architecture design with clear separation of concerns
- Maintain requirements purity without influence from existing code patterns

**Stage 3: Architecture Generation**
- **Task 3.1: Requirements & Domain Research**: Analyze requirements, load steering documents, decompose into research domains, execute focused research with context management, apply simplicity gate
- **Task 3.2: Architecture Design**: Load research files, validate scope, design system/component/data/API architecture with Mermaid diagrams
- **Task 3.3: Gap Analysis & Targeted Research**: Review for completeness, identify gaps (5-10 max), execute targeted research, create service-to-requirement mapping
- **Task 3.4: Decision Documentation**: Create ADRs in separate files
- **Task 3.5: Validation & Quality Assessment**: Requirements coverage (95%+), integration validation, service limits assessment, quality scoring (≥85/100 required)
- **Reference System Integration**: Incorporate project-code analysis from Stage 1 to inform architecture decisions
- Document architecture decisions with rationale and alternatives
- Balance requirements-driven design with existing system integration opportunities
- Comprehensive architecture integration validation with service limits assessment

**Stage 4: Holistic Quality Assessment**
- Multi-dimensional quality assessment across all domains (requirements + architecture together)
- Numerical scoring (0-100) with mandatory 90/100 threshold
- Iterative refinement optimizing requirements and architecture holistically
- Complete audit trail with score sheets for each iteration

**Stage 5: Security Assessment**
- AWS-compliant security threat modeling using STRIDE methodology
- Comprehensive security controls mapping and mitigation strategies
- Integration with specification package for complete security posture
- Security testing framework with concrete test cases

**Stage 6: Property Identification**
- **Task 6.1**: Functional requirements analysis and categorization for property identification
- **Task 6.2**: Identify simple, testable properties using universal rules such as idempotency, invariants, commutativity, and reversibility
- **Task 6.3**: Create clear property statements with property identification and requirement traceability for build agent implementation

**Stage 7: Documentation Generation**
- Tools prescriptive guidance generation with comprehensive MCP servers and Skills inventory
- Project-specific MCP and Skills recommendations with implementation guidance
- Executive summary creation synthesizing final specification package
- Stakeholder communication materials and implementation readiness assessment

**Stage 8: Output Organization**
- Project folder structure validation and organization
- Iterative content management with proper file naming
- Specialized content organization (threat model, supplement material, executive summary)
- Final handoff preparation with comprehensive documentation

**Stage 9+: Feedback Integration (Iterative)**
- Stakeholder feedback collection and analysis from `project-doc/feedback/iteration-N/` folders
- Dynamic improvement task generation based on feedback content and scope
- Complete project folder regeneration with new iteration folders (project-name-iteration-N)
- Regeneration of all deliverables: specification-package, score-sheet, executive-summary, threat-model, supplement-material
- Changelog creation documenting changes from previous iteration
- Continuous quality improvement through stakeholder-driven enhancements
- Support for unlimited feedback cycles with proper task numbering and traceability

## Key Capabilities

### Organized Output Management
- **Direct Output Structure**: All deliverables organized directly in generated/design/ folder with structured layout
- **Iteration Management**: Sequential specification packages (iteration-1, iteration-2, etc.) with final iteration named "iteration-final"
- **Score Sheet Organization**: All assessment score sheets in root with clear numbering, final named "iteration-final"
- **Threat Model Integration**: Dedicated folder for comprehensive security assessment
- **Supporting Documentation**: Organized supplement material including input assessment analysis

### Enhanced Input Assessment Analysis
- **Three-Category Requirements Processing**: Systematic analysis across three distinct requirements categories (project-context, technical-knowledge, organization-context)
- **Context Classification**: Automatic distinction between "what we're building" vs "what we're integrating with" vs "organizational constraints"
- **Technical Knowledge Integration**: Analysis of external reference materials to extract integration requirements without misinterpreting them as build targets
- **Organizational Policy Application**: Automatic application of company standards, naming conventions, and compliance requirements across all architecture decisions
- **Project Context Extraction**: Business, technical, and user context extraction from project-specific materials
- **Gap Identification**: Category-specific identification of missing information and constraints
- **Stakeholder Mapping**: Complete stakeholder analysis with requirements categorization across requirements input types
- **Generation Readiness**: Requirements assessment of readiness to proceed with specification generation
- **Reference System Separation**: Legacy system analysis handled separately in Stage 1 to avoid biasing requirements

### Iterative Feedback Integration
- **Stakeholder Feedback Processing**: Systematic analysis of feedback documents from multiple stakeholder types (business, technical, security, operational)
- **Change Detection Engine**: Content fingerprinting using SHA-256 hashing to identify new, modified, and unchanged inputs for incremental processing
- **Conflict Detection System**: Semantic analysis to identify contradictions between new feedback and existing decisions with automated conflict categorization
- **User-Guided Conflict Resolution**: Interactive resolution workflow with conflict reports, resolution options, and impact analysis
- **Incremental Processing**: Selective analysis of only changed inputs with cached result reuse for efficiency (target: <50% of full regeneration time)
- **Dynamic Task Generation**: Automatic generation of improvement tasks based on feedback content and scope, following coding agent's Task 1 pattern
- **Feedback Categorization**: Classification of feedback into requirements changes, architecture modifications, security enhancements, and quality improvements
- **Intelligent Specification Merging**: Update existing specifications while preserving approved decisions with change annotations
- **Iteration Management**: Support for unlimited feedback cycles with proper task numbering (Task 8, 9, 10+) and complete project folder iterations
- **Traceability Maintenance**: Complete audit trail linking feedback documents to generated improvement tasks and specification changes
- **Version Management**: Complete specification evolution history with conflict resolution documentation and changelog generation
- **Scope Impact Assessment**: Analysis of feedback impact on project scope, timeline, and resource requirements with severity classification

### Quality Assurance
- **Systematic Assessment**: Multi-dimensional evaluation across 5 quality categories
- **Numerical Scoring**: 0-100 scale with detailed feedback and improvement recommendations
- **Mandatory Threshold**: 90/100 minimum score before implementation readiness
- **Progress Tracking**: Transparent iteration management with score progression

### Security Integration
- **STRIDE-based Analysis**: Systematic threat identification across all categories
- **AWS Standards Compliance**: Baseline Security Controls (BSC) mapping
- **Actionable Mitigations**: Specific security controls with implementation guidance
- **Testing Framework**: Concrete security test cases and validation procedures

### Implementation Readiness
- **Complete Documentation**: All specification components present and validated
- **Traceability**: Requirements linked to business objectives and source documents
- **Development Support**: User stories with acceptance criteria and implementation guidance
- **Quality Validation**: Stakeholder confirmation and development team approval

### Research-Driven Architecture Generation
- **Task 3.1: Requirements & Domain Research**: Analyze requirements and execute focused domain research
  - Analyze requirements and context (functional, non-functional, customer mode)
  - Load relevant steering documents from `.kiro/steering/design-agent/architecture/`
  - Decompose into research domains based on project type
  - Execute domain research with context management 
  - Write findings to file immediately after each domain to manage context
  - Apply simplicity gate to avoid over-engineering
- **Task 3.2: Architecture Design**: Design complete system architecture
  - Load research files and validate scope against stated requirements
  - Design system architecture with high-level components
  - Design component specifications with interfaces and data models
  - Design data architecture, API specifications, and integration patterns
  - Create Mermaid diagrams for system and component architecture
- **Task 3.3: Gap Analysis & Targeted Research**: Identify and fill gaps
  - Review architecture documents for completeness
  - Identify specific gaps and execute targeted research
  - Create service-to-requirement mapping with traceability
- **Task 3.4: Decision Documentation**: Document decisions
  - Create Architecture Decision Records (ADRs) in separate files
  - Design monitoring, observability, and disaster recovery strategies
- **Task 3.5: Validation & Quality Assessment**: Validation before implementation
  - Requirements coverage analysis (95%+ threshold)
  - Component integration validation
  - Service limits impact assessment with mitigation strategies
  - Technical feasibility assessment
  - Overall quality score (≥85/100 required)

### Enhanced Project Input System
- **Stage-Separated Input Processing**: Requirements generation uses three categories; architecture generation incorporates reference system analysis
- **Integration Requirements Extraction**: Analyze external API documentation and system references to derive integration constraints without treating them as build targets
- **Policy-Driven Architecture**: Automatic application of organizational standards, AWS resource tagging, security policies, and compliance requirements
- **Reference System Integration**: Systematic analysis of existing codebases in Stage 1, incorporated into architecture decisions in Stage 3
- **Context Separation**: Clear distinction between project requirements, external integration needs, organizational constraints, and reference system considerations
- **Traceability by Category**: Requirements traced to specific input categories; architecture decisions traced to requirements plus reference analysis
- **Category-Specific Quality Assessment**: Validation of specifications against requirements categories with detailed compliance reporting

### Modular Task Architecture
- **Clear Organization**: Each workflow stage has its own focused module for easy navigation
- **Focused Content**: Each module covers specific workflow aspects without overlap
- **Easy Maintenance**: Updates can be made to specific areas without affecting other stages
- **Better Usability**: Find relevant instructions quickly without searching through large files
- **Feedback Integration Module**: Dedicated task module (08-incorporate-feedback.md) providing systematic approach for analyzing stakeholder feedback and generating improvement tasks

## Success Criteria

### Process Outcomes
- **Organized Deliverables**: All outputs properly organized in single project folder structure
- Comprehensive input assessment analysis establishing generation foundation
- Complete specification package with all required components
- Minimum 90/100 quality score across all assessment dimensions
- Comprehensive threat model with actionable security mitigations
- Stakeholder confirmation of implementation readiness

### Quality Standards
- Requirements traceable to business objectives with clear acceptance criteria
- Architecture decisions documented with rationale and alternatives
- User stories with detailed implementation guidance and measurable outcomes
- Security posture clearly defined with comprehensive threat mitigation

## When to Use This Workflow

### Optimal Scenarios
- **Complex Enterprise Projects** requiring comprehensive specification development
- **Security-Critical Systems** needing integrated threat modeling and controls
- **Multi-Stakeholder Initiatives** requiring structured documentation and communication
- **AWS Professional Services Engagements** following enterprise delivery standards
- **Quality-Critical Environments** where 90/100 standard is essential for success
- **Iterative Refinement Projects** where stakeholder feedback drives continuous specification improvement
- **Collaborative Development Initiatives** requiring multiple review cycles and stakeholder input integration

