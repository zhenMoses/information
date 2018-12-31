from datetime import datetime
import re
from flask import request, abort, current_app, make_response, jsonify, session
from info.utils.captcha.captcha.captcha import captcha
from . import passport_bp
from info import redis_store,db
from info import constants
from info.response_code import RET
from info.models import User
from info.lib.yuntongxun.sms import CCP


@passport_bp.route('/image_code')
def get_image_code():
    """
        1.获取参数
            1.1 code_id： UUID通用的唯一编码，作为key将验证码真实值存储到redis数据库
        2.校验参数
            2.1 非空判断code_id不能为空
        3.逻辑处理
            3.1 生成验证码图片，验证码图片的真实值
            3.2 code_id作为key将验证码图片的真实值保存到redis数据库，并且设置有效时长(5分钟)
        4.返回值
            4.1 返回验证码图片
        """
    code_id=request.args.get('code_id')

    if not code_id:
        current_app.logger.debug("参数不足")
        abort(404)


    image_name, real_image_code, image_data = captcha.generate_captcha()

    try:
        redis_store.setex("CODEID_%s" % code_id,constants.IMAGE_CODE_REDIS_EXPIRES,real_image_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='保存图片验证码失败')


    resp=make_response(image_data)
    resp.headers["Content-Type"] ='image/JPEG'
    return resp



@passport_bp.route('/sms_code',methods=['POST'])
def send_sms_code():
    """短信验证码后端接口"""
    """
        1.获取参数
            1.获取手机:mobile,图片验证码:image_code,image_code_id:UUID编号
        2.校验参数
            1.1进行非空判断
            1.2对手机号码进行正则判断
        3.逻辑处理
            3.1根据image_code去获取redis数据库存在的图片验证码的值real_image_code
              3.1.1 real_image_code没有值:图片验证码过期了
              3.1.2 real_image_code 有值,删除redis数据库的值,防止多次使用同一个验证码来进行多次验证码
              
            3.2 判断image_code 和real_image_code 两个值是否一致
                3.2.1 不一致: 提示图片验证码错误
                3.2.2 一致:发送短信验证码
            # TODO :检验用户是否存在
            3.3发送短信流程
                3.1.1 生成6位随机数字
                3.1.2  调用CCP类中方法发送短信验证码
+               3.3.3 发送短信验证码失败：提示前端重新发送
+               3.3.4 将6位的短信验证码值使用redis数据库保存起来，设置有效时长（方便注册接口获取真实的短信验证值
        4.返回结果
    
    
    """
#     1.获取参数
#             1.获取手机:moblie,图片验证码:image_code,image_code_id:UUID编号
    param_dict=request.json

    mobile=param_dict.get('mobile')
    image_code=param_dict.get('image_code')
    image_code_id=param_dict.get('image_code_id')


    #1.1进行非空判断
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不足")
    #1.2对手机号码进行正则判断
    if not re.match('1[3456789][0-9]{9}$',mobile):
        current_app.logger.error("手机格式错误")
        return jsonify(errno=RET.PARAMERR,errmsg="手机格式错误")


    # 3.1根据image_code去获取redis数据库存在的图片验证码的值real_image_code
    try:
        real_image_code=redis_store.get("CODEID_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg="获取真实的图片验证码错误")

    #3.1.1 real_image_code没有值:图片验证码过期了
    if not real_image_code:
        return jsonify(errno=RET.NODATA,errmsg='数据不存在')

    #3.1.2 real_image_code 有值,删除redis数据库的值,防止多次使用同一个验证码来进行多次验证码
    else:
        try:
            redis_store.delete("CODEID_%s" % image_code_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="删除真实的图片验证码异常")

    # 3.2 判断image_code 和real_image_code 两个值是否一致
    # 3.2.1 不一致: 提示图片验证码错误
    if  image_code.lower() !=real_image_code.lower():
        return jsonify(errno=RET.DATAERR,errmsg='图片验证码不匹配')

    #3.2.2 一致:发送短信验证码
    # 判断用户是否存在
    try:

        user=User.query.filter(User.mobile==mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询异常")

    if user:
        return jsonify(errno=RET.DATAEXIST,errmsg="用户已存在")

    #3.1.1 生成6位随机数字
    import random
    # 不足6位,前面补零
    sms_code=random.randint(0,999999)
    sms_code="%06d" % sms_code

    #3.1.2  调用CCP类中方法发送短信验证码
    result=CCP().send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)
    #3.3.3 发送短信验证码失败：提示前端重新发送
    if result ==-1:
        return jsonify(errno=RET.THIRDERR,errmsg="第三方系统出错")
    # 3.3.4 将6位的短信验证码值使用redis数据库保存起来，设置有效时长（方便注册接口获取真实的短信验证值
    elif result == 0:
        redis_store.setex("SMS_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

    return  jsonify(errno=RET.OK,errmsg="发送验证码成功")



@passport_bp.route('/register',methods=['POST'])
def register():
    """注册后端接口的实现"""
    """
    1.获取参数
    1.1 手机号码 mobile  手机验证码:sms_code 未加密的密码:password s数据格式:json
    2.校验参数
        2.1非空判断
        2.2手机号码正在验证
    3.逻辑处理
        3.1 根据sms_code去和redis 的值real_sms_code进行比较
            3.1.1 real_sms_code 有值:删除redis数据库中删除
            3.1.2 real_sms_code 无值: 验证码过期了,重新发送
        3.2 判断sms_code 和real_sms_code 是否一致
            3.2.1 不一致:提示验证码错误
            3.2.1  一致:注册
        3.3 创建用户对象,并给各个属相赋值
        3.4 保存用户信息到数据库,并进行用户密码加密
        3.5 注册成功代表登录成功，记录用户登录信息到sesssion中
            
    4.返回值
    """
    #1.1 手机号码 mobile  手机验证码:sms_code 未加密的密码:password s数据格式:json
    param_dict=request.json
    mobile=param_dict.get('mobile')
    sms_code=param_dict.get('sms_code')
    password=param_dict.get('password')

    #2.1非空判断
    if not all([mobile,sms_code,password]):
        current_app.logger.error("参数不足")
        return jsonify(errno=RET.PARAMERR,errmsg="参数不足")
    # 2.2手机号码正在验证
    if not re.match('1[3456789][0-9]{9}$',mobile):
        current_app.logger.error("手机格式错误")
        return jsonify(errno=RET.DATAERR,errmsg="手机格式错误")


    # 3.1 根据sms_code去和redis 的值real_sms_code进行比较
    try:
        real_sms_code=redis_store.get("SMS_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取用户对象异常")

    # 3.1.1 real_sms_code 有值:删除redis数据库中删除
    if real_sms_code:
        redis_store.delete("SMS_%s" % mobile)
        # 3.1.2 real_sms_code 无值: 验证码过期了,重新发送
    else:
        current_app.logger.error("短信验证码过期")
        return jsonify(essno=RET.NODATA,errmsg="短信验证码过期")


    # 3.2 判断sms_code 和real_sms_code 是否一致
    # 3.2.1 不一致:提示验证码错误
    if sms_code != real_sms_code:
        current_app.logger.error("短信验证码错误")
        return jsonify(errno=RET.DATAERR,errmsg="短信验证码错误")
    # 3.2.1  一致:注册
    # 3.3 创建用户对象,并给各个属相赋值
    user =User()

    user.mobile= mobile
    user.nick_name=mobile
    user.last_login=datetime.now()
    user.password=password

    # 3.4 保存用户信息到数据库,并进行用户密码加密
    # 数据存储之前对password进行加密处理
    user.set_hashpasswd(password)
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 数据库进行回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="添加用户信息异常")

    # 3.5 注册成功代表登录成功，记录用户登录信息到sesssion中
    session['user_id'] = user.id
    session['user_mobile'] = user.mobile
    session['nick_name'] = user.nick_name

    # 注册成功
    return jsonify(errno=RET.OK,errmsg="注册成功")


@passport_bp.route('/login', methods=['POST'])
def login():
    """登陆接口的实现"""
    """
        1.获取参数
            1.1获取手机号monile 密码:password
            
        2.检验参数
            2.1 不能为空
            2.2手机正则判断
        3.逻辑处理
            3.1 根据手机号码去查询当前用户user
+           3.2 使用user对象判断用户填写的密码是否跟数据库里的一致
+            3.3 使用session记录用户登录信息
+           3.4 修改用户最后一次登录时间
        4.返回值
    
    
    """
    # 1.1获取手机号mobile 密码:password
    param_dict = request.json

    mobile = param_dict.get('mobile')
    password = param_dict.get('password')

    # 2.1 不能为空
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不足")
    # 2.2手机正则判断
    if not re.match('1[3456789][0-9]{9}$', mobile):
        current_app.logger.error("手机格式错误")
        return jsonify(errno=RET.PARAMERR,errmsg="手机格式错误")

    try:
        # 3.1 根据手机号码去查询当前用户user
        user=User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询用户信息异常")

    if not user:
        return jsonify(errno=RET.NODATA,errmsg="查询数据不存在")

    # 3.2 使用user对象判断用户填写的密码是否跟数据库里的一致
    if not user.check_passowrd(password):
        return jsonify(errno=RET.DATAERR,errmsg="密码填写错误")

    # 3.3 使用session记录用户登录信息
    session['user_id'] = user.id
    session['user_mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    # 3.4 修改用户最后一次登录时间
    user.last_login = datetime.now()
    # 保存到数据库
    try:
        # 如果是修改不需要再add只需要提交修改即可
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DATAERR,errmsg="用户信息异常")

    return jsonify(errno=RET.OK, errmsg="登陆成功")
