from flask import Flask, session, g, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect,generate_csrf
from redis import StrictRedis
from flask_session import Session
from config import config_dict
import logging

from logging.handlers import RotatingFileHandler
from info.utils.common import do_index_class, get_user_data

# 只是申明了db对象而已，并没有做真实的数据库初始化操作
db = SQLAlchemy()


# 将redis数据库对象申明成全局变量
# # type:StrictRedis 提前申明redis_store数据类型
redis_store = None  #  type:StrictRedis



def write_log(config_class):
    """日志使用"""

    # 设置日志的记录等级
    logging.basicConfig(level=config_class.LOG_LEVEL)  # 调试debug级

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小:100M、保存的日志文件个数上限
    # backCount=10 是指log文件存储不足,最多复制10个文件
    file_log_handler = RotatingFileHandler("./logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息

    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)





 # 将app封装起来，给外界调用提供一个借口
# development --- 返回的是开发模式的app对象
# production --- 返回的是线上模式的app对象
def creat_app(config_name):
    """
    将与app相关联的配置封装到`工厂方法`中
    :return: app对象
    """

    #  1.创建app对象
    app = Flask(__name__)
    # 根据development健获取对应的配置类名
    config_class = config_dict[config_name]
    # DevelopmentConfig ---> 开发模式的app对象
    # ProductionConfig --->  线上模式的app对象
    app.config.from_object(config_class)


    # 记录日志
    write_log(config_class)
    # 2.创建mysql数据库对象
    # db = SQLAlchemy(app)
    # 延迟加载，懒加载思想，当app有值的时候才进行真正的初始化操作
    db.init_app(app)
    # 3.创建redis数据库对象
    global redis_store
    redis_store = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

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
    # CSRFProtect(app)
    #
    # @app.after_request
    def set_csrf_token(response):

        csrf_token = generate_csrf()

        response.set_cookie =("crsk_token",csrf_token)

        return response


    @app.errorhandler(404)
    @get_user_data
    def handler_404(err):
        user=g.user
        data={
            "user_info":user.to_dict() if user else None
        }
        return render_template('news/404.html',data=data)
    # 添加自定义过滤器
    app.add_template_filter(do_index_class,"do_index_class")


    # 5.借助Session调整flask.session的存储位置到redis中存储
    Session(app)



    # 6.注册首页蓝图
    # 将蓝图的导入延迟到工厂方法中，真正需要注册蓝图的时候再导入，能够解决循环导入的文件
    # 注册首页蓝图
    from info.modules.index import index_bp
    app.register_blueprint(index_bp)
    # 登录注册模块的蓝图
    from info.modules.passport import passport_bp
    app.register_blueprint(passport_bp)
    # 新闻模块的蓝图
    from info.modules.news import news_bp
    app.register_blueprint(news_bp)
    # 个人中心模块的蓝图
    from info.modules.profile import profile_bp
    app.register_blueprint(profile_bp)
    return app
