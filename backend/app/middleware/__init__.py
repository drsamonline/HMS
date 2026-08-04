"""Middleware package for HHMS backend application.

This package provides framework-level middleware components that:
- Handle cross-cutting concerns
- Implement observability patterns
- Manage request/response lifecycle
- Enforce security policies

All middleware components are designed to be:
- Framework-agnostic where possible
- Independently testable
- Configurable through dependency injection
- Compliant with clean architecture principles
"""

from .exception_handler import ExceptionHandlerMiddleware
from .logging import RequestLoggingMiddleware
from .request_id import RequestIDMiddleware
from .process_time import ProcessTimeMiddleware

__all__ = [
    "ExceptionHandlerMiddleware",
    "RequestLoggingMiddleware",
    "RequestIDMiddleware",
    "ProcessTimeMiddleware",
]