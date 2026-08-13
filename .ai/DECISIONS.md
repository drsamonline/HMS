# DECISIONS

## Architectural Decision Records (ADRs)

---

## D-001: Repository First Development

**Status:** LOCKED

**Date:** 2025-01-30

### Context

The HHMS project requires a clear, documented foundation before any code development begins. The repository itself serves as the single source of truth for all project information.

### Decision

Adopt a "Repository First" approach where:

1. The repository structure is defined and created before any application code
2. All project rules, principles, and guidelines are documented upfront
3. AI context files are maintained to ensure consistent development sessions
4. Documentation evolves alongside code, never lagging behind

### Consequences

**Positive:**
- Clear project direction from the start
- Consistent development practices across sessions
- Easy onboarding for new contributors
- Reduced ambiguity in decision-making

**Negative:**
- Initial setup takes more time
- Documentation overhead must be maintained

### Rationale

This approach ensures that every development session has clear context and follows established principles. It prevents architectural drift and maintains project coherence over time.

### Compliance

This decision is LOCKED and cannot be changed without formal project governance review.

---

## Template for Future Decisions

## D-XXX: [Decision Title]

**Status:** [PROPOSED | ACCEPTED | REJECTED | LOCKED]

**Date:** [YYYY-MM-DD]

### Context

[What is the issue or situation that prompted this decision?]

### Decision

[What is the change that we're introducing or the choice that we're making?]

### Consequences

**Positive:**
- [List positive outcomes]

**Negative:**
- [List negative outcomes]

### Rationale

[Why was this decision made? What alternatives were considered?]

### Compliance

[Is this decision locked or can it be revisited?]


---

## D-002: LAN Desktop Client/Server Deployment

**Status:** LOCKED

**Date:** 2026-08-13

### Context

HHMS is intended for hospital LAN deployment with multiple client workstations and one server. The client must remain lightweight and must never open the shared database directly.

### Decision

HHMS will target a two-executable deployment:

- `HHMS-Server.exe` owns the FastAPI application and SQLite database.
- `HHMS-Client.exe` provides the desktop UI and communicates with the server over LAN using HTTP/JSON.

The client shall support automatic LAN server discovery with a manual server-address fallback.

The portable LAN release shall remain SQLite-first. PostgreSQL compatibility is retained for future deployments but is not a production prerequisite for the portable release.

The frontend shall use HTML/CSS/JavaScript inside a lightweight native Windows host; WebView2 is the current target host technology.

### Consequences

**Positive:**
- Centralized shared patient/database state.
- No direct database concurrency from clients.
- No requirement for Python or Node.js on client workstations.
- Lightweight frontend implementation.
- Suitable for low-resource hospital PCs.

**Negative:**
- Client requires the server to be reachable for shared data operations.
- Windows client packaging and WebView2 runtime distribution must be solved before release.

### Rationale

This matches the hospital LAN operating model, minimizes dependencies, and prevents a browser-first architecture from forcing a later desktop rewrite.
