from info.modules.index import index_bp
import logging
from flask import current_app


@index_bp.route('/')
def index():
    from info import redis_store
    redis_store.set("name", "laowang")

    # 日志使用
    logging.debug("This is a debug log.")
    logging.info("This is a info log.")
    logging.warning("This is a warning log.")
    logging.error("This is a error log.")
    logging.critical("This is a critical log.")


    # 另外一种记录日志的方法
    # flask中记录日志方法（项目采用这种方式记录）
    current_app.logger.debug("flask记录debug信息")
    return "index"