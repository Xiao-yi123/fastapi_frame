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


TABLE_RELATIONSHIP = {

}
 # 模型关联关系 使用join查询时会用到
# 示例
# TABLE_RELATIONSHIP = {
#     "数据表名": {
#         "model_name": "数据表对应的model名",
#         "table_name": "数据表名",
#         "对应关联的数据表名": {
#             "table_name": "对应关联的数据表名",
#             "model_name": "对应关联的数据表的model名",
#             "relationship_name": "在对应数据的model类里面的关系名",
#         },
#     "users": {
#         "model_name": "UsersModel",
#         "table_name": "users",
#         "xhs_tk": {
#             "table_name": "xhs_tk",
#             "model_name": "TkModel",
#             "relationship_name": "tk_model",
#         },
#         "xhs_note": {
#             "table_name": "xhs_note",
#             "model_name": "XhsNoteModel",
#             "relationship_name": "xhs_note_model",
#         },
#         "sd_group": {
#             "table_name": "sd_group",
#             "model_name": "SdGroupModel",
#             "relationship_name": "sd_group_model",
#         },
#     },
#     "sd_group": {
#         "model_name": "SdGroupModel",
#         "table_name": "sd_group",
#         "users": {
#             "table_name": "users",
#             "model_name": "UsersModel",
#             "relationship_name": "users_model",
#         },
#         "xhs_tk": {
#             "table_name": "xhs_tk",
#             "model_name": "TkModel",
#             "relationship_name": "tk_model",
#         },
#         "xhs_note": {
#             "table_name": "xhs_note",
#             "model_name": "XhsNoteModel",
#             "relationship_name": "xhs_note_model",
#         },
#
#     },
#     "xhs_tk": {
#         "model_name": "TkModel",
#         "table_name": "xhs_tk",
#         "users": {
#             "table_name": "users",
#             "model_name": "UsersModel",
#             "relationship_name": "users_model",
#         },
#         "sd_group": {
#             "table_name": "sd_group",
#             "model_name": "SdGroupModel",
#             "relationship_name": "sd_group_model",
#         },
#     },
#     "xhs_note": {
#         "model_name": "XhsNoteModel",
#         "table_name": "xhs_note",
#         "users": {
#             "table_name": "users",
#             "model_name": "UsersModel",
#             "relationship_name": "users_model",
#         },
#         "sd_group": {
#             "table_name": "sd_group",
#             "model_name": "SdGroupModel",
#             "relationship_name": "sd_group_model",
#         },
#     },
# }


__all__ = [
    "Base",
    "TABLE_RELATIONSHIP"
]