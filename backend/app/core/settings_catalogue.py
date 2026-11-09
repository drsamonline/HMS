"""
The settings catalogue.

Every value the server reads from configuration, described once: what group it
belongs to, what type it is, what it defaults to, whether changing it needs a
restart, and whether it is a secret.

The specification asks for a hospital administrator to configure the system
without editing a `.env` file. That is impossible while the only description of a
setting is a pydantic field in source: the wizard cannot label it, cannot say
which values are allowed, and cannot warn that changing it restarts the server.

So the catalogue is the description, `Settings` remains the enforcement, and a
test asserts the two cover exactly the same keys - the same arrangement as the
permission catalogue in D-020, for the same reason.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from dataclasses import dataclass


#: Where a setting is edited, which is also who is allowed to edit it.
GROUP_HOSPITAL = "hospital"      # identity and print headers: the administrator
GROUP_CLINICAL = "clinical"      # external clinical services: optional
GROUP_DATA = "data"              # retention, archiving, backup: the administrator
GROUP_NETWORK = "network"        # port and discovery: whoever installs the server
GROUP_SECURITY = "security"      # tokens and secrets: advanced only
GROUP_ADVANCED = "advanced"      # diagnostics and internals: advanced only

GROUPS = (
    GROUP_HOSPITAL,
    GROUP_CLINICAL,
    GROUP_DATA,
    GROUP_NETWORK,
    GROUP_SECURITY,
    GROUP_ADVANCED,
)

#: Where the effective value came from, in precedence order.
SOURCE_DEFAULT = "default"
SOURCE_ENV = "env"
SOURCE_DATABASE = "database"


@dataclass(frozen=True)
class SettingSpec:
    """One configurable value."""

    key: str
    group: str
    type: str            # string | integer | boolean | decimal | list | secret
    default: object
    label: str
    description: str
    restart_required: bool = False
    choices: tuple[str, ...] = ()
    #: Bootstrap values are read before the database exists, so they cannot come
    #: from it and are never offered by the wizard's database-backed steps.
    bootstrap: bool = False


def _s(key, group, type_, default, label, description, **kw) -> SettingSpec:
    return SettingSpec(
        key=key,
        group=group,
        type=type_,
        default=default,
        label=label,
        description=description,
        **kw,
    )


SETTINGS: tuple[SettingSpec, ...] = (
    # ---------------------------------------------------------------- hospital
    _s("HOSPITAL_NAME", GROUP_HOSPITAL, "string", "Hospital Homoeopathic Management System",
       "Hospital name", "Printed at the top of every document and report."),
    _s("HOSPITAL_CODE", GROUP_HOSPITAL, "string", "HHMS",
       "Hospital code", "Short code used in identifiers and on the sidebar."),
    _s("TIME_ZONE", GROUP_HOSPITAL, "string", "Asia/Kolkata",
       "Time zone", "Every timestamp the server records is in this zone."),
    _s("DATE_FORMAT", GROUP_HOSPITAL, "string", "%d-%m-%Y",
       "Date format", "How dates appear on screen and on paper."),
    _s("DATETIME_FORMAT", GROUP_HOSPITAL, "string", "%d-%m-%Y %H:%M",
       "Date and time format", "How timestamps appear on screen and on paper."),

    # ---------------------------------------------------------------- clinical
    _s("WHO_ICD11_CLIENT_ID", GROUP_CLINICAL, "string", None,
       "WHO ICD-11 client ID", "Only needed if the hospital uses ICD-11 coding."),
    _s("WHO_ICD11_CLIENT_SECRET", GROUP_CLINICAL, "secret", None,
       "WHO ICD-11 client secret", "Only needed if the hospital uses ICD-11 coding."),
    _s("WHO_ICD11_API_BASE_URL", GROUP_CLINICAL, "string",
       "https://id.who.int/icd", "ICD-11 API address", "Rarely changed."),
    _s("WHO_ICD11_TOKEN_URL", GROUP_CLINICAL, "string",
       "https://icdaccessmanagement.who.int/connect/token", "ICD-11 token address",
       "Rarely changed."),
    _s("WHO_ICD11_RELEASE", GROUP_CLINICAL, "string", "2024-01",
       "ICD-11 release", "Which release of the ICD-11 coding to use."),

    # -------------------------------------------------------------------- data
    _s("LIVE_DATA_YEARS", GROUP_DATA, "integer", 1,
       "Years kept live", "Records newer than this stay in the working database."),
    _s("ONLINE_ARCHIVE_YEARS", GROUP_DATA, "integer", 5,
       "Years kept online", "Older records are archived but still readable."),
    _s("COLD_ARCHIVE_YEARS", GROUP_DATA, "integer", 10,
       "Years before cold storage", "After this, records move to cold storage only."),
    _s("AUTO_MAINTENANCE_ENABLED", GROUP_DATA, "boolean", True,
       "Run maintenance automatically", "Archiving and housekeeping on a timer."),
    _s("AUTO_BACKUP_ENABLED", GROUP_DATA, "boolean", True,
       "Back up automatically", "Nightly database copy."),
    _s("MAINTENANCE_INTERVAL_HOURS", GROUP_DATA, "integer", 24,
       "Maintenance interval (hours)", "How often the heavy maintenance pass runs."),
    _s("REPORT_SCHEDULER_INTERVAL_MINUTES", GROUP_DATA, "integer", 60,
       "Report scheduler interval (minutes)", "How often due scheduled reports are checked."),
    _s("LOG_RETENTION_DAYS", GROUP_DATA, "integer", 30,
       "Log retention (days)", "Server logs older than this are removed."),

    # ----------------------------------------------------------------- network
    _s("SERVER_PORT", GROUP_NETWORK, "integer", 8000,
       "Server port", "Other computers on the LAN reach the server on this port.",
       restart_required=True, bootstrap=True),
    _s("DISCOVERY_ENABLED", GROUP_NETWORK, "boolean", True,
       "Find the server automatically", "Clients discover the server without typing an address.",
       restart_required=True, bootstrap=True),
    _s("DISCOVERY_PORT", GROUP_NETWORK, "integer", 38541,
       "Discovery port", "Used only when automatic discovery is on.",
       restart_required=True, bootstrap=True),
    _s("DISCOVERY_NAME", GROUP_NETWORK, "string", "HHMS",
       "Discovery name", "The name clients show when they find this server.",
       restart_required=True, bootstrap=True),
    _s("BACKEND_CORS_ORIGINS", GROUP_NETWORK, "list", (),
       "Allowed browser origins", "Empty by default: the GUI is served by this server.",
       restart_required=True),

    # ---------------------------------------------------------------- security
    _s("SECRET_KEY", GROUP_SECURITY, "secret", None,
       "Token signing key", "Generated on first run. Changing it signs everyone out.",
       restart_required=True, bootstrap=True),
    _s("JWT_ALGORITHM", GROUP_SECURITY, "string", "HS256",
       "Token algorithm", "Rarely changed; only a matching algorithm is accepted.",
       restart_required=True),
    _s("PERMISSION_ENFORCEMENT", GROUP_SECURITY, "string", "enforce",
       "Permission enforcement", "off, warn or enforce. Never 'off' in a hospital.",
       choices=("off", "warn", "enforce")),
    _s("ACCESS_TOKEN_EXPIRE_MINUTES", GROUP_SECURITY, "integer", 30,
       "Session length (minutes)", "How long a login lasts before it must be repeated."),
    _s("LOGIN_RATE_LIMIT_ATTEMPTS", GROUP_SECURITY, "integer", 10,
       "Login attempts allowed", "Attempts allowed per window before a pause."),
    _s("LOGIN_RATE_LIMIT_WINDOW_SECONDS", GROUP_SECURITY, "integer", 60,
       "Login attempt window (seconds)", "The window those attempts are counted over."),

    # ---------------------------------------------------------------- advanced
    _s("APP_NAME", GROUP_ADVANCED, "string", "Hospital Homoeopathic Management System",
       "Application name", "Shown in the API documentation and logs."),
    _s("APP_SHORT_NAME", GROUP_ADVANCED, "string", "HHMS",
       "Application short name", "Shown in the API documentation."),
    _s("APP_VERSION", GROUP_ADVANCED, "string", "0.0.0",
       "Application version", "Set by the release, not by hand."),
    _s("API_V1_PREFIX", GROUP_ADVANCED, "string", "/api/v1",
       "API prefix", "Changing this breaks every client."),
    _s("ENVIRONMENT", GROUP_ADVANCED, "string", "development",
       "Environment", "development, test or production."),
    _s("DEBUG", GROUP_ADVANCED, "boolean", False,
       "Debug mode", "Never enable in a hospital: it exposes internals."),
    _s("SERVER_HOST", GROUP_ADVANCED, "string", "0.0.0.0",
       "Bind address", "0.0.0.0 accepts LAN connections; 127.0.0.1 does not.",
       restart_required=True),
    _s("DATABASE_URL", GROUP_ADVANCED, "string", None,
       "Database address", "Where the hospital's data lives.",
       restart_required=True, bootstrap=True),
    _s("DATABASE_ECHO", GROUP_ADVANCED, "boolean", False,
       "Log every SQL statement", "Diagnostic only; it is slow."),
    _s("LOG_LEVEL", GROUP_ADVANCED, "string", "INFO",
       "Log level", "DEBUG, INFO, WARNING, ERROR.",
       choices=("DEBUG", "INFO", "WARNING", "ERROR")),
    _s("LOG_DIRECTORY", GROUP_ADVANCED, "string", None,
       "Log directory", "Where server logs are written."),
    _s("LOG_FILE_NAME", GROUP_ADVANCED, "string", "hhms.log",
       "Log file name", "The file inside the log directory."),
    _s("DEFAULT_PAGE_SIZE", GROUP_ADVANCED, "integer", 50,
       "Default page size", "Rows per page when a list does not say."),
    _s("MAX_PAGE_SIZE", GROUP_ADVANCED, "integer", 200,
       "Maximum page size", "The largest page a client may request."),
    _s("ROOT_DIR", GROUP_ADVANCED, "string", None,
       "Application root", "Where the database, logs and uploads live. Derived at runtime."),
)

BY_KEY: dict[str, SettingSpec] = {spec.key: spec for spec in SETTINGS}


def in_group(group: str) -> tuple[SettingSpec, ...]:
    """Every setting in one group, in declaration order."""

    if group not in GROUPS:
        raise KeyError(group)
    return tuple(spec for spec in SETTINGS if spec.group == group)


def editable_in_database() -> tuple[SettingSpec, ...]:
    """Settings the wizard may store in the database.

    Bootstrap values are read before the database is open, so they can only come
    from the environment and are never offered by a database-backed step.
    """

    return tuple(spec for spec in SETTINGS if not spec.bootstrap)


__all__ = [
    "BY_KEY",
    "GROUPS",
    "SETTINGS",
    "SOURCE_DATABASE",
    "SOURCE_DEFAULT",
    "SOURCE_ENV",
    "SettingSpec",
    "editable_in_database",
    "in_group",
]
