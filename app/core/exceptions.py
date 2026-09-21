"""
统一异常处理模块
定义自定义异常类和异常处理器
"""

from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """应用基础异常类"""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class BusinessException(BaseAppException):
    """业务逻辑异常"""

    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, error_code=error_code)


class ResourceNotFoundException(BaseAppException):
    """资源未找到异常"""

    def __init__(self, resource_name: str = "资源"):
        super().__init__(
            message=f"{resource_name}不存在",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND"
        )


class AuthenticationException(BaseAppException):
    """认证异常"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED"
        )


class AuthorizationException(BaseAppException):
    """授权异常"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_FAILED"
        )


class ValidationException(BaseAppException):
    """数据验证异常"""
    
    def __init__(self, message: str = "数据验证失败", field: str = None):
        error_msg = message
        if field:
            error_msg = f"字段 '{field}': {message}"
        super().__init__(
            message=error_msg,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR"
        )


class RecommendationException(BaseAppException):
    """推荐异常"""
    
    def __init__(self, message: str = "推荐失败", error_type: str = "recommendation_error"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=f"RECOMMENDATION_{error_type.upper()}"
        )


class ExternalServiceException(BaseAppException):
    """外部服务异常"""
    
    def __init__(self, service_name: str, message: str = "服务不可用"):
        super().__init__(
            message=f"{service_name}: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=f"EXTERNAL_SERVICE_{service_name.upper()}"
        )

    def __init__(self, message: str = "无权限访问该资源"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_FAILED"
        )


class ValidationException(BaseAppException):
    """数据验证异常"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.details = details
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR"
        )


class ExternalServiceException(BaseAppException):
    """外部服务调用异常"""

    def __init__(self, service_name: str, message: str = "外部服务调用失败"):
        super().__init__(
            message=f"{service_name}: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR"
        )


class DatabaseException(BaseAppException):
    """数据库操作异常"""

    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR"
        )
