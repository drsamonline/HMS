# Security Policy

This document outlines the security policy and procedures for HHMS.
The full technical security design lives in [docs/SECURITY_ARCHITECTURE.md](docs/SECURITY_ARCHITECTURE.md).

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **Do not** disclose the vulnerability publicly.
2. Send an email or open a private issue with the details.
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

We aim to:

- **Acknowledge** reports within 48 hours
- **Assess** initial impact within 7 days
- **Release fixes** for critical issues within 30 days

## Data Protection

HHMS handles sensitive patient data. The system always:

- Encrypts data at rest and in transit where applicable
- Enforces role-based access controls ([docs/RBAC_CONSISTENCY.md](docs/RBAC_CONSISTENCY.md))
- Logs security-relevant events to the audit trail
- Follows applicable privacy regulations

Deployment note: the SQLite database is **server-owned only** — clients never open
it directly and communicate exclusively over the trusted hospital LAN via HTTP/JSON.

## Security Best Practices

### For Developers

- Never commit sensitive data (passwords, keys, secrets) — runtime secrets such as `data/secret.key` must stay out of version control.
- Use environment/configuration files for settings, not hard-coded values.
- Validate all user inputs against [docs/VALIDATION_RULES.md](docs/VALIDATION_RULES.md).
- Keep dependencies updated.
- Follow secure coding practices from [.ai/CODING_RULES.md](.ai/CODING_RULES.md).

### For Users / Administrators

- Change default passwords immediately.
- Keep the system updated.
- Use strong, unique passwords.
- Perform regular verified backups (see [docs/DATA_LIFECYCLE_AND_MAINTENANCE.md](docs/DATA_LIFECYCLE_AND_MAINTENANCE.md)).
- Restrict access to authorized users only; VACUUM and rollover operations are administrator-only.

## Security Updates

Security updates are announced through:

- GitHub releases
- [CHANGELOG.md](CHANGELOG.md) entries
- Security advisories (when applicable)
