import asyncio
import importlib
from typing import Optional, List, Dict, Any

from sqlalchemy import and_, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import joinedload, subqueryload

from app.database.curd.mixins.utils_mixin import UtilsMixin


class ReadMixin(UtilsMixin):


    async def get_first(self,model_field: Optional[List[str]] = None, **kwargs):
        """
        根据关键字参数获取第一条符合条件的记录。

        :param kwargs: 查询条件的键值对。
        :return: 符合条件的第一条记录。
        """
        filters = self.get_filters(self._model, **kwargs)
        if filters:
            return await self._execute_query(filters, select(*self.build_query(model_field)).where(and_(*filters)), first=True)

    def get_first_sync(self, model_field: Optional[List[str]] = None,  **kwargs):
        """
        根据指定的模型字段和连接字段获取数据库中的第一条记录。

        参数:
        - model_field: 需要查询的模型字段。
        - join_fields: 用于连接的字段列表。
        - **kwargs: 可变关键字参数，用于过滤查询结果。

        返回:
        - 返回查询结果中的第一条记录，如果没有结果则返回None。
        """
        # 获取过滤条件
        filters = self.get_filters(self._model, **kwargs)
        if filters:
            # 使用数据库会话来构建查询
            with self.getDatabaseSession(connect_str=self.connect_str) as session:
                # 构建查询对象
                query = session.query(*self.build_query(model_field))
                # 应用过滤条件并获取第一条记录
                result = query.filter(and_(*filters)).first()
                return result


    async def get_list(self,model_field: Optional[List[str]] = None, **kwargs):
        """
        根据关键字参数获取符合条件的所有记录。

        :param kwargs: 查询条件的键值对。
        :return: 符合条件的所有记录列表。
        """
        filters = self.get_filters(self._model, **kwargs)

        if filters:
            return await self._execute_query(filters, select(*self.build_query(model_field)).where(and_(*filters)))
        else:
            return await self._execute_query(filters, select(*self.build_query(model_field)).where())

    def get_list_sync(self, model_field: Optional[List[str]] = None, **kwargs):
        """
        根据给定的模型字段和连接字段，同步获取列表数据。

        参数:
        - model_field (Optional[List[str]]): 模型字段列表，用于指定需要查询的字段。
        - join_fields (Optional[Dict[str, List[str]]]): 连接字段字典，用于指定需要连接查询的字段。
        - **kwargs: 其他关键字参数，用于构建查询过滤条件。

        返回:
        - result: 查询结果列表。
        """
        # 获取查询过滤条件
        filters = self.get_filters(self._model, **kwargs)

        if filters:
            # 如果存在过滤条件，则使用指定的模型字段和连接字段进行查询
            with self.getDatabaseSession(connect_str=self.connect_str) as session:
                query = session.query(*self.build_query(model_field))
                try:
                    # 执行查询并获取所有结果
                    result = query.filter(and_(*filters)).all()
                except Exception as e:
                    # 如果发生异常，返回错误信息
                    raise Exception(f"SQL GET ERROR:{str(e)}")
                return result
        else:
            # 如果不存在过滤条件，则查询整个模型
            with self.getDatabaseSession(connect_str=self.connect_str) as session:
                query = session.query(*self.build_query(model_field))
                try:
                    # 执行查询并获取所有结果
                    result = query.filter().all()
                except Exception as e:
                    # 如果发生异常，返回错误信息
                    raise Exception(f"SQL GET ERROR:{str(e)}")
                return result

    async def get_random(self, pram_num: int = 1,model_field: Optional[List[str]] = None,  **kwargs):
        """
        根据给定的过滤条件随机返回一条记录。

        :param kwargs: 查询条件的键值对。
        :return: 随机选取的一条记录。
        """
        filters = self.get_filters(self._model, **kwargs)

        # 使用SQLAlchemy的func.rand()函数来进行随机排序
        query = select(*self.build_query(model_field)).where(and_(*filters)).order_by(func.random()).limit(pram_num)

        result = await self._execute_query([], query)

        # 假设 _execute_query 返回的是一个结果集
        if result:
            return result
        else:
            return None  # 如果没有找到任何记录，则返回 None

    def get_random_sync(self, pram_num: int = 1, model_field: Optional[List[str]] = None,  **kwargs):
        """
        根据给定的参数获取随机数据记录。

        参数:
        - pram_num: int, 默认为1，指定要获取的随机记录的数量。
        - model_field: Optional[List[str]], 可选参数，指定需要查询的模型字段列表。
        - **kwargs: 其他可变关键字参数，用于构建查询过滤条件。

        返回:
        - result: 查询结果，包含根据条件获取的随机记录。
        """
        # 构建查询过滤条件
        filters = self.get_filters(self._model, **kwargs)

        # 使用上下管理器确保数据库会话的安全开启和关闭
        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            # 使用SQLAlchemy的func.rand()函数来进行随机排序
            query = session.query(*self.build_query(model_field)).where(and_(*filters)).order_by(func.random()).limit(pram_num)

            try:
                # 执行查询并获取所有结果
                result = query.all()
            except Exception as e:
                # 如果发生异常，返回错误信息
                raise Exception(f"SQL GET ERROR:{str(e)}")
            return result


    async def get_count(self, **kwargs):
        """
        根据关键字参数获取符合条件的记录总数。

        :param kwargs: 查询条件的键值对。
        :return: 符合条件的记录总数。
        """
        filters = self.get_filters(self._model, **kwargs)

        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            count_query = await session.execute(
                select(func.count()).select_from(self._model).where(and_(*filters))
            )
            return count_query.scalar()

    def get_count_sync(self, **kwargs):
        """
        根据关键字参数获取符合条件的记录总数。

        :param kwargs: 查询条件的键值对。
        :return: 符合条件的记录总数。
        """
        filters = self.get_filters(self._model, **kwargs)

        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            count_query = session.query(func.count()).select_from(self._model).where(and_(*filters))
            return count_query.scalar()

    async def get_list_page(self, current: int = 1, size: int = 10, **kwargs):
        """
        根据关键字参数获取分页后的记录列表。

        :param current: 当前页数，默认为1。
        :param size: 每页记录数，默认为10。
        :param kwargs: 查询条件的键值对。
        :return: 分页后的记录列表。
        """
        filters = self.get_filters(self._model, **kwargs)

        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            query = await session.execute(
                select(self._model).where(and_(*filters)).offset((current - 1) * size).limit(size)
            )
            return query.scalars().all()

    def get_list_page_sync(self, current: int = 1, size: int = 10, model_field: Optional[List[str]] = None,  **kwargs):
        """
        根据当前页码和页面大小同步获取列表页面数据。

        :param current: 当前页码，默认为1。
        :param size: 页面大小，默认为10。
        :param model_field: 模型字段列表，用于查询。
        :param kwargs: 其他参数，用于过滤查询结果。
        :return: 查询结果列表。
        """
        # 获取过滤条件
        filters = self.get_filters(self._model, **kwargs)

        # 使用上下文管理器获取数据库会话
        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            # 执行查询，应用过滤条件，分页并获取结果
            result = session.query(*self.build_query(model_field)).filter(and_(*filters)).offset((current - 1) * size).limit(size).all()

        # 返回查询结果
        return result


    def join_query(self, current: int = -1, size: int = 0, prams: Optional[Dict[str, Any]] = None,
                   other_params: Optional[List["CRUDJoinParams"]] = None,
                   model_field: Optional[List[str]] = None):
        """
        执行一个关联查询。

        :param current: 当前页码，默认为-1。
        :param size: 每页大小，默认为0。
        :param prams: 主查询的过滤条件参数字典。
        :param other_params: 关联查询参数列表。
        :param model_field: 模型字段列表，用于查询。
        :param join_fields: 关联字段字典，包含关联查询的字段。

        :return: 查询结果和总记录数的字典。
        """
        prams = prams or {}
        other_params = other_params or []

        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            all_prams = []
            query_obj = session.query(*self.build_query(model_field,other_params))
            # 处理主查询的过滤条件
            if prams:
                all_prams.extend(self.get_filters(self._model, **prams))

            # 处理关联查询
            for join_params in other_params:
                if not isinstance(join_params, CRUDJoinParams):
                    continue
                try:
                    module = importlib.import_module("app.database")
                    model_class = getattr(module, join_params.model)
                except (ImportError, AttributeError) as e:
                    raise ValueError(f"无法加载模型 {join_params.model}: {e}")

                if join_params.is_outerjoin:
                    query_obj = query_obj.outerjoin(model_class)
                if join_params.is_join:
                    query_obj = query_obj.join(model_class)
                if join_params.is_subqueryload:
                    query_obj = query_obj.options(subqueryload(getattr(self._model, join_params.relationship_name)))
                if join_params.is_joinedload:
                    query_obj = query_obj.options(joinedload(getattr(self._model, join_params.relationship_name)))

                if join_params.params:
                    all_prams.extend(self.get_filters(model_class, **join_params.params))

            # 构建最终查询
            if all_prams:
                query_obj = query_obj.filter(and_(*all_prams))

            num = query_obj.count()

            # 分页处理
            if current >= 0 and size > 0:
                current = max(1, current)
                size = max(1, size)
                query_obj = query_obj.offset((current - 1) * size).limit(size)

            data = query_obj.all()

            return {
                "data": data,
                "total": num,
            }


    async def _execute_query(self, filters, query, first=False):
        """
        执行查询，并处理可能的连接断开错误。

        :param filters: 过滤条件列表。
        :param query: 查询语句。
        :param first: 是否只取第一条记录，默认为False。
        :return: 查询结果。
        """
        max_retries = 3
        retry_delay = 1  # 重试间隔时间（秒）

        for attempt in range(max_retries):
            try:
                async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
                    query_with_filters = query.where(and_(*filters))
                    result = await session.execute(query_with_filters)
                    if first:
                        return result.scalars().first()
                    else:
                        return result.scalars().all()
            except OperationalError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise e
        return None