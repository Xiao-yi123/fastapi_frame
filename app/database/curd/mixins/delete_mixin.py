from typing import List

from sqlalchemy import and_, select

from app.database.curd.mixins.utils_mixin import UtilsMixin


class DeleteMixin(UtilsMixin):
    async def delete_by_id(self, id: int,**kwargs):
        """
        根据ID删除一条记录。

        :param id: 记录的ID。
        :return: 删除的记录对象。
        """
        filters = []
        if kwargs:
            filters = self.get_filters(self._model, **kwargs)
        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            query = await session.execute(select(self._model).where(and_(self._model.id == id,*filters)))
            result = query.scalars().first()
            if result:
                await session.delete(result)
                await session.commit()
        return result

    def delete_by_id_sync(self, id: int,**kwargs):
        filters = [self._model.id==id]

        if kwargs:
            extra_filters = self.get_filters(self._model, **kwargs)
            filters.extend(extra_filters)

        full_filter = and_(*filters)
        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            query = session.query(self._model)
            result = query.filter(full_filter).delete()
            session.commit()
        return result

    async def batch_delete(self, ids: List[int],**kwargs):
        """
        批量删除多条记录。

        :param ids: 记录的ID列表。
        :return: 删除成功的记录数量。
        """
        filters = []
        if kwargs:
            filters = self.get_filters(self._model, **kwargs)

        # 异步获取数据库会话
        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            # 执行异步查询，根据用户ID和记录ID列表筛选出需要删除的记录
            query = await session.execute(
                select(self._model).where(and_(self._model.id.in_(ids),*filters))
            )
            # 获取查询结果列表
            results = query.scalars().all()
            # 遍历查询结果，异步删除每条记录
            for result in results:
                await session.delete(result)
            # 提交事务，确保更改生效
            await session.commit()
        # 返回删除成功的记录数量
        return len(results)

    def batch_delete_sync(self, ids: list,**kwargs):
        if not ids:
            return 0  # 防止误删全表

        filters = [self._model.id.in_(ids)]

        if kwargs:
            extra_filters = self.get_filters(self._model, **kwargs)
            filters.extend(extra_filters)

        full_filter = and_(*filters)

        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            result = session.query(self._model).filter(full_filter).delete(synchronize_session=False)
            session.commit()
            return result