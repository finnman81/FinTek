# Stage 6: Property Identification

## Overview

**Objective**: Identify testable properties for functional requirements to enable property-based testing in the build phase
**Dependencies**: 
- Complete requirements package available in project specification directory
**Persona Focus**: Test Architect

This stage identifies simple, testable properties for functional requirements that can be validated through property-based testing during implementation. Non-functional requirements (performance, security, compliance) are not suitable for property-based testing and should be validated through other testing approaches.

## Task 6.1: Requirements Analysis

**Status**: Not Started
**Dependencies**: Complete requirements package available in project specification directory

**Description**: Review and analyze all functional requirements to understand their structure and content

**Required Deliverable**: Complete understanding of functional requirements for property identification

### Key Activities
- **Review Functional Requirements**: Analyze functional requirements from last specification package iteration (exclude non-functional requirements)
- **Categorize Functional Requirements**: Group functional requirements by functional area and complexity
- **Identify Candidates**: Mark functional requirements that appear suitable for property-based testing

## Task 6.2: Property Identification

**Status**: Not Started
**Dependencies**: Requirements Analysis completion (Task 6.1)

**Description**: Identify testable properties for requirements using common property-based testing patterns

**Required Deliverable**: List of identified properties mapped to specific requirements

**Unique index** Give each identified property a unique index (0,1,2 ...)

### Key Activities
- **Apply Property Patterns**: Use common property-based testing patterns below to identify testable properties
- **Comprehensive Coverage**: For any requirement with testable properties, cover as many applicable scenarios as possible within given constraints to maximize test coverage and catch edge cases

## Common Property-Based Testing Patterns

### 1. **Round Trip Properties**
Operations with inverses that return to original value:
- `decode(encode(x)) == x` - Serialization/deserialization
- `parse(format(x)) == x` - Parsing and formatting
- `contains(insert(x, set), x) == true` - Insert then check existence

### 2. **Invariants**
Properties that remain constant despite changes:
- `map(f, list).length == list.length` - Collection size preservation
- `sort(list)` contains same elements - Content preservation
- `obj.start <= obj.end` - State consistency rules

### 3. **Idempotence**
Operations where doing it twice equals doing it once:
- `distinct(distinct(list)) == distinct(list)` - Duplicate removal
- `normalize(normalize(x)) == normalize(x)` - Data normalization
- Database updates have same effect when repeated

### 4. **Metamorphic Properties**
Relationships between inputs and outputs:
- `filter(predicate, list).length <= list.length` - Size relationships
- `max(list) >= min(list)` - Ordering relationships
- `intersection(A, B) ⊆ A` - Subset relationships

### 5. **Commutativity**
Order of operations doesn't matter:
- `add(x, y) == add(y, x)` - Addition operations
- `union(A, B) == union(B, A)` - Set operations

### 6. **Error Conditions**
Invalid inputs properly signal errors:
- Negative array indices throw errors
- Division by zero raises exception
- Type mismatches fail appropriately

### 7. **Associativity**
Grouping of operations doesn't matter:
- `concat(concat(a, b), c) == concat(a, concat(b, c))` - String/list concatenation
- `(x + y) + z == x + (y + z)` - Arithmetic operations
- `compose(f, compose(g, h)) == compose(compose(f, g), h)` - Function composition

### 8. **Identity Elements**
Operations with neutral elements:
- `add(x, 0) == x` - Addition with zero
- `concat(list, []) == list` - Concatenation with empty
- `multiply(x, 1) == x` - Multiplication with one

### 9. **Monotonicity**
Increasing inputs lead to increasing outputs:
- If `x <= y`, then `position(x, sorted_list) <= position(y, sorted_list)` - Ordering preservation
- Later events have later timestamps - Time ordering
- Increment operations increase values - Counter behavior

**Multiple Properties**: Some requirements may exhibit multiple testable properties (e.g., a data transformation requirement might have both invariant and round-trip properties). 
**Limit to maximum 3 properties per requirement** to maintain focus and avoid over-testing
**Focus on Universal Rules**: Identify properties that can be tested across many inputs
**Map Properties to Requirements**: Link each identified property to specific requirement IDs.
**Use only the original requirement IDs** from the requirements - do not create or make up new requirement indexes

## Task 6.3: Property Documentation

**Status**: Not Started
**Dependencies**: Property Identification completion (Task 6.2)

**Description**: Create documentation of all identified properties for build agent handoff

**Required Deliverable**: create `properties.md` file in `generated/design/[project-name]/` folder, NOT the specification-package-iteration-X folder

**Test Case Constraints**: Instruct build agent to generate at most 200 total test cases for the test. Critical requirements and properties should get more test cases than less critical ones


### Key Activities
- **Complete Functional Requirements Analysis**: Document ALL functional requirements with their property analysis status
- **Functional Requirements WITH Properties**: For each testable functional requirement, include full requirement text, property type(s), specific property description(s), and testing approach. 
- **Multiple properties per requirement are allowed** when appropriate (e.g., a requirement may have both an invariant and a round-trip property), but limit to maximum 3 properties per requirement
- **Functional Requirements WITHOUT Properties**: For each non-testable functional requirement, include full requirement text and clear reason why no property was identified
- **Non-Functional Requirements Exclusion**: Explicitly note that non-functional requirements (performance, security, compliance) are excluded from property-based testing analysis
- **Analysis Summary**: Provide total counts and property coverage percentage
- **Use only the original requirement IDs** from the requirements - do not create or make up new requirement indexes

### Acceptance Criteria

- **All Functional Requirements Analyzed**: All functional requirements have been analyzed for testable properties
- **Clear Property Statements**: Each property is simply and clearly described
- **Requirements Traceability**: Properties are linked to specific functional requirements
- **Build Agent Ready**: Documentation is simple and straightforward

### Integration Points

- **Documentation Generation**: Property specifications inform documentation generation
- **Output Organization**: Properties identified and described in properties.md file
- **Build Agent Handoff**: Properties serve as input for test implementation

## Task Checklist

- [ ] **Task 6.1: Requirements Analysis**
  - [ ] Review functional requirements from last specification package iteration (exclude non-functional requirements)
  - [ ] Categorize functional requirements by functional area and complexity
  - [ ] Identify functional requirements that appear suitable for property-based testing

- [ ] **Task 6.2: Property Identification**
  - [ ] Apply common property-based testing patterns to identify testable properties
  - [ ] Focus on easily testable properties with universal rules (idempotency, invariants, commutativity, reversibility, etc.)
  - [ ] For requirements with testable properties, cover as many applicable scenarios as possible within given constraints to maximize test coverage
  - [ ] Map identified properties to specific requirement IDs (use only original requirement IDs from requirements - do not create new indexes)
  
- [ ] **Task 6.3: Property Documentation**
  - [ ] Create `properties.md` file in `generated/design/[project-name]/` folder with complete functional requirements analysis showing:
    - that "Properties generated by design agent"
    - The specification package folder where you found the functional requirements used to derive the properties
    - ALL functional requirements with full text
    - Functional requirements WITH properties: property type(s), description(s), and testing approach
    - Functional requirements WITHOUT properties: clear reason why no property identified
    - Explicit note that non-functional requirements are excluded from property-based testing analysis
    - Analysis summary with total counts and coverage percentage
  - [ ] Never mention date and version
  - [ ] No other analysis, recommendation, testing approach, statistics or any other sections, keep it simple
  