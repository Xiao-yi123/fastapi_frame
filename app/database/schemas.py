from typing import Optional, Union

from pydantic import BaseModel, Field
from datetime import datetime

class UserBaseSchema(BaseModel):
    nickname: Union[str] = Field(default='', max_length=255, description="昵称")
    username: Union[str] = Field(default="")


class UserCreateSchema(UserBaseSchema):
    avatar: Union[str] = 'https://img.picgo.net/2024/06/17/e3b09edfa1dc94996e1b014913bd80612078f88419ebb48c.png'
    login_ip: Union[str] = Field(default='127.0.0.1', description="登录ip")
    role: Union[str] = Field(default='user', max_length=255, description="权限"),
    auth_num: Union[int] = Field(default=0, description="授权数量"),
    vip_end: Union[datetime] = Field(default=None, description="会员到期时间")
    token: Union[str] = Field(..., description='重置密码的token')
    password: Union[str] = Field(..., description="密码")


class UserResetPwdSchema(BaseModel):
    token: Union[str] = Field(..., description='重置密码的token')
    password: Union[str] = Field(..., description='新密码')

class UserUpdateSchema(UserBaseSchema):
    avatar: Union[str] = Field(None, description="头像")
    login_ip: Union[str] = Field(None, description="登录ip")
    role: Union[str] = Field(None, max_length=255, description="权限"),
    auth_num: Union[int] = Field(None, description="授权数量"),
    vip_end: Union[datetime] = Field(None, description="会员到期时间")
    token: Union[str] = Field(None, description='重置密码的token')






__all__ = [
    'UserCreateSchema',
    "UserResetPwdSchema",
    "UserUpdateSchema",
]
