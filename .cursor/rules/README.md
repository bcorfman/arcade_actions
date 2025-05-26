# Cursor Rules Organization

## Directory Structure
```
.cursor/rules/
├── README.md
├── dependency_injection.rules
├── testing.rules
├── code_style.rules
├── security.rules
└── performance.rules
```

## Rule Categories
Each rules file should focus on a specific domain:

- `dependency_injection.rules`: Rules for dependency injection patterns
- `testing.rules`: Rules for test coverage and testability
- `code_style.rules`: Rules for code formatting and style
- `security.rules`: Rules for security best practices
- `performance.rules`: Rules for performance optimization

## Conflict Prevention

1. **Rule Naming Convention**
   - Prefix rule names with their domain: `DI_`, `TEST_`, `STYLE_`, etc.
   - Example: `DI_ConstructorInjection` instead of just `ConstructorInjection`

2. **Rule Scoping**
   - Each rule should only check for patterns in its domain
   - Avoid overlapping checks between different rule files
   - Use specific file patterns to limit rule scope

3. **Rule Dependencies**
   - Document dependencies between rules
   - Use rule priorities to handle potential conflicts
   - Example: Testing rules might depend on dependency injection rules

4. **Rule Validation**
   - Run `cursor validate-rules` to check for conflicts
   - Fix any reported conflicts before committing

## Adding New Rules

1. Choose the appropriate domain file
2. Follow the naming convention
3. Document any dependencies on other rules
4. Test the rule in isolation
5. Run the validation tool
6. Update this README if adding a new domain

## Rule Severity Levels

- `error`: Must be fixed immediately
- `warning`: Should be fixed soon
- `suggestion`: Consider fixing when convenient

## Rule Testing

Before committing new rules:
1. Test rules in isolation
2. Test rules in combination
3. Verify no false positives
4. Check for performance impact 