from flask import session, current_app, jsonify, g


from info.response_code import RET


def do_index_class(index):
    if index ==1:
        return "first"
    elif index ==2:
        return "second"
    elif index == 3:
        return "third"
    else:
        return ""


 # 使用装饰器封装登录成功获取用户对象
# 传入参数：view_func被装饰的视图函数名称

# 问题：只要使用装饰器装饰函数，装饰器会改变函数的函数名称&函数的内部注释
#
# 解决方案： 1.导入import functools
# 2.@functools.wraps(func)装饰到wrapper内层装饰器函数上
#
import functools
def get_user_data(view_func):
    # 1.实现装饰器业务逻辑
    @functools.wraps(view_func)
    def user_info(*args,**kwargs):
        user_id = session.get('user_id')
        # 1.查询当前用户id
        # 先声明防止局部变量不能访问
        user = None
        from info.models import User
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")
        # 引入临时全局变量,使user变成全局变量
        g.user=user

        return view_func(*args,**kwargs)
    return user_info