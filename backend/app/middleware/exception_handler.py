"""
HHMS Exception Handlers
=======================

Centralized FastAPI exception-handler registration.

Application-specific exceptions are converted into consistent JSON
responses while unexpected exceptions are logged without exposing
internal implementation details to clients.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_502_BAD_GATEWAY,
)

from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BusinessRuleException,
    ConfigurationException,
    DatabaseException,
    DuplicateResourceException,
    ExternalServiceException,
    FileStorageException,
    HHMSException,
    ResourceNotFoundException,
    ValidationException,
)


logger = logging.getLogger("HHMS")


def _request_id(request: Request) -> str | None:
    """
    Retrieve the request ID assigned by request middleware.

    Parameters
    ----------
    request : Request
        Current HTTP request.

    Returns
    -------
    str | None
        Request identifier when available.
    """

    return getattr(request.state, "request_id", None)


def _error_response(
    *,
    request: Request,
    status_code: int,
    message: str,
    error_code: str,
    details: Any | None = None,
) -> JSONResponse:
    """
    Build a standardized HHMS error response.

    Parameters
    ----------
    request : Request
        Current HTTP request.

    status_code : int
        HTTP response status code.

    message : str
        Client-safe error message.

    error_code : str
        Machine-readable application error code.

    details : Any | None
        Optional client-safe validation or error details.

    Returns
    -------
    JSONResponse
        Standardized JSON error response.
    """

    error: dict[str, Any] = {
        "code": error_code,
        "message": message,
    }

    request_id = _request_id(request)

    if request_id is not None:
        error["request_id"] = request_id

    if details is not None:
        error["details"] = details

    return JSONResponse(
        status_code=status_code,
        content={"error": error},
    )


async def handle_hhms_exception(
    request: Request,
    exc: HHMSException,
) -> JSONResponse:
    """
    Handle application-specific HHMS exceptions.

    Parameters
    ----------
    request : Request
        Current HTTP request.

    exc : HHMSException
        Application exception.

    Returns
    -------
    JSONResponse
        Standardized application error response.
    """

    status_mapping: tuple[
        tuple[type[HHMSException], int, str],
        ...,
    ] = (
        (
            ValidationException,
            HTTP_400_BAD_REQUEST,
            "VALIDATION_ERROR",
        ),
        (
            AuthenticationException,
            HTTP_401_UNAUTHORIZED,
            "AUTHENTICATION_ERROR",
        ),
        (
            AuthorizationException,
            HTTP_403_FORBIDDEN,
            "AUTHORIZATION_ERROR",
        ),
        (
            ResourceNotFoundException,
            HTTP_404_NOT_FOUND,
            "RESOURCE_NOT_FOUND",
        ),
        (
            DuplicateResourceException,
            HTTP_409_CONFLICT,
            "DUPLICATE_RESOURCE",
        ),
        (
            BusinessRuleException,
            HTTP_422_UNPROCESSABLE_ENTITY,
            "BUSINESS_RULE_VIOLATION",
        ),
        (
            ConfigurationException,
            HTTP_500_INTERNAL_SERVER_ERROR,
            "CONFIGURATION_ERROR",
        ),
        (
            DatabaseException,
            HTTP_500_INTERNAL_SERVER_ERROR,
            "DATABASE_ERROR",
        ),
        (
            FileStorageException,
            HTTP_500_INTERNAL_SERVER_ERROR,
            "FILE_STORAGE_ERROR",
        ),
        (
            ExternalServiceException,
            HTTP_502_BAD_GATEWAY,
            "EXTERNAL_SERVICE_ERROR",
        ),
    )

    status_code = HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "APPLICATION_ERROR"

    for exception_type, mapped_status, mapped_code in status_mapping:
        if isinstance(exc, exception_type):
            status_code = mapped_status
            error_code = mapped_code
            break

    if status_code >= HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(
            "Application exception: %s",
            exc,
            exc_info=True,
            extra={
                "request_id": _request_id(request),
            },
        )

    return _error_response(
        request=request,
        status_code=status_code,
        message=exc.message,
        error_code=error_code,
    )


async def handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle FastAPI request-validation errors.

    Parameters
    ----------
    request : Request
        Current HTTP request.

    exc : RequestValidationError
        FastAPI validation exception.

    Returns
    -------
    JSONResponse
        Standardized validation error response.
    """

    details = [
        {
            "location": list(error.get("loc", [])),
            "message": error.get(
                "msg",
                "Invalid value.",
            ),
            "type": error.get(
                "type",
                "validation_error",
            ),
        }
        for error in exc.errors()
    ]

    return _error_response(
        request=request,
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        message="Request validation failed.",
        error_code="REQUEST_VALIDATION_ERROR",
        details=details,
    )


async def handle_http_exception(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle framework-level HTTP exceptions.

    Parameters
    ----------
    request : Request
        Current HTTP request.

    exc : StarletteHTTPException
        Framework HTTP exception.

    Returns
    -------
    JSONResponse
        Standardized HTTP error response.
    """

    detail = exc.detail

    if isinstance(detail, str):
        message = detail
    else:
        message = "HTTP request failed."

    return _error_response(
        request=request,
        status_code=exc.status_code,
        message=message,
        error_code="HTTP_ERROR",
    )


async def handle_unexpected_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected application exceptions.

    Internal exception details are logged but never exposed
    through the client response.

    Parameters
    ----------
    request : Request
        Current HTTP request.

    exc : Exception
        Unexpected exception.

    Returns
    -------
    JSONResponse
        Generic internal-server-error response.
    """

    logger.error(
        "Unhandled application exception",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={
            "request_id": _request_id(request),
        },
    )

    return _error_response(
        request=request,
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        message="An internal server error occurred.",
        error_code="INTERNAL_SERVER_ERROR",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all HHMS exception handlers on a FastAPI application.

    Parameters
    ----------
    app : FastAPI
        FastAPI application instance.
    """

    app.add_exception_handler(
        HHMSException,
        handle_hhms_exception,
    )

    app.add_exception_handler(
        RequestValidationError,
        handle_validation_error,
    )

    app.add_exception_handler(
        StarletteHTTPException,
        handle_http_exception,
    )

    app.add_exception_handler(
        Exception,
        handle_unexpected_exception,
    )


__all__ = [
    "handle_hhms_exception",
    "handle_http_exception",
    "handle_unexpected_exception",
    "handle_validation_error",
    "register_exception_handlers",
]