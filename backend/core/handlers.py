from fastapi import Request
from fastapi.responses import JSONResponse
from config.logger import logger
from core.exceptions import BusinessError

def register_exception_handlers(app):
    """main.py 里调用一次：register_exception_handlers(app)"""

    @app.exception_handler(BusinessError)
    async def business_error_handler(request: Request, exc: BusinessError):
        # 业务异常：按异常类型自带的状态码翻译，格式与 FastAPI 默认一致
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        # 兜底 500：完整堆栈进日志，对外只说「内部错误」——不泄露 str(e)
        logger.exception(f"未处理异常 {request.method} {request.url.path}")
        return JSONResponse(status_code=500, content={"detail": "服务器内部错误，请稍后重试"})