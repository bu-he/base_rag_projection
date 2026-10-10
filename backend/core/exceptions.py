# 业务异常基类
class BusinessError(Exception):
    """业务异常基类：可预期的错误都继承它"""
    status_code = 400
    default_message = "业务处理失败"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)

class AuthError(BusinessError):
    status_code = 401
    default_message = "认证失败"

class NotFoundError(BusinessError):
    status_code = 404
    default_message = "资源不存在或无权访问"
