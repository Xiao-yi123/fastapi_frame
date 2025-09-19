"""
@Package   
@File      DatebaseOperation.py
@Version   V1.0
@Author    一云 <yi_yun200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from sqlalchemy import create_engine,MetaData,text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError

class DateBaseOperation:
    def __init__(self,host: str = None,port: int = None,user: str = None,password: str = None,table_name: str = None,database_type: str = "mysql"):
        self._model = None
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database_type = database_type
        # 创建基类
        self.Base = declarative_base()
        match database_type:
            case "mysql":
                self.connect_type = "mysql+pymysql"
                self.engine = create_engine(f'{self.connect_type}://{user}:{password}@{host}:{port}/{table_name}')
            case "postgresql":
                self.connect_type = "postgresql+psycopg2"
                self.engine = create_engine(f'{self.connect_type}://{user}:{password}@{host}:{port}/{table_name}')
            case "sqlite":
                self.connect_type = "sqlite"
                self.engine = create_engine(f'{self.connect_type}:///{table_name}')
            case _:
                raise ValueError("数据库类型错误")
        # 创建所有表
        self.Base.metadata.create_all(self.engine)

        # 创建会话
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        # 创建元数据对象
        self.metadata = MetaData()

        # 从数据库中加载所有表结构
        self.metadata.reflect(bind=self.engine)

    def __del__(self):
        self.session.close()
    def get_all_table(self):
        # 获取所有表名
        table_names = self.metadata.tables.keys()
        return table_names

    def clear_table(self,table_name_param=None):
        # 禁用外键约束检查
        self.session.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
        # 遍历所有表并清空数据
        for table_name in self.get_all_table():
            table = self.metadata.tables[table_name]
            if table_name_param:
                if table_name == table_name_param:
                    self.session.execute(table.delete())
                    break
            else:
                self.session.execute(table.delete())
        # 启用外键约束检查
        self.session.execute(text('SET FOREIGN_KEY_CHECKS = 1'))

        # 提交会话
        self.session.commit()

    def del_table(self,table_name_param=None):
        # 禁用外键约束检查
        self.session.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
        if table_name_param:
            table = self.metadata.tables.get(table_name_param)
            table.drop(self.engine)
        else:
            self.metadata.drop_all(self.engine)
        # 启用外键约束检查
        self.session.execute(text('SET FOREIGN_KEY_CHECKS = 1'))

    def create_table(self,base_class):
        try:
            # 创建表
            base_class.metadata.create_all(self.engine)
            print("表创建成功。")
        except ProgrammingError as e:
            if "Table 'users' already exists" in str(e):
                print("表已存在，无需重复创建。")
            else:
                print(f"创建表时发生其他错误: {e}")

    def check_and_create_database(self, database):
        """
        检查指定的 MySQL 数据库是否存在，若不存在则创建该数据库。

        :param host: 数据库主机地址
        :param port: 数据库端口号
        :param user: 数据库用户名
        :param password: 数据库用户密码
        :param database: 数据库名称
        :return: 无
        """
        # 创建一个不指定数据库的引擎，用于检查数据库是否存在
        engine = create_engine(f'{self.connect_type}://{self.user}:{self.password}@{self.host}:{self.port}')

        try:
            # 使用上下文管理器创建一个连接
            with engine.connect() as connection:
                # 尝试连接到指定数据库
                connection.execute(text(f'USE {database}'))
                print(f"数据库 {database} 已存在。")
        except ProgrammingError as e:
            if "Unknown database" in str(e):
                # 若数据库不存在，则创建数据库
                with engine.connect() as connection:
                    connection.execute(text(f'CREATE DATABASE {database}'))
                    connection.commit()
                print(f"数据库 {database} 创建成功。")
            else:
                print(f"执行操作时发生其他错误: {e}")

    # @staticmethod
    # def model_to_dict(model):
    #     """
    #     将数据库模型实例转换为字典
    #
    #     参数:
    #     model - 数据库模型实例
    #
    #     返回:
    #     包含模型数据的字典，其中键是列名，值是对应的值
    #     """
    #     # 使用列表推导式和getattr函数将模型的每个列的名和值转换为字典
    #     return {c.name: getattr(model, c.name) for c in model.__table__.columns}
    #
    # @staticmethod
    # def model_to_sql(Base):
    #     # 创建内存中的数据库引擎
    #     engine = create_engine('sqlite:///:memory:')
    #
    #     # 获取元数据
    #     metadata = Base.metadata
    #     # 生成 SQL 语句
    #     sql_statements = "\n".join(str(CreateTable(table).compile(engine)) for table in metadata.sorted_tables)
    #     return sql_statements

if __name__ == '__main__':
    host = "43.255.159.42"
    port = 3306
    user = "texg"
    password = "TsYisNDNB4yJwE8G"
    table_name = "texg"
    d = DateBaseOperation(host, port, user, password, table_name)
    # d = DateBaseOperation("127.0.0.1", 3306, "root", "root", "baiwan")
    # d.get_all_table()
    # d.clear_table("sd_group")
    # d.del_table("sd_group")
    # d.create_table(Base)
    d.check_and_create_database(table_name)