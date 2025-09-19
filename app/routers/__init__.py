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



import importlib
import os
from pathlib import Path

from fastapi import FastAPI,APIRouter
from starlette.staticfiles import StaticFiles
def auto_load_routers(base_package: str, base_path: Path) -> APIRouter:
    router = APIRouter()

    def recursive_import(package_name: str, package_path: Path):
        for entry in os.listdir(package_path):
            full_path = package_path / entry
            if full_path.is_dir() and (full_path / "__init__.py").exists():
                # 如果是包，则递归注册子包中的路由
                sub_package_name = f"{package_name}.{entry}"
                sub_router = APIRouter(prefix=f"/{entry}")
                recursive_import(sub_package_name, full_path)
                router.include_router(sub_router)
            elif full_path.is_file() and entry.endswith(".py") and entry != "__init__.py":
                # 如果是模块，则导入模块并注册路由
                module_name = entry[:-3]  # 去掉 .py 后缀
                full_module_name = f"{package_name}.{module_name}"
                module = importlib.import_module(full_module_name)
                if hasattr(module, "router"):
                    router.include_router(module.router, prefix=f"/{module_name}")

    recursive_import(base_package, base_path)
    return router


def registerRouter(server: FastAPI):
    server.mount("/static", StaticFiles(directory="static"), name="static")
    server.include_router(auto_load_routers("app.routers", Path(__file__).parent ))




__all__ = ["registerRouter"]
