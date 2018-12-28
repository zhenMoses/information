from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from redis import StrictRedis
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from config import config_dict

#  1.创建app对象
app = Flask(__name__)
# 根据development健获取对应的配置类名
config_class = config_dict['development']
# DevelopmentConfig ---> 开发模式的app对象
# ProductionConfig --->  线上模式的app对象
app.config.from_object(config_class)

# 2.创建mysql数据库对象
db = SQLAlchemy(app)

# 3.创建redis数据库对象
redis_store = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

"""
   redis_store.set("age", 18)  ---->存储到redis ---0号数据库
   session["name"] = "laowang" ---->存储到redis ---1号数据库
   """
# 4.开启后端的CSRF保护机制
"""
# 底层：
# 1.提取cookie中的csrf_token的值
# 2.提取表单中的csrf_token的值，或者ajax请求的头中的X-CSRFToken键对应的值
# 3.对比这两个值是否相等
"""
CSRFProtect(app)


# 5.借助Session调整flask.session的存储位置到redis中存储
Session(app)


#6. 创建数据管理对象,将app 交给管理对象管理
manager = Manager(app)
#  7.数据库迁移初始化
Migrate(app, db)
# 8.添加迁移命令
manager.add_command('db', MigrateCommand)





@app.route('/')
def index():
    return "hello world"





if  __name__ =='__main__':
       # 9.使用manager对象启动flask项目,代替app.run()
       manager.run()