
import sys
from fastapi import FastAPI
import uvicorn

from app.routers import registerRouter
from config.exceptions import registerCustomErrorHandle
from config.middleware import make_middlewares

from config.rabbitmq import RabbitManager, RabbitConfig
from config.settings import appSettings, mqSettings

sys.dont_write_bytecode  =True
def create_app() -> FastAPI:
    # 设置事件循环策略
    app = FastAPI(
        title=appSettings.name,
        description=appSettings.description,
        version=appSettings.version,
        debug=appSettings.debug,
        docs_url=appSettings.docs_url,
        redoc_url=appSettings.redoc_url,
        openapi_url=appSettings.openapi_url,
        middleware=make_middlewares(),
    )
    registerRouter(app)
    registerCustomErrorHandle(app)
    # 在启动FastAPI应用时初始化数据库

    return app


app = create_app()


# 在后台线程启动消费者
if appSettings.start_mq:
    rabbit_config = RabbitConfig()
    rabbit_manager = RabbitManager(rabbit_config=rabbit_config.connfig_to_dict())
    for item in rabbit_config.RabbitMq.values():
        if "start_monitoring" in item.type:
            rabbit_manager.start_monitoring(exchange_name=item.exchange_name,queue_name=item.queue_start_monitoring)
        if "monitor_queue" in item.type:
            rabbit_manager.monitor_queue(exchange_name=item.exchange_name, queue_info=item.queue_monitor_queue)




if __name__ == "__main__":
    uvicorn.run(app="main:app", host=appSettings.host, port=appSettings.port, reload=appSettings.reload)





