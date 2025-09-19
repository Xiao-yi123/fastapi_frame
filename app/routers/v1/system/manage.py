"""
@Package   
@File      manage.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from fastapi import Depends, APIRouter

from app.database import UserCRUD, UserCreateSchema, UserRoleEnum,UserResetPwdSchema
from app.types.response import ResponseSuccess, ResponseFail
from config.dependency import AuthDepend
from app.utils import generate_unid1_token, hashlib_sha256, get_public_ip
from app.types.request import ResetPasswordParam, ManageUserCreateParam, BatchDeleteParam

router = APIRouter(prefix=f'/systemManage', tags=['系统管理'], dependencies=[Depends(AuthDepend.is_authed)])

user_curd = UserCRUD()

@router.get('/getCompleteUserInfo', summary='获取完整的用户信息')
async def getCompleteUserInfoRouteFunc(auth_user_data=Depends(AuthDepend.is_authed_sql)):
    """
    获取完整的用户信息

    通过用户ID查询用户信息，如果用户不存在，则返回失败响应；
    如果用户存在，则返回成功响应，包含用户信息。

    参数:
    - request: Request对象，包含状态和用户ID

    返回:
    - ResponseFail对象，如果用户不存在，包含错误信息
    - ResponseSuccess对象，如果用户存在，包含成功消息和用户信息
    """

    data = user_curd.serialization([auth_user_data], exclude=['password', 'token'])
    # 返回成功响应，包含用户信息
    return ResponseSuccess(msg="请求成功", data=data[0])


@router.post("/createUser", summary="创建用户")
async def createUserRouteFunc(param: ManageUserCreateParam, auth_user_info=Depends(AuthDepend.is_authed_sql)):
    """
    创建用户
    默认密码 ： 用户名 + 123456
    """
    # 验证当前用户是否有权限执行创建用户操作
    await user_curd.verify_role_operation(auth_user_info.role, "CreateUser")

    # 获取用户数据，根据传入的用户名参数
    user_data = await user_curd.get_first(username=param.username)
    # 如果用户数据存在，说明用户名已被占用
    if user_data:
        # 返回失败响应，提示用户名已存在
        ResponseFail(msg='用户名已存在')

    # 生成唯一token
    token = generate_unid1_token()
    # 生成默认密码，并进行SHA256加密
    password = hashlib_sha256(param.username + '123456' + token)

    # 准备创建用户所需的数据
    create = UserCreateSchema(
        token=token,
        login_ip=await get_public_ip(),  # 获取当前用户的登录IP
        password=password,
        **param.dict(),  # 将创建用户参数转换为字典并解包
    )

    # 执行创建用户操作
    result = await user_curd.create(create=create)
    result_json = user_curd.serialization([result], exclude=['password', 'token'])
    # 返回成功响应，包含创建的用户信息
    return ResponseSuccess(msg="请求成功", data=result_json[0])


@router.post("/editUser/{user_id}", summary="更新用户")
async def editUserRouteFunc(user_id: int, param: ManageUserCreateParam, auth_user_info=Depends(AuthDepend.is_authed_sql)):
    """
    更新用户信息的接口方法。

    参数:
    - request: 请求对象，包含请求的所有数据。
    - user_id: int，需要更新的用户ID，通过路径参数获取。
    - param: ManageUserCreateParam，更新用户信息所需的参数，遵循请求体传递。

    返回:
    - 如果用户更新成功，返回ResponseSuccess对象，包含成功消息"编辑成功"。
    - 如果用户更新失败，返回ResponseFail对象，包含失败消息"编辑失败"。
    """
    # 验证当前用户是否有权限执行创建用户操作
    await user_curd.verify_role_operation(auth_user_info.role, "UpdateUser")
    # 验证end
    # 执行用户信息更新操作
    result = await user_curd.update_by_id(id=user_id, update=param)
    if result:
        # 如果更新成功，返回成功响应
        return ResponseSuccess(msg="编辑成功", data=[])
    else:
        # 如果更新失败，返回失败响应
        ResponseFail(msg="编辑失败")


@router.delete("/deleteUser/{user_id}", summary="删除用户")
async def deleteUserRouteFunc(user_id: int, auth_user_info=Depends(AuthDepend.is_authed_sql)):
    # 验证当前用户的角色是否有权进行删除操作
    await user_curd.verify_role_operation(auth_user_info.role, "DeleteUser")
    # 验证end

    # 执行删除操作，根据结果返回成功或失败的响应
    result = await user_curd.delete_by_id(id=user_id)
    if result:
        return ResponseSuccess(msg="删除成功", data=[])
    else:
        ResponseFail(msg="删除失败")


@router.delete('/delete/batch', summary='批量删除')
async def batchDeleteRouteFunc(ids: BatchDeleteParam, auth_user_info=Depends(AuthDepend.is_authed_sql)):
    # 从待删除列表中移除当前操作用户ID，确保不会删除自己的账号
    ids = [i for i in ids.ids if i != auth_user_info.id]

    # 验证当前用户的角色是否有权进行删除操作
    await user_curd.verify_role_operation(auth_user_info.role, "DeleteUser")
    # 验证end

    # 执行批量删除操作
    result = await user_curd.batch_delete(ids=ids)

    # 根据删除操作的结果返回相应信息
    if result:
        # 删除成功，返回成功信息
        return ResponseSuccess(msg="删除成功", data=[])
    else:
        # 删除失败，返回失败信息
        ResponseFail(msg="删除失败")


@router.put('/resetPassword', summary="重置密码")
async def resetPasswordRouteFunc(param: ResetPasswordParam, auth_user_info=Depends(AuthDepend.is_authed_sql)):
    # 如果有指定的用户ID，进行旧密码验证
    if not param.id:
        # 比较输入的旧密码和数据库中的加密密码是否匹配
        await user_curd.compare_pwd(password=param.old_password, encryption_password=auth_user_info.password,
                                    token=auth_user_info.token)

    # 如果尝试修改超级管理员的密码，返回失败响应
    if (auth_user_info.role == UserRoleEnum.SUPER.value) and (param.id == auth_user_info.id):
        ResponseFail(msg="不能修改超级管理员密码")

    # 根据角色获取用户信息
    if (auth_user_info.role == UserRoleEnum.SUPER.value) or (auth_user_info.role == UserRoleEnum.ADMIN.value):
        user_info = await user_curd.get_first(id=param.id)
    # 验证阶段结束

    # 生成重置密码所需的唯一token
    token = generate_unid1_token()
    # 创建重置密码的数据对象
    data = UserResetPwdSchema(
        token=token,
        password=hashlib_sha256(param.new_password + token)
    )

    # 更新用户密码
    update_num = await user_curd.update_by_id(user_info.id, data)
    # 如果更新成功，返回成功响应
    if update_num:
        return ResponseSuccess(msg="重置成功", data=[])
    else:
        # 如果更新失败，返回失败响应
        ResponseFail(msg="重置失败")


__all__ = [
    "router"
]
