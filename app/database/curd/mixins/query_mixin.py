from typing import List, Optional, Dict, Any, Type, Tuple, Union
from sqlalchemy import func, BinaryExpression
from sqlalchemy.future import select
from app.database.curd.mixins.utils_mixin import UtilsMixin


class QueryMixin(UtilsMixin):
    def query_sync(
            self,
            filter_params: Optional[Dict[str, Any]] = None,
            or_filter_params: Optional[List[Dict[str, Any]]] = None,
            order_by: Optional[List[Any]] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            columns: Optional[List[Any]] = None,
            group_by: Optional[List[Any]] = None,
            distinct: bool = False,
            count_only: bool = False,
            join_models: Optional[List[Type]] = None,
            join_conditions: Optional[List[BinaryExpression]] = None,
            options: Optional[List[Any]] = None
    ) -> Union[List[Dict[str, Any]], int, List[Tuple]]:
        with self.getDatabaseSession(connect_str=self.connect_str) as session:

            # 初始化基础查询
            if columns:
                base_query = session.query(*columns)
            else:
                base_query = session.query(self._model)

            # 使用统一构建方法
            base_query = self.build_query_base(
                base_query=base_query,
                filter_params=filter_params,
                or_filter_params=or_filter_params,
                order_by=order_by,
                limit=limit,
                offset=offset,
                columns=columns,
                group_by=group_by,
                distinct=distinct,
                join_models=join_models,
                join_conditions=join_conditions,
                options=options
            )

            # 如果只需要计数
            if count_only:
                return base_query.count()

            # 执行查询
            results = base_query.all()

            # 如果查询的是特定列，返回元组列表
            if columns:
                return results

            # 否则转换为字典列表
            return [
                {column.name: getattr(row, column.name) for column in row.__table__.columns}
                for row in results
            ]

    async def query(
            self,
            filter_params: Optional[Dict[str, Any]] = None,
            or_filter_params: Optional[List[Dict[str, Any]]] = None,
            order_by: Optional[List[Any]] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            columns: Optional[List[Any]] = None,
            group_by: Optional[List[Any]] = None,
            distinct: bool = False,
            count_only: bool = False,
            join_models: Optional[List[Type]] = None,
            join_conditions: Optional[List[BinaryExpression]] = None,
            options: Optional[List[Any]] = None
    ) -> Union[List[Dict[str, Any]], int, List[Tuple]]:
        async with self.getDatabaseSessionAsync(connect_str=self.connect_str) as session:
            # 初始化基础查询
            if columns:
                base_query = select(*columns)
            else:
                base_query = select(self._model)

            # 使用统一构建方法
            base_query = self.build_query_base(
                base_query=base_query,
                filter_params=filter_params,
                or_filter_params=or_filter_params,
                order_by=order_by,
                limit=limit,
                offset=offset,
                columns=columns,
                group_by=group_by,
                distinct=distinct,
                join_models=join_models,
                join_conditions=join_conditions,
                options=options
            )

            # 如果只需要计数
            if count_only:
                count_stmt = select(func.count()).select_from(base_query.subquery())
                result = await session.execute(count_stmt)
                return result.scalar_one()

            # 执行查询
            result = await session.execute(base_query)
            rows = result.scalars().all()

            # 如果查询的是特定列，返回元组列表
            if columns:
                return rows

            # 否则转换为字典列表
            return [
                {column.name: getattr(row, column.name) for column in row.__table__.columns}
                for row in rows
            ]

# # 基本查询
# results = query(
#     session=session,
#     model=User,
#     filter_params={
#         'age': ('>', 18),
#         'name': ('like', 'John%')
#     },
#     order_by=[User.age.desc()],
#     limit=10
# )
#
# # JOIN 查询
# results = query(
#     session=session,
#     model=User,
#     join_models=[Order],
#     join_conditions=[User.id == Order.user_id],
#     filter_params={
#         'Order.status': 'paid'
#     },
#     columns=[User.name, Order.order_number]
# )
#
# # OR 条件查询
# results = query(
#     session=session,
#     model=User,
#     or_filter_params=[
#         {'age': ('>', 30)},
#         {'name': ('like', 'Smith%')}
#     ]
# )