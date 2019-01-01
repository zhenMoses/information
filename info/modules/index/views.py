from info.modules.index import index_bp
import logging
from flask import current_app, session, jsonify
from flask import  render_template
from info.models import User, News, Category
from info.response_code import RET
from info import constants

@index_bp.route('/')
def index():
    # ----------1.用户登录成功后页面显示----------
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






    #-------------2.查询新闻点击排行数据展示--------------



    try:
        news_rank_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询新闻数据异常")

    news_list_dict=[]
    # if news_rank_list:
    #     for news in news_rank_list:
    #         news_list=news.to_dict()
    #         news_list_dict.append(news_list)

    for news in news_rank_list if news_rank_list else []:
        news_list_dict.append(news.to_dict())


# ---------------3.查询新闻分类数据展示----------------
#     categories:[新闻分类列表]
    try:
        categories=Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询分类数据异常")

    category_dict_list=[]
    for category in categories if categories else []:
        category_dict_list.append(category.to_dict())


    # 4.组织响应数据
    data = {
        "user_info": user_dict,
        "chick_news_list": news_list_dict,
        "categories":category_dict_list
    }
    # 5.返回渲染页面
    return render_template("news/index.html", data=data)





@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')