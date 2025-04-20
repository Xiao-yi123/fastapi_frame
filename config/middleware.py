"""
@Package   
@File      middleware.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""

import os

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.utils import is_valid_ip,ResponseFail
from config.settings import appSettings


class TokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exclude_paths: list = []):
        super().__init__(app)
        self.exclude_paths = exclude_paths

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in self.exclude_paths or path.startswith("/static/"):
            return await call_next(request)
            # # 检查路径是否以任何一个需要跳过的前缀开始
            # if any(path.startswith(prefix) for prefix in skip_path_prefixes):
            #     return await call_next(request)

        token = request.headers.get("apifoxToken", "")

        if not token:
            ResponseFail(msg="token is empty")

        if not (token == "XL299LiMEDZ0H5h3A29PxwQXdMJqWyY2"):
            ResponseFail(msg="token is error")

        # Proceed with the request
        response = await call_next(request)
        return response

class IpWhitelistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        allowed_ips = []
        ipfilepath = os.path.join(
            appSettings.public_dir["STATIC_MANAGE"], "allowed_ips.txt"
        )
        with open(ipfilepath, "r") as file:
            ips = file.read().splitlines()
            for ip in ips:
                if is_valid_ip(ip):
                    allowed_ips.append(ip)

        if "X-Forwarded-For" in request.headers:
            client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
        else:
            client_ip = request.client.host
        if allowed_ips != [] and client_ip not in allowed_ips:
            ResponseFail(
                msg=f"Access forbidden: [{client_ip}] IP not allowed"
            )

        # Proceed with the request
        response = await call_next(request)
        return response

class ExceptionHandlingDependencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
            依赖项用于捕获请求处理过程中发生的异常。
            """
        try:
            response = await call_next(request)
        except Exception as e:
            # 记录异常信息
            error_msg = f"An error occurred while processing request: {request.method} {request.url} {str(e)}"

            # 返回自定义的错误响应
            response = JSONResponse(
                status_code=500,
                content={"detail": error_msg},
            )
        return response



def make_middlewares():
    """
    创建并返回一个包含多个中间件的列表。

    这个函数初始化了一个中间件列表，包含了 `IpWhitelistMiddleware`、
    `BackGroundTaskMiddleware` 和 `CORSMiddleware` 中间件。每个中间件都通过
    `Middleware` 类进行初始化，并且 `CORSMiddleware` 中间件配置了额外的参数
    以支持跨域请求。

    Returns:
        list: 一个包含多个中间件的列表。
    """
    # 初始化中间件列表
    middleware = [
        # 添加IP白名单中间件
        Middleware(IpWhitelistMiddleware),
        Middleware(ExceptionHandlingDependencyMiddleware),
        # 添加后台任务中间件
        # 添加跨域资源共享中间件，并配置允许所有来源、凭证、HTTP方法和头
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 允许的来源列表
            allow_credentials=True,  # 是否允许发送凭证 (cookies, authorization headers)
            allow_methods=["*"],  # 允许的 HTTP 方法
            allow_headers=["*"],  # 允许的 HTTP 头
        ),
    ]
    # 返回初始化的中间件列表
    return middleware



__all__ = ["make_middlewares"]
