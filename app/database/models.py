"""
@Package
@File      models.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, VARCHAR, TIMESTAMP, text, TEXT
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()


class UserRoleEnum(str, Enum):
    SUPER = "R_SUPER"
    ADMIN = "R_ADMIN"
    NORMALUSER = "R_NORMAL_USER"


class UserModel(Base):
    __tablename__ = 'users'
    __comment__ = '用户表'
    # 索引
    # __table_args__ = (
    #     Index('unique_xhs_user_id_status', 'xhs_user_id', 'status', unique=True),
    # )
    id: Mapped[int] = mapped_column(INTEGER(11), primary_key=True, comment='ID',autoincrement=True)
    role: Mapped[UserRoleEnum] = mapped_column(String(25), server_default=text(UserRoleEnum.NORMALUSER),
                                               comment='权限：admin超级管理员 user普通用户')
    nickname: Mapped[str] = mapped_column(VARCHAR(255), comment='昵称')
    avatar: Mapped[str] = mapped_column(VARCHAR(255), comment='头像')
    username: Mapped[str] = mapped_column(VARCHAR(50), comment='用户名')
    password: Mapped[str] = mapped_column(VARCHAR(255), comment='密码')
    vip_end: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'),
                                                       comment='会员截至时间')
    login_time: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'),
                                                          comment='登录时间')
    token: Mapped[Optional[str]] = mapped_column(TEXT, comment='登录令牌')
    auth_num: Mapped[Optional[int]] = mapped_column(INTEGER(11), server_default=text("'0'"), comment='授权数量')
    use_num: Mapped[Optional[int]] = mapped_column(INTEGER(11), server_default=text("'0'"), comment='已使用')
    login_ip: Mapped[Optional[str]] = mapped_column(VARCHAR(50), server_default=text("'127.0.0.1'"), comment='登录IP')

    # 定义关联关系
    # xhs_collection_task_model = relationship("XhsCollectionTaskModel", back_populates="user_model", lazy='joined')
    # 定义关联关系
    # xhs_model = relationship("XhsModel", back_populates="user_model", lazy='joined')
    # xhs_groups_model = relationship("XhsGroupModel", back_populates="user_model", lazy='joined')
    # xhs_node_model = relationship("XhsNodeModel", back_populates="user_model", lazy='joined')
    # xhs_send_model = relationship("XhsSendModel", back_populates="user_model", lazy='joined')
    # log_model = relationship("LogModel", back_populates="user_model", lazy='joined')


__all__ = [
    "Base",
    "UserModel",
    "UserRoleEnum",
]