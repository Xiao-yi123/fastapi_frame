"""
@Package   
@File      __init__.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
from fastapi import FastAPI, APIRouter
from starlette.staticfiles import StaticFiles



class BaseRouter:
    def __init__(self, server: FastAPI):
        self.server = server

    def registerRouter(self):
        self.server.mount("/static", StaticFiles(directory="static"), name="static")



__all__ = ["BaseRouter"]
