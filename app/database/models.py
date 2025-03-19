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



__all__ = [
    "Base"
]