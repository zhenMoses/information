import re
from flask import  request,abort,current_app,make_response,jsonify
from info.utils.captcha.captcha.captcha import captcha
from . import passport_bp
from  info import redis_store
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

