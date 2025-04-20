"""
@Package   
@File      http_resp.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi import status, HTTPException


# ---------------------- 定义模型 ----------------------
class Additional(BaseModel):
    """额外信息"""
    time: str
    trace_id: str


class HttpResponse(BaseModel):
    """http统一响应"""
    code: int = Field(default=200)  # 响应码
    msg: str = Field(default="处理成功")  # 响应信息


def ResponseSuccess(data: Any, code: str = "200", msg: str = "Success", success: bool = True, **dis):
    """成功响应"""
    try:
        code = int(code)
    except:
        pass
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'code': code ,
            'msg': msg,
            'data': data,
            'success': success

        },
        **dis
    )

def ResponseFail(msg: str = "Some error message", code: int = 1000):
    """响应失败"""
    currentTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raise HTTPException(status_code=code, detail=msg)
    # return JSONResponse(
    #         status_code=code,
    #         content={
    #             'code': code,
    #             'msg': msg,
    #         },
    #     )


__all__ = [
    "ResponseSuccess",
    "ResponseFail",
]
