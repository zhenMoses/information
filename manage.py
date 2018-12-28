from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import  creat_app,db,redis_store
import logging
from flask import current_app



app = creat_app("development")



#6. 创建数据管理对象,将app 交给管理对象管理
manager = Manager(app)
#  7.数据库迁移初始化
Migrate(app, db)
# 8.添加迁移命令
manager.add_command('db', MigrateCommand)





@app.route('/')
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
    return "hello world"





if  __name__ =='__main__':
       # 9.使用manager对象启动flask项目,代替app.run()
       manager.run()