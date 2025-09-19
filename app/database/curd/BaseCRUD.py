
from .mixins import ReadMixin,QueryMixin,DeleteMixin,CreateMixin,UpdateMixin

class BaseCRUD(ReadMixin,QueryMixin,DeleteMixin,CreateMixin,UpdateMixin):
    """
    基础CRUD操作类，提供基本的数据增删改查功能。

    :ivar _model: 数据库模型类。
    """

__all__ = ['BaseCRUD']