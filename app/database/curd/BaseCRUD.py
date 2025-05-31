import asyncio
import importlib
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field
from sqlalchemy import and_, func, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.future import select
from sqlalchemy.orm import subqueryload, joinedload
from sqlalchemy.sql.ddl import CreateTable

from app.database import XhsNoteModel
from app.types.request import PagingQueryParams
from app.types.response import ResponseFail
from config.database import getDatabaseSessionAsync, getDatabaseSession


class CRUDJoinParams(BaseModel):
    model: Optional[str] = Field(None, description='用户关联模型')
    relationship_name: Optional[str] = Field(None, description='关联模型名称')
    params: Optional[dict] = Field(None, description='其他查询参数')
    fields:Optional[List[str]] = Field(None, description='需要查询的字段')
    is_outerjoin: Optional[bool] = Field(False, description='是否使用外连接')
    is_join: Optional[bool] = Field(False, description='是否使用内连接')
    is_subqueryload: Optional[bool] = Field(False, description='是否使用子查询加载')
    is_joinedload: Optional[bool] = Field(False, description='是否使用 joinedload 加载')


class BaseCRUD:
    """
    基础CRUD操作类，提供基本的数据增删改查功能。

    :ivar _model: 数据库模型类。
    """

    def __init__(self, connect_str: str = None):
        """
        初始化方法，设置模型类为None。
        """
        self._model = None
        self.connect_str = connect_str
        self.getDatabaseSession = getDatabaseSession
        self.getDatabaseSessionAsync = getDatabaseSessionAsync

    def get_filters(self, model, **kwargs):
        """
        根据传入的模型、是否使用模糊查询以及关键字参数生成查询过滤条件列表。

        :param model: 模型对象，用于获取属性。
        :param kwargs: 动态关键字参数，代表查询条件的键值对。
        :return: 一个包含所有过滤条件的列表，供后续进行数据库查询使用。
        """
        filters = []
        for key, value in kwargs.items():
            if hasattr(model, key):
                if value is not None:
                    if isinstance(value, tuple) and len(value) == 2:
                        operator, val = value
                        operator = operator.lower()
                        match operator:
                            case '>':
                                filters.append(getattr(model, key) > val)
                            case '<':
                                filters.append(getattr(model, key) < val)
                            case '!=':
                                filters.append(getattr(model, key) != val)
                            case ">=":
                                filters.append(getattr(model, key) >= val)
                            case "<=":
                                filters.append(getattr(model, key) <= val)
                            case "in":
                                filters.append(getattr(model, key).in_(val))
                            case "not in":
                                filters.append(getattr(model, key).notin_(val))
                            case "like":
                                filters.append(getattr(model, key).like(f"%{value}%"))
                            case "ilike":
                                filters.append(getattr(model, key).ilike(f"%{value}%"))
                            case "is_null":
                                filters.append(getattr(model, key).is_(None))
                            case "is_not_null":
                                filters.append(getattr(model, key).is_not(None))
                            # 区间查询
                            case "between":
                                filters.append(getattr(model, key).between(value[1][0], value[1][1]))

                            case _:
                                filters.append(getattr(model, key) == value)
                    else:
                        filters.append(getattr(model, key) == value)
                else:
                    filters.append(getattr(model, key).is_(None))
        return filters

    def build_query(self, model_field: Optional[List[str]] = None, join_fields: any = None):
        """
        根据指定的模型字段和关联模型字段构建查询。

        :param model_field: 主模型需要查询的字段列表，默认为None。
        :param join_fields: 关联模型及其字段字典，例如：{"user": ["id", "name"]}，默认为None。
        :return: 包含主模型字段和关联模型字段的查询列。
        """
        columns = []

        # 添加主模型字段
        if model_field:
            columns.extend(getattr(self._model, field) for field in model_field)
        else:
            columns.append(self._model)
        # 添加关联模型字段
        if join_fields:
            for join_params in join_fields:
                if (not isinstance(join_params, CRUDJoinParams)) or not join_params.fields:
                    continue
                try:
                    module = importlib.import_module("app.database")
                    model_class = getattr(module, join_params.model)
                    columns.extend(getattr(model_class, field) for field in join_params.fields)
                except (ImportError, AttributeError) as e:
                    raise ValueError(f"无法加载模型 {join_params.model}: {e}")
        return columns

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
                    ResponseFail(msg=f"SQL GET ERROR:{str(e)}")
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
                    ResponseFail(msg=f"SQL GET ERROR:{str(e)}")
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
                ResponseFail(msg=f"SQL GET ERROR:{str(e)}")
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

    async def update_by_id(self, id: int, update):
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
        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            query = await session.execute(select(self._model).where(self._model.id == id))
            result = query.scalars().first()
            if result:
                for key, value in update_dict.items():
                    setattr(result, key, value)
                await session.commit()
        return result

    def update_by_id_sync(self, id: int, update):
        # 检查 `update` 是否有 `dict` 方法
        if isinstance(update, BaseModel):
            update_dict = update.dict(exclude_unset=True)
        elif isinstance(update, dict):
            update_dict = update
        else:
            raise ValueError("create 参数必须是 Pydantic 模型实例 or dict类型")
        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            query = session.query(self._model)  # 创建查询对象
            result = query.filter(self._model.id == id).update(update_dict)  # 使用查询对象的update方法
            session.commit()  # 提交事务
        return result

    async def batch_update_by_ids(self, ids: List[int], update):
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
        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            query = await session.execute(select(self._model).where(self._model.id.in_(ids)))
            results = query.scalars().all()
            for result in results:
                for key, value in update_dict.items():
                    setattr(result, key, value)
            await session.commit()
        return len(results)

    def batch_update_by_ids_sync(self, ids: List[int], update):
        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            query = session.query(self._model)  # 创建查询对象
            result = query.filter(self._model.id.in_(ids)).update(update, synchronize_session=False)  # 使用in_方法批量更新
            session.commit()  # 提交事务
        return result

    async def delete_by_id(self, id: int):
        """
        根据ID删除一条记录。

        :param id: 记录的ID。
        :return: 删除的记录对象。
        """
        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            query = await session.execute(select(self._model).where(self._model.id == id))
            result = query.scalars().first()
            if result:
                await session.delete(result)
                await session.commit()
        return result

    def delete_by_id_sync(self, id: int):
        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            query = session.query(self._model)
            result = query.filter(self._model.id == id).delete()
            session.commit()
        return result

    async def batch_delete(self, ids: List[int]):
        """
        批量删除多条记录。

        :param ids: 记录的ID列表。
        :return: 删除成功的记录数量。
        """
        # 异步获取数据库会话
        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            # 执行异步查询，根据用户ID和记录ID列表筛选出需要删除的记录
            query = await session.execute(
                select(self._model).where(and_(self._model.id.in_(ids)))
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

    def batch_delete_sync(self, ids: list):
        with self.getDatabaseSession(connect_str=self.connect_str) as session:
            query = session.query(self._model)
            result = query.filter(
                self._model.id.in_(ids),
            ).delete(synchronize_session=False)
            session.commit()
        return result

    def serialization(self, all_data, include: List[str] = None, exclude: List[str] = None):
        """
        序列化数据对象。

        :param all_data: 需要序列化的数据对象列表。
        :param include: 需要包含的字段列表，默认为None。
        :param exclude: 需要忽略的字段列表，默认为None。
        :return: 序列化后的数据列表。
        """
        if not isinstance(all_data, (list, tuple, dict)):
            raise ValueError("all_data must be a list or tuple")

        serialized_data = []
        for data in all_data:
            data_dict = {k: v for k, v in data.__dict__.items() if not k.startswith('_sa')}

            # 处理 datetime 对象
            for key, value in data_dict.items():
                if isinstance(value, datetime):
                    data_dict[key] = value.isoformat()

            if include:
                data_dict = {k: v for k, v in data_dict.items() if k in include}
            elif exclude:
                data_dict = {k: v for k, v in data_dict.items() if k not in exclude}

            serialized_data.append(data_dict)

        return serialized_data

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

    @staticmethod
    def model_to_dict(model):
        """
        将数据库模型实例转换为字典

        参数:
        model - 数据库模型实例

        返回:
        包含模型数据的字典，其中键是列名，值是对应的值
        """
        # 使用列表推导式和getattr函数将模型的每个列的名和值转换为字典
        return {c.name: getattr(model, c.name) for c in model.__table__.columns}

    @staticmethod
    def model_to_sql(Base):
        # 创建内存中的数据库引擎
        engine = create_engine('sqlite:///:memory:')

        # 获取元数据
        metadata = Base.metadata
        # 生成 SQL 语句
        sql_statements = "\n".join(str(CreateTable(table).compile(engine)) for table in metadata.sorted_tables)
        return sql_statements

    @staticmethod
    async def query_data(curd, param: PagingQueryParams, other_param: dict = {}):
        # 将请求参数转换为字典，排除None值
        new_param = param.dict(exclude_none=True)
        if other_param:
            new_param.update(other_param)
        # 使用转换后的参数获取接收记录列表数据
        data = await curd.get_list_page(**new_param)
        # 序列化数据为InDBaseSchema格式
        new_data = curd.serialization(data)
        # 移除参数中的分页相关字段
        if 'current' in new_param: del new_param['current']
        if 'size' in new_param: del new_param['size']
        # 使用更新后的参数获取接收记录总数用于查询符合条件的数量
        num = await curd.get_count(**new_param)
        return {
            "data": new_data,
            "total": num,
        }


__all__ = ["CRUDJoinParams", 'BaseCRUD']
