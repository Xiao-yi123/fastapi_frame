"""
@Package   
@File      exceptions.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from fastapi import status, FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from tortoise.exceptions import DoesNotExist, IntegrityError
from starlette.exceptions import HTTPException



async def httpExceptionHandler(request, exc: HTTPException) -> JSONResponse:
    """自定义处理HTTPException"""
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        # 处理404错误
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                'code': int(exc.status_code),
                'msg': "接口路由不存在~",
            }
        )
    elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        # 处理405错误
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                'code': int(exc.status_code),
                'msg':"请求方式错误，请查看文档确认~",
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                'code': int(exc.status_code),
                'msg': exc.detail,
            },
        )


class SettingNotFound(Exception):
    pass


async def DoesNotExistHandle(req: Request, exc: DoesNotExist) -> JSONResponse:
    content = dict(
        code=404,
        msg=f"Object has not found, exc: {exc}, query_params: {req.query_params}",
    )
    return JSONResponse(content=content, status_code=404)


async def IntegrityHandle(_: Request, exc: IntegrityError) -> JSONResponse:
    content = dict(
        code=500,
        msg=f"IntegrityError，{exc}",
    )
    return JSONResponse(content=content, status_code=500)

async def RequestValidationHandle(_: Request, exc: RequestValidationError) -> JSONResponse:
    content = dict(code=422, msg=f"RequestValidationError, {exc}")
    return JSONResponse(content=content, status_code=422)


async def ResponseValidationHandle(_: Request, exc: ResponseValidationError) -> JSONResponse:
    content = dict(code=500, msg=f"ResponseValidationError, {exc}")
    return JSONResponse(content=content, status_code=500)


def registerCustomErrorHandle(server: FastAPI):
    """ 统一注册自定义错误处理器"""
    server.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    server.add_exception_handler(HTTPException, httpExceptionHandler)
    server.add_exception_handler(IntegrityError, IntegrityHandle)
    server.add_exception_handler(RequestValidationError, RequestValidationHandle)
    server.add_exception_handler(ResponseValidationError, ResponseValidationHandle)

__all__ = [
    'registerCustomErrorHandle',
]