from info.modules.index import index_bp
import logging
from flask import current_app, session, jsonify
from flask import  render_template
from info.models import User
from info.response_code import RET


@index_bp.route('/')
def index():
    # ----------用户登录成功后页面显示----------
    """
        #     1.查询用户,获取用户id
        # 2.根据用户id获取用户对象
        # 3.将用户对象转成字典
        # 4.组织响应数据
        # 5.返回渲染页面

    """
    #     1.查询用户,获取用户id
    user_id = session.get("user_id")
    # 2.根据用户id获取用户对象
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,essmsg="查询用户数据异常")

    # 3.将用户对象转成字典
    """
        if user:
        user_dict = user.to_dict()
    """

    user_dict = user.to_dict() if user else None
    # 4.组织响应数据
    data ={
        "user_info": user_dict
    }
    # 5.返回渲染页面
    return render_template("news/index.html", data=data)


@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')