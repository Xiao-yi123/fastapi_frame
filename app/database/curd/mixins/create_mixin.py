from pydantic import BaseModel

from app.database.curd.mixins.utils_mixin import UtilsMixin


class CreateMixin(UtilsMixin):
    async def create(self, create):
        """
        创建一条新的记录。

        :param create: 创建数据的对象。
        :return: 新创建的记录对象。
        """
        if isinstance(create, BaseModel):
            create_data = self._model(**create.dict())
        elif isinstance(create, dict):
            create_data = self._model(**create)
        else:
            raise ValueError("create 参数必须是 Pydantic 模型实例 or dict类型")
        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            session.add(create_data)
            await session.commit()
            await session.refresh(create_data)  # 刷新以获取新用户的ID
            return create_data

    def create_sync(self, create):
        if isinstance(create, BaseModel):
            create_data = self._model(**create.dict())
        elif isinstance(create, dict):
            create_data = self._model(**create)
        else:
            raise ValueError("create 参数必须是 Pydantic 模型实例 or dict类型")
        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            session.add(create_data)
            session.commit()
            session.refresh(create_data)  # 刷新以获取新用户的ID
            return create_data