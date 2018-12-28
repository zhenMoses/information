
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import  creat_app,db,redis_store

app = creat_app("development")

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