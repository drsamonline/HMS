# CODING RULES

## General Principles

### 1. No Duplicate Code (DRY)

- Reuse existing functions and modules
- Extract common logic into shared utilities
- Copy-paste is acceptable only when reuse would violate simplicity

### 2. No Hardcoding

- Use configuration files for environment-specific values
- Define constants at the top of files or in dedicated config modules
- Never hardcode paths, URLs, credentials, or magic numbers

### 3. Clear Naming

- Use descriptive names for variables, functions, classes, and files
- Avoid abbreviations unless they are universally understood
- Names should reveal intent, not type

### 4. Reusable Components

- Build small, focused components with single responsibilities
- Minimize dependencies between components
- Design for composition over inheritance

### 5. Separate Business Logic

- Keep business logic separate from UI, database, and infrastructure code
- Business rules should be testable without external dependencies
- Use clear boundaries between layers

### 6. No Unrelated File Modifications

- Only modify files relevant to the current task
- Do not reformat or refactor unrelated code
- Keep commits focused and atomic

---

## Code Style

### Formatting

- Follow .editorconfig settings
- Consistent indentation (spaces, not tabs)
- Maximum line length: 100 characters (preferred), 120 (hard limit)

### Comments

- Comment WHY, not WHAT (code should explain what it does)
- Keep comments up to date with code changes
- Remove commented-out code before committing

### Functions

- Keep functions small (ideally under 30 lines)
- One function = one responsibility
- Limit parameters (3 or fewer preferred)

### Files

- One class or module per file (generally)
- Keep files under 500 lines when possible
- Organize imports logically

---

## Error Handling

- Handle errors explicitly
- Use meaningful error messages
- Log errors appropriately
- Never silently swallow exceptions

---

## Testing

- Write tests for business logic
- Tests should be deterministic
- Name tests descriptively
- Test edge cases and error conditions

---

## Documentation

- Update docs with every code change
- Document public APIs and interfaces
- Include usage examples where helpful
- Keep README files current

---

## Review Checklist

Before committing code:

- [ ] No duplicate code
- [ ] No hardcoded values
- [ ] Clear, descriptive naming
- [ ] Business logic separated from infrastructure
- [ ] Only relevant files modified
- [ ] Tests pass
- [ ] Documentation updated
