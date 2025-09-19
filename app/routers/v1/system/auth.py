"""
@Package   
@File      auth.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from fastapi import APIRouter, Depends

from app.types.response import ResponseFail, ResponseSuccess
from config.dependency import AuthDepend

from app.utils import jwtGenerator, jwtParse
from app.types.request import LoginParam
from app.database import UserRoleEnum,UserCRUD

router = APIRouter(prefix=f'/auth', tags=['权限认证'])
@router.post('/login', summary='用户登录')
async def loginRouteFunc(login_pm: LoginParam):
    """
    用户登录接口

    该接口用于处理用户登录请求，接收用户登录参数，生成并返回访问令牌和刷新令牌。

    参数:
    - login_pm: 用户登录参数，包含用户身份信息。

    返回值:
    - 返回一个响应对象，包含请求成功信息以及生成的访问令牌和刷新令牌。
    """

    # 初始化用户CURD操作对象
    user_curd = UserCRUD()

    # 获取用户输入的密码
    password = login_pm.password

    # 根据用户名查询用户信息
    sql_data_obj = await user_curd.get_first(username=login_pm.userName)
    # 如果用户不存在，抛出异常
    if not sql_data_obj:
        raise ResponseFail(msg='用户名或密码错误')

    # 比较用户输入的密码与数据库中的加密密码是否一致，并验证令牌
    await user_curd.compare_pwd(password=password, encryption_password=sql_data_obj.password, token=sql_data_obj.token)

    # 构建令牌数据基础信息
    data = {
        "username": login_pm.userName
    }

    # 生成访问令牌
    token = jwtGenerator(data=data, id=sql_data_obj.id)

    # 生成刷新令牌
    refresh_token = jwtGenerator(data=data, id=sql_data_obj.id, is_refresh=True)

    # 登录成功可以写入cookie
    return ResponseSuccess(msg="请求成功", data={
        'token': token,
        'refreshToken': refresh_token,
    })


@router.get('/getUserInfo', summary='获取用户信息', description='''
定义一个名为DGetUserInfo的异步函数，用于获取用户信息
该函数依赖于AuthDepend.is_authed来确保用户已认证
''')
async def getUserInfoRouteFunc(auth_user_data=Depends(AuthDepend.is_authed_sql)):
    """
    获取当前认证用户的信息。

    :param auth_user_data: 认证用户的数据，通过AuthDepend.is_authed依赖注入获取。
    :return: 包含用户信息的成功响应。
    """
    # 准备用户信息字典
    data = {
        # 用户ID，此处简化为静态值，实际应从用户信息中获取
        "userId": auth_user_data.id,
        # 用户名，从认证用户数据中获取，如果不存在，则默认为None
        "userName": auth_user_data.username,
        # 用户角色，此处简化为静态值，实际应从用户信息中获取
        "roles": [
            auth_user_data.role
        ],
        # 用户权限按钮，此处简化为包含所有角色的静态列表，实际应根据用户角色动态生成
        "buttons": [
            UserRoleEnum.SUPER,
            UserRoleEnum.ADMIN,
            UserRoleEnum.NORMALUSER
        ]
    }
    # 返回成功响应，包含用户数据
    return ResponseSuccess(msg="请求成功", data=data)

