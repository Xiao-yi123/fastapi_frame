"""
@Package
@File      models.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


MODEl_JOIN_QUERY = {} # 模型关联关系 使用join查询时会用到
# 示例
# {
#     "UsersModel":{
#         "model":UsersModel,
#         "relationship_name":"users_model",
#     },
#     "TkModel":{
#         "model":TkModel,
#         "relationship_name": "tk_model",
#     }
#
# }

__all__ = [
    "Base",
    "MODEl_JOIN_QUERY"
]