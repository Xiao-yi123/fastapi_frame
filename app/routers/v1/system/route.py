"""
@Package   
@File      route.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
import json

from fastapi import APIRouter, Depends

from app.routers.v1.system import *
from app.types.response import ResponseSuccess
from config.dependency import AuthDepend

from config.settings import appSettings

router = APIRouter(prefix=f'/route', tags=['路由管理'], dependencies=[Depends(AuthDepend.is_authed)])


def filter_children_by_role(item, role_to_check='R_USER'):
    """
    根据指定角色过滤项的子项列表。

    该函数递归地检查项的子项列表，保留那些在'meta'字典中没有指定角色的项。
    如果子项不符合角色要求，则从父项的'children'列表中移除该子项。

    参数:
    - item: 当前正在检查的项，可以包含'children'列表。
    - role_to_check: 用于过滤子项的角色标志。

    返回:
    - 返回过滤后的父项。
    """
    # 检查当前项是否有 'roles' 字段
    if 'meta' in item and 'roles' in item['meta']:
        # 如果 'roles' 字段存在且包含指定角色，则保留该条目
        if not (role_to_check in item['meta']['roles']):
            # 如果不包含指定角色，则从父级的 'children' 列表中删除该条目
            return None

    # 如果存在子项，则递归地检查子项
    if 'children' in item:
        # 过滤子项
        filtered_children = [child for child in item['children'] if
                             filter_children_by_role(child, role_to_check) is not None]
        # 更新 'children' 列表
        item['children'] = filtered_children

    return item


@router.get('/getConstantRoutes', summary='获取路由列表')
async def getConstantRouteFunc():
    file_path = appSettings.public_dir['STATIC_MANAGE'] + '/ConstantRoutes.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        file_data = f.read()
        data = json.loads(file_data)

    return ResponseSuccess(data=data)


@router.get('/getUserRoutes', summary='获取用户路由列表')
async def getUserRouteFunc(auth_user_data=Depends(AuthDepend.is_authed_sql)):
    """
    获取用户路由列表的接口。

    该函数根据用户的权限角色，筛选出用户有权限访问的路由信息。

    参数:
    - auth_user_data: 依赖项，用于获取经过身份验证的用户信息。

    返回值:
    - ResponseSuccess: 包含用户可访问路由列表和默认首页信息的响应对象。
    """
    # 定义用户路由信息文件路径
    file_path = appSettings.public_dir['STATIC_MANAGE'] + '/UserRoutes.json'

    # 读取用户路由信息文件
    with open(file_path, 'r', encoding='utf-8') as f:
        file_data = f.read()
        file_data = json.loads(file_data)

    # 初始化过滤后的路由数据列表
    filtered_data = []
    # 遍历所有路由数据，根据用户角色进行过滤
    for route in file_data:
        filtered_route = filter_children_by_role(route, auth_user_data.role)
        if filtered_route is not None:
            filtered_data.append(filtered_route)

    # 组装最终返回的数据，包含过滤后的路由和默认首页
    data = {
        "routes": filtered_data,
        "home": "home"
    }
    # 返回包含用户可访问路由列表和默认首页信息的响应对象
    return ResponseSuccess(data=data)



__all__ = [
    "router"
]
