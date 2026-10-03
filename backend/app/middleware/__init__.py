"""
HHMS Middleware Package
=======================

Centralized exports for HTTP middleware and exception-handler
registration.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from .exception_handler import (
    handle_hhms_exception,
    handle_http_exception,
    handle_unexpected_exception,
    handle_validation_error,
    register_exception_handlers,
)
from .logging import RequestLoggingMiddleware
from .process_time import ProcessTimeMiddleware
from .request_id import RequestIDMiddleware

__all__ = [
    "RequestIDMiddleware",
    "ProcessTimeMiddleware",
    "RequestLoggingMiddleware",
    "register_exception_handlers",
    "handle_hhms_exception",
    "handle_http_exception",
    "handle_unexpected_exception",
    "handle_validation_error",
]