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
        self.v1_router = APIRouter(prefix="/v1")

    def __getV1SystemRoute(self):
        from app.routers.v1.system.auth import router_auth
        from app.routers.v1.system.route import router_route
        from app.routers.v1.system.manage import router_manage

        self.v1_router.include_router(router_auth)
        self.v1_router.include_router(router_route)
        self.v1_router.include_router(router_manage)

    def includeV1Route(self):

        self.__getV1SystemRoute()
        self.server.include_router(self.v1_router)

    def registerRouter(self):
        self.server.mount("/static", StaticFiles(directory="static"), name="static")
        self.includeV1Route()


__all__ = ["BaseRouter"]
