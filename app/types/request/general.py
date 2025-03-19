"""
@Package   
@File      general.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from typing import Union

from fastapi import Query
from pydantic import BaseModel,Field


class LoginParam(BaseModel):
    userName: Union[str] = Query(..., description='用户名')
    password: Union[str] = Query(..., description='密码')


class ResetPasswordParam(BaseModel):
    id: Union[int] = Query(0, description='用户ID')
    old_password: Union[str] = Query(..., description='密码')
    new_password: Union[str] = Query(..., description='新密码')


class PagingQueryParam(BaseModel):
    current: Union[int] = Query(default=1, description='当前页')
    size: Union[int] = Query(default=10, description='每页数量')


class BatchDeleteParam(BaseModel):
    ids: Union[list] = Query(None, description='批量删除的ID')


class SetGroupParam(BaseModel):
    group_id: Union[str, None] = Query(None)
    ids: Union[list] = Query(...)


__all__ = [
    'LoginParam',
    'ResetPasswordParam',
    'PagingQueryParam',
    'BatchDeleteParam',
    'SetGroupParam'
]
