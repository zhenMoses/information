from info import constants, db
from info.models import User, News, Comment
from info.modules.news import news_bp
from flask import render_template, session, current_app, jsonify, g, abort, request

from info.response_code import RET
from info.utils.common import get_user_data




@news_bp.route('/<int:news_id>')
@get_user_data
def news_detail(news_id):
    """新闻详情页面展示"""
   # ---------------1.用户登录成功，查询用户基本信息展示----------------
   #  使用g对象传递user对象数据
    user=g.user
    # 3.将用户对象转成字典
    # if user:
    user_dict =user.to_dict() if user else None


    # -------------2.查询新闻点击排行数据展示--------------

    try:
        news_rank_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询新闻数据异常")

    news_list_dict=[]


    for news in news_rank_list if news_rank_list else []:
        news_list_dict.append(news.to_dict())



    # ---------------3.根据新闻id查询新闻详情数据展示----------------

    news_obj = None
    if news_id:
        try:
            news_obj = News.query.get(news_id)

        except Exception as e:
            current_app.logger.error(e)
            abort(404)
            return jsonify(errno=RET.DBERR,errmsg="查询新闻对象失败")

    # 新闻点击量增加
    news_obj.clicks += 1
    # 新闻对象转字典
    news_dict=news_obj.to_dict() if news_obj else None

    # ---------------4.查询当前登录用户是否收藏过当前新闻----------------

    # 标识当前用户是否收藏当前新闻， 默认值False:没有收藏
    is_collected = False

    # user.collection_news 当前用户对象收藏的新闻列表数据
     # news_obj： 当前新闻对象
    # 判断当前新闻对象是否在当前用户对象收藏的新闻列表中

    if news_obj in user.collection_news:
        # 标识当前用户已经收藏该新闻
        is_collected = True

    # ---------------5.查询评论列表数据----------------

    comment_list =[]
    try:
        comment_list= Comment.query.filter(Comment.news_id==news_id).order_by(Comment.create_time.desc()).all()

    except Exception as e:
        current_app.logger.error(e)
    print(comment_list)
    # 评论对象列表转字典列表
    comment_dict=[]

    for comment in comment_list if comment_list else []:
        comment_list_dict=comment.to_dict()
        comment_dict.append(comment_list_dict)



    # 返回数据
    data = {
        "user_info": user_dict,
        "chick_news_list": news_list_dict,
        "news": news_dict,
        "is_collected": is_collected,
        "comments": comment_dict
    }



    return render_template('news/detail.html',data=data)




@news_bp.route('/news_collect',methods=['POST'])
@get_user_data
def get_news_collect():
    """新闻收藏、取消收藏的后端接口"""

    """
          1.获取参数
               1.1 news_id:当前新闻的id，user:当前登录的用户对象，action:收藏，取消收藏的行为
           2.参数校验
               2.1 非空判断
                2.2 action in ["collect", "cancle_collect"]
            3.逻辑处理
               3.1 根据新闻id查询当前新闻对象，判断新闻是否存在
                3.2 收藏：将新闻对象添加到user.collection_news列表中
                3.3 取消收藏：将新闻对象从user.collection_news列表中移除
            4.返回值
        """
    user = g.user
    params_dict = request.json
    news_id = params_dict.get('news_id')
    action = params_dict.get('action')

    #非空判断
    if not all([news_id,action]):
        current_app.logger.error("参数不足")
        return jsonify(errno=RET.PARAMERR,errmsg="参数不足")

    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg="用户尚未登录")


    if action not in ["collect", "cancel_collect"]:
        current_app.logger.error("参数错误")
        return jsonify(errno=RET.PARAMERR,errmsg="参数错误")


    # #3.1 根据新闻id查询当前新闻对象，判断新闻是否存在
    news=None
    try:
        news=News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA,errmsg="新闻不存在")

    # 3.2 收藏：将新闻对象添加到user.collection_news列表中
    if action == "collect":
        user.collection_news.append(news)

    # 3.3 取消收藏：将新闻对象从user.collection_news列表中移除
    else:
        if news in user.collection_news:
            user.collection_news.remove(news)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="保存失败")


    return jsonify(errno=RET.OK, errmsg="成功")



@news_bp.route('/news_comment',methods=['POST'])
@get_user_data
def news_comment():
    # """"""发布(主，子)评论的后端接口""""""

    """
        1.获取参数
            1.获取当前用户对象 ,新闻对象id:news_id,获取评论内容:comment 区分主评论\子评论参数parent_id
        2.检验参数
            2.1 非空判断

        3.逻辑处理
            3.1根据news_id 查询当前新闻对象
            3.2创建评论对象，并给各个属性赋值，保存回数据库
        4.返回值
    """

    #1.获取当前用户对象 ,新闻对象id:news_id,获取评论内容:comment 区分主评论\子评论参数parent_id
    param_dict = request.json
    news_id = param_dict.get("news_id")
    comment = param_dict.get("comment")
    parent_id = param_dict.get("parent_id")
    user = g.user
    print(news_id)
    print(comment)
    print(user)
    #  2.1 非空判断
    if not all([news_id,comment]):
        current_app.logger.error("参数不足")
        return jsonify(errno=RET.PARAMERR,errmsg="参数不足")


    # 判断用户是否登录
    if not user:
        current_app.logger.error("用户尚未登录")
        return jsonify(errno=RET.NODATA, errmsg="用户尚未登录")

    #3.1根据news_id 查询当前新闻对象
    try:
       news=News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询新闻对象异常")


    if not news:
        return jsonify(errno=RET.NODATA, errmsg="该新闻不存在")

    # 3.2 创建评论对象，并给各个属性赋值，保存回数据库
    comment_obj = Comment()
    comment_obj.user_id=user.id
    comment_obj.news_id=news.id
    comment_obj.content=comment


    if parent_id:
        # 代表是一条子评论
        comment_obj.parent_id = parent_id

    try:
        db.session.add(comment_obj)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="保存数据失败")

    return jsonify(errno=RET.OK, errmsg="发布评论成功", data=comment_obj.to_dict())








