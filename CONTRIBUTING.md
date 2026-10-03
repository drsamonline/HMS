# Contributing to HHMS

Thank you for considering contributing to HHMS! This document explains how to
contribute to the project. All contributions — code, documentation, or review —
must follow the rules below.

## Quick Start

1. Read [.ai/PROJECT_CONSTITUTION.md](.ai/PROJECT_CONSTITUTION.md) — the 12 locked project principles.
2. Review [.ai/PROJECT_STATE.md](.ai/PROJECT_STATE.md) for current objectives and batch status.
3. Check [ROADMAP.md](ROADMAP.md) for planned features and milestone position.
4. Browse the documentation catalogue in [docs/INDEX.md](docs/INDEX.md).
5. Ensure your contribution aligns with the project principles (see below).

## Development Workflow

HHMS development follows a strict sequential workflow — no step may be skipped:

```text
Specification → Review → Implementation → Code Review → Testing → Git Commit → Next Milestone
```

Work is combined into the **largest safe coherent batch**, audited against the
intended change set, and committed only after verification is green. The full
locked workflow is defined in [.ai/PROJECT_STATE.md](.ai/PROJECT_STATE.md).

## Code Contributions

- **Follow coding standards** — see [.ai/CODING_RULES.md](.ai/CODING_RULES.md) and [docs/NAMING_CONVENTIONS.md](docs/NAMING_CONVENTIONS.md).
- **No duplicate code** — reuse existing components; never create duplicate models, services, endpoints, or frontend modules.
- **Clear naming** — descriptive names for variables, functions, and classes.
- **Modular design** — keep components small and focused.
- **Documentation** — update relevant documentation with every change (docs are kept in sync with code).
- **Implementation rules** — respect [docs/IMPLEMENTATION_RULES.md](docs/IMPLEMENTATION_RULES.md) and [docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md).

## Documentation Contributions

- Keep documentation clear, concise, and unambiguous.
- Update [CHANGELOG.md](CHANGELOG.md) with significant changes.
- Ensure examples are accurate and tested.
- Add new documents to the catalogue in [docs/INDEX.md](docs/INDEX.md).

## Commit Messages

- Use the imperative mood ("Add", not "Added").
- First line: short summary (max 50 characters); body wrapped at 72 characters.
- Follow the conventional format defined in [docs/NAMING_CONVENTIONS.md](docs/NAMING_CONVENTIONS.md#10-git-commit-message-format):

  ```text
  feat: add patient registration form

  Implemented the patient registration UI with form validation.

  References: #12, D-001
  ```

- Types: `feat` · `fix` · `docs` · `style` · `refactor` · `test` · `chore`.

## Pull Request Process

1. Ensure all tests pass (see [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md)).
2. Update documentation as needed.
3. Describe your changes clearly and link related issues.
4. Verify compliance using [.ai/REVIEW_CHECKLIST.md](.ai/REVIEW_CHECKLIST.md).

## Project Principles

| Principle | Meaning |
|-----------|---------|
| **Simplicity First** | Prefer simple solutions over complex ones. |
| **No Scope Creep** | Stay within the frozen v1.0 requirements. |
| **One Feature Per Milestone** | Focus on completing one thing at a time. |
| **Offline First** | Design for LAN/offline operation; no internet dependency. |
| **Modular Architecture** | Build reusable, independent components. |
| **Docs With Every Change** | Keep documentation in sync with code. |

## Reporting Security Issues

Do **not** open a public issue for vulnerabilities. Follow [SECURITY.md](SECURITY.md).

## Questions?

Open an issue for discussion — contributions large and small are welcome.
