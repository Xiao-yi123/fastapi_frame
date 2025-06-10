from typing import List

from pydantic import BaseModel
from sqlalchemy import and_, select

from app.database.curd.mixins.utils_mixin import UtilsMixin


class UpdateMixin(UtilsMixin):
    async def update_by_id(self, id: int, update,**kwargs):
        """
        根据ID更新一条记录。

        :param id: 记录的ID。
        :param update: 更新数据的对象。
        :return: 更新后的记录对象。
        """
        # 检查 `update` 是否有 `dict` 方法
        if isinstance(update, BaseModel):
            update_dict = update.dict(exclude_unset=True)
        elif isinstance(update, dict):
            update_dict = update
        else:
            raise ValueError("create 参数必须是 Pydantic 模型实例 or dict类型")
        filters = []
        if kwargs:
            filters = self.get_filters(self._model,**kwargs)
        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            query = await session.execute(select(self._model).where(and_(self._model.id == id,*filters)))
            result = query.scalars().first()
            if result:
                for key, value in update_dict.items():
                    setattr(result, key, value)
                await session.commit()
        return result

    def update_by_id_sync(self, id: int, update,**kwargs):

        # 检查 `update` 是否有 `dict` 方法
        if isinstance(update, BaseModel):
            update_dict = update.dict(exclude_unset=True)
        elif isinstance(update, dict):
            update_dict = update
        else:
            raise ValueError("create 参数必须是 Pydantic 模型实例 or dict类型")
        filters = [self._model.id == id]

        if kwargs:
            extra_filters = self.get_filters(self._model, **kwargs)
            filters.extend(extra_filters)

        full_filter = and_(*filters)
        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            query = session.query(self._model)  # 创建查询对象
            result = query.filter(full_filter).update(update_dict)  # 使用查询对象的update方法
            session.commit()  # 提交事务
        return result

    async def batch_update_by_ids(self, ids: List[int], update,**kwargs):
        """
        批量更新多条记录。

        :param ids: 记录的ID列表。
        :param update: 更新数据的对象。
        :return: 更新成功的记录数量。
        """
        # 检查 `update` 是否有 `dict` 方法
        if isinstance(update, BaseModel):
            update_dict = update.dict(exclude_unset=True)
        elif isinstance(update, dict):
            update_dict = update
        else:
            raise ValueError("create 参数必须是 Pydantic 模型实例 or dict类型")
        filters = []
        if kwargs:
            filters = self.get_filters(self._model, **kwargs)
        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            query = await session.execute(select(self._model).where(and_(self._model.id.in_(ids),*filters)))
            results = query.scalars().all()
            for result in results:
                for key, value in update_dict.items():
                    setattr(result, key, value)
            await session.commit()
        return len(results)

    def batch_update_by_ids_sync(self, ids: List[int], update,**kwargs):
        filters = [self._model.id.in_(ids)]

        if kwargs:
            extra_filters = self.get_filters(self._model, **kwargs)
            filters.extend(extra_filters)

        full_filter = and_(*filters)
        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            query = session.query(self._model)  # 创建查询对象
            result = query.filter(full_filter).update(update, synchronize_session=False)  # 使用in_方法批量更新
            session.commit()  # 提交事务
        return result
