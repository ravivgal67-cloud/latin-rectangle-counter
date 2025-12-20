---
inclusion: always
---

# Development Methodology Guidelines

## Core Principles

### Correctness First
- All software must be developed with formal notions of correctness
- Property-based testing is mandatory for validating correctness properties
- Implementation must conform to specified correctness properties
- Tests provide evidence that software obeys correctness properties

### Specification-Driven Development
- Follow the three-artifact approach:
  1. Comprehensive specification including correctness properties
  2. Working implementation that conforms to specification
  3. Test suite providing evidence of correctness
- Requirements must follow EARS patterns and INCOSE quality rules
- Design documents must include testable correctness properties

### Testing Strategy
- **Dual Testing Approach**: Both unit tests and property-based tests are required
  - Unit tests: Verify specific examples, edge cases, error conditions
  - Property tests: Verify universal properties across all inputs
  - Together they provide comprehensive coverage
- Property-based tests must run minimum 100 iterations
- Each correctness property must be implemented by a single property-based test
- Tests must be tagged with explicit references to design document properties

### Implementation Guidelines
- Write minimal code that directly addresses requirements
- Avoid verbose implementations and unnecessary code
- Focus on essential functionality to keep code minimal
- Implementation-first development: implement feature before writing tests
- Get tests passing before completing any task - correct code is essential

### Quality Standards
- No tolerance for non-compliance with EARS patterns or INCOSE rules
- Requirements must be solution-free (focus on what, not how)
- Use active voice, avoid vague terms, no escape clauses
- One thought per requirement, explicit and measurable conditions
- Consistent, defined terminology throughout

### Workflow Discipline
- Execute one task at a time - do not automatically proceed to next task
- Complete all required code changes before validation steps
- Verify implementation against specified requirements
- Stop after completing requested task for user review

## Property-Based Testing Patterns

### Common Correctness Properties
1. **Invariants**: Properties preserved after transformation
2. **Round Trip Properties**: Operations with inverses return to original
3. **Idempotence**: Doing operation twice equals doing it once
4. **Metamorphic Properties**: Relationships between components
5. **Model Based Testing**: Optimized vs standard implementation
6. **Confluence**: Order of operations doesn't matter
7. **Error Conditions**: Bad inputs properly signal errors

### Special Requirements
- **Parsers/Serializers**: Always include round-trip properties
- **Pretty Printers**: Required for all parsers to enable round-trip testing
- **Grammar Validation**: Parse then print should preserve structure

## Documentation Standards
- Requirements: User stories with EARS-compliant acceptance criteria
- Design: Include architecture, components, data models, correctness properties
- Tasks: Numbered checklist with clear objectives and requirement references
- All documents must reference specific requirements granularly

This methodology ensures we build correct, well-tested software through systematic specification and validation.