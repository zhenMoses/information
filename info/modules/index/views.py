from info.modules.index import index_bp
import logging
from flask import current_app, session, jsonify,request
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


@index_bp.route('/news_list')
def get_news_list():
    """
    1.获取参数
        1.1 cid:分类id，p：当前页码，默认值：1表示第一页数据，per_page:每一页多少条数据，默认值：10
    2.检验参数
            2.1 cid非空判断
           2.2 将数据int强制类型转换
    3.逻辑处理
        3.1 根据cid作为查询条件，新闻的时间降序排序,进行分页查询
       3.2 将新闻对象列表转换成字典列表
    4.返回值
    :return:
    """
    #1.1 cid:分类id，p：当前页码，默认值：1表示第一页数据，per_page:每一页多少条数据，默认值：10

    cid = request.args.get('cid')
    p = request.args.get('page', 1)
    per_page = request.args.get('per_page', 10)

    #2.1 cid非空判断
    if not cid:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    # 2.2 将数据int强制类型转换
    try:
        cid = int(cid)
        p = int(p)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数类型错误")


    # 3.1 根据cid作为查询条件，新闻的时间降序排序,进行分页查询
    filter_list = []
    if cid != 1:
        filter_list.append(News.category_id == cid)

    try:
        paginate = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(p,per_page,False)

        # 获取当前所有的数据
        news_list=paginate.items

        # 获取总页面
        total_page = paginate.pages
        # 获取当前页面
        current_page = paginate.page
        # print(news_list)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻列表数据异常")

    #  3.2 将新闻对象列表转换成字典列表
    news_list_dict=[]
    for news in news_list if news_list else []:
        news_list_dict.append(news.to_dict())
    # print(news_list_dict)
    # 4.组织返回数据
    data = {
        "news_list": news_list_dict,
        "current_page": current_page,
        "total_page": total_page
    }

    return jsonify(errno=RET.OK, essmsg="查询数据成功", data=data)


@index_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')