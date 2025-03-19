"""
@Package   
@File      dependency.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from app.database import UserCRUD
from app.types.response import ResponseFail
from app.utils import jwtParse
from fastapi import Header

class AuthDepend:
    @classmethod
    async def is_authed(cls, apifoxToken: str = Header(..., description="token验证")):
        """
        验证用户是否已授权。

        此方法接收一个APIFox令牌（通过Header参数传递），并验证该令牌以确定用户是否已授权。
        验证过程包括解析令牌、检查令牌状态以及返回相应的验证结果。

        参数:
        - apifoxToken (str): 通过Header传递的APIFox令牌，格式为"Bearer {token}"。

        返回:
        - 如果令牌有效，返回状态和用户数据。
        - 如果令牌无效，返回错误信息。
        """
        try:
            # 移除令牌前缀"Bearer "，以便于解析
            token = apifoxToken.replace("Bearer ", "")

            # 解析JWT令牌数据
            jwt_data = jwtParse(token)
            # 检查JWT令牌的状态
            status, user_data = jwt_data.get("status", False), jwt_data.get("data", "error")
            if not status:
                # 如果令牌无效，返回错误信息
                ResponseFail(msg=user_data)
            else:
                return status,user_data
        except Exception as e:
            # 捕获并处理可能的异常
            ResponseFail(msg=f"验证失败: {str(e)}")
    @classmethod
    async def is_authed_sql(cls, apifoxToken: str = Header(..., description="token验证")):
        """
        验证用户令牌并检查用户数据库中是否存在该用户。

        :param apifoxToken: 用户的令牌，用于验证用户身份。
        :return: 用户信息，如果用户存在且令牌有效。否则返回错误信息。
        """
        try:
            # 验证用户令牌
            status, user_data = await AuthDepend.is_authed(apifoxToken)
            if status:
                # 如果令牌有效，提取用户名
                username = user_data.get("data", {}).get("username")
                # 初始化用户增删改查对象
                user_curd = UserCRUD()
                # 查询数据库中是否存在该用户
                sql_user = await user_curd.get_first(username=username)
                if not sql_user:
                    # 如果用户不存在，返回错误信息
                    ResponseFail(msg="用户不存在")
                else:
                    # 如果用户存在，返回用户信息
                    return sql_user
            else:
                # 如果令牌无效，返回错误信息
                ResponseFail(msg=user_data)
        except Exception as e:
            # 捕获并处理可能的异常
            ResponseFail(msg=f"验证失败: {str(e)}")


__all__ = [
    "AuthDepend",
]
