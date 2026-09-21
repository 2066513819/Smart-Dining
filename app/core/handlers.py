"""
统一异常处理器
将各种异常转换为标准化的API响应
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from typing import Union

from app.core.exceptions import (
    BaseAppException,
    BusinessException,
    ResourceNotFoundException,
    AuthenticationException,
    AuthorizationException,
    ValidationException,
    ExternalServiceException,
    DatabaseException
)

logger = logging.getLogger(__name__)


async def base_app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """处理自定义应用异常"""
    logger.warning(
        f"应用异常: {exc.error_code} - {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": getattr(exc, 'details', None)
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求验证异常"""
    logger.warning(
        f"请求验证失败: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )

    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求数据验证失败",
                "details": errors
            }
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """处理数据库异常"""
    logger.error(
        f"数据库异常: {type(exc).__name__}: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "数据库操作失败，请稍后重试"
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理未捕获的通用异常"""
    logger.error(
        f"未处理的异常: {type(exc).__name__}: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试"
            }
        }
    )


def register_exception_handlers(app):
    """注册所有异常处理器"""
    app.add_exception_handler(BaseAppException, base_app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("异常处理器注册完成")
