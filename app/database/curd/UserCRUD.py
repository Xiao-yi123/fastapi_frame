from app.database import UserModel, UserRoleEnum
from app.database.curd.BaseCRUD import BaseCRUD
from app.utils.encryption import hashlib_sha256


class UserCRUD(BaseCRUD):
    def __init__(self,connect_str: str = None):
        super().__init__(connect_str)
        self._model = UserModel

    async def verify_user_unique_by_username(self, username: str):
        """
        验证用户名是否唯一。
        """
        from app.types.response import ResponseFail

        if await self.get_first(username=username):
            ResponseFail(msg="用户已存在")

    @staticmethod
    async def compare_pwd(password: str, encryption_password: str, token: str):
        """
        比较密码是否正确
        :param password:  新密码
        :param encryption_password: 加密后的密码
        :param token:  跟新密码一起加密的token
        :return:
        """
        from app.types.response import ResponseFail

        if encryption_password != hashlib_sha256(password + token):
            ResponseFail(msg="用户名或密码错误")

    @staticmethod
    async def verify_role_operation(role_value: str, operation_value: str):
        """
        验证用户角色是否能执行该操作。
        """
        from app.types.response import ResponseFail

        match operation_value:
            case "CreateUser":
                if role_value not in {UserRoleEnum.SUPER.value, UserRoleEnum.ADMIN.value}:
                    ResponseFail(msg="用户角色没有权限")
            case "UpdateUser":
                if role_value != UserRoleEnum.SUPER.value:
                    ResponseFail(msg="不能修改超级管理员权限")
            case "DeleteUser":
                if role_value != UserRoleEnum.SUPER.value:
                    ResponseFail(msg="没有权限执行删除操作")
            case _:
                ResponseFail(msg='参数错误')


__all__ = ['UserCRUD']

