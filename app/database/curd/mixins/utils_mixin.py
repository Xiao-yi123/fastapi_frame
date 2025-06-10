import importlib
from datetime import datetime
from typing import List, Optional, Dict, Any, Type

from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, BinaryExpression, create_engine
from sqlalchemy.future import select
from sqlalchemy.sql.ddl import CreateTable
from sqlalchemy.sql.selectable import Select  # ✅ 添加导入语句
from sqlalchemy.orm.query import Query       # ✅ 可选：用于同步 Query 类型判断

from app.types import PagingQueryParams
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

class UtilsMixin:
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

    def build_query_base(
            self,
            base_query,  # 可以是 session.query(Model) 或 select(Model)
            filter_params: Optional[Dict[str, Any]] = None,
            or_filter_params: Optional[List[Dict[str, Any]]] = None,
            order_by: Optional[List[Any]] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            columns: Optional[List[Any]] = None,
            group_by: Optional[List[Any]] = None,
            distinct: bool = False,
            join_models: Optional[List[Type]] = None,
            join_conditions: Optional[List[BinaryExpression]] = None,
            options: Optional[List[Any]] = None,
    ):
        """
        构建基础查询对象，支持同步和异步模式。
        """

        is_select = isinstance(base_query, Select)
        is_query = isinstance(base_query, Query)

        # -----------------------------
        # 处理字段选择
        # -----------------------------
        if columns:
            if is_select:
                base_query = select(*columns)
            elif is_query:
                base_query = base_query.with_entities(*columns)

        # -----------------------------
        # 添加 JOIN 条件
        # -----------------------------
        if join_models and join_conditions:
            for model, condition in zip(join_models, join_conditions):
                if is_select:
                    base_query = base_query.join(model, condition)
                elif is_query:
                    base_query = base_query.join(model, condition)

        # -----------------------------
        # 添加过滤条件
        # -----------------------------
        if filter_params:
            conditions = self.get_filters(self._model, **filter_params)
            if conditions:
                if is_select:
                    base_query = base_query.where(and_(*conditions))
                elif is_query:
                    base_query = base_query.filter(and_(*conditions))

        # -----------------------------
        # 添加 OR 过滤条件
        # -----------------------------
        if or_filter_params:
            or_conditions = []
            for params in or_filter_params:
                conditions = self.get_filters(self._model, **params)
                if conditions:
                    or_conditions.append(and_(*conditions))
            if or_conditions:
                if is_select:
                    base_query = base_query.where(or_(*or_conditions))
                elif is_query:
                    base_query = base_query.filter(or_(*or_conditions))

        # -----------------------------
        # 分组
        # -----------------------------
        if group_by:
            for group in group_by:
                if is_select:
                    base_query = base_query.group_by(group)
                elif is_query:
                    base_query = base_query.group_by(group)

        # -----------------------------
        # 去重
        # -----------------------------
        if distinct:
            if is_select:
                base_query = base_query.distinct()
            elif is_query:
                base_query = base_query.distinct()

        # -----------------------------
        # 加载选项（如 joinedload）
        # -----------------------------
        if options:
            for option in options:
                if is_select:
                    base_query = base_query.options(option)
                elif is_query:
                    base_query = base_query.options(option)

        # -----------------------------
        # 排序
        # -----------------------------
        if order_by:
            for order in order_by:
                if is_select:
                    base_query = base_query.order_by(order)
                elif is_query:
                    base_query = base_query.order_by(order)

        # -----------------------------
        # 分页
        # -----------------------------
        if limit is not None:
            if is_select:
                base_query = base_query.limit(limit)
            elif is_query:
                base_query = base_query.limit(limit)

        if offset is not None:
            if is_select:
                base_query = base_query.offset(offset)
            elif is_query:
                base_query = base_query.offset(offset)

        return base_query

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


__all__ = [
    "CRUDJoinParams",
    "UtilsMixin"
]