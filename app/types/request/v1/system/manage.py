"""
@Package   
@File      manage.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from datetime import datetime
from typing import Union

from fastapi import Query
from pydantic import BaseModel, ConfigDict

from app.types.request import PagingQueryParam


class ManageUserSearchParam(PagingQueryParam):
    role: Union[str] = Query(None, description='角色权限')
    username: Union[str, None] = Query(None, description='用户名')
    nickname: Union[str, None] = Query(None, description='昵称')
    auth_num: Union[int, None] = Query(None, description='权限数量')
    vip_end_date: Union[list, None] = Query(None, description='VIP到期时间')
    status: Union[str, None] = Query(None, description='状态')

    class Config:
        arbitrary_types_allowed = True


class ManageUserCreateParam(BaseModel):
    role: Union[str,None] = Query(None, description='角色权限')
    avatar: Union[str, None] = Query(None, description='头像')
    nickname: Union[str, None] = Query(None, description='昵称')
    auth_num: Union[int] = Query(0, description='权限数量')
    vip_end: Union[datetime] = Query(datetime.now(), description='VIP到期时间')

    model_config = ConfigDict(extra='allow', arbitrary_types_allowed=True)


__all__ = [
    'ManageUserSearchParam',
    'ManageUserCreateParam'
]
# Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjMsImlhdCI6MTcyOTE1MTM4NSwiZXhwIjoxNzI5MjQxMzg1LCJpc3MiOiJ5aXl1bnQiLCJzdWIiOiJ5aXl1bnQiLCJkYXRhIjp7InVzZXJuYW1lIjoiYWRtaW4ifX0.5_q-Aeu6ZUECYvGV2CRyrf1JbB7-kvhkOrCSvxhBLGA