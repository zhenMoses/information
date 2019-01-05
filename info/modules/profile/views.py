from info import  db
from info.modules.profile import profile_bp
from flask import jsonify, render_template, g, request, redirect, current_app, session
from info.utils.common import get_user_data
from info.response_code import RET


@profile_bp.route('/user')
@get_user_data
def user_info():
    """个人中心页面"""
    user=g.user

    if not user:
        return redirect('/')
    data={
        "user_info": user.to_dict() if user else None
    }
    return render_template('profile/user.html', data=data)



# 修改签名和昵称,并返回
@profile_bp.route('/base_info',methods=['GET','POST'])
@get_user_data
def base_info():
    """用户基本资料页面"""
    user = g.user
    # GET请求：返回模板页面，展示基本用户资料
    if request.method == "GET":

        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template('profile/user_base_info.html', data=data)


    # POST请求:修改修改用户基本资料


    """
        1.获取参数
            user:当前用户,nick_name:昵称,gender:性别
        2.检验参数
            2.1 非空判断
            2.2 gender in [MAN / WOMEN]
        3.逻辑处理
            将当前用户各个属性重新赋值 ，保存到数据库即可
        4.返回值
            
    """
    params_dict=request.json
    nick_name=params_dict.get('nick_name')
    signature=params_dict.get('signature')
    gender=params_dict.get('gender')

    if not all([nick_name, signature, gender]):

        current_app.logger.error("参数不足")
        return jsonify(errno=RET.PARAMERR,errmsg='参数不足')

    if gender not  in ['MAN', 'WOMEN']:
        current_app.logger.error("参数错误")
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 3.0 将当前用户各个属性重新赋值 ，保存到数据库即可
    user.signature=signature
    user.nick_name=nick_name
    user.gender=gender
    # 注意：修改了nick_name，会话对象中数据也要调整
    session['nick_name']=nick_name


    # 将上述修改操作保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="保存数据失败")

    return jsonify(errno=RET.OK, errmsg="修改用户基本数据成功")


# 用户头像 设置
@profile_bp.route('/pic_info',methods=['GET','POST'])
@get_user_data
def pic_info():
    if request.method=='GET':
        return render_template('profile/user_pic_info.html')
