from flask import  request,abort,current_app,make_response,jsonify
from info.utils.captcha.captcha.captcha import captcha
from . import passport_bp
from  info import redis_store
from info import constants


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


    resp=make_response(image_data)
    resp.headers["Content-Type"] ='image/JPEG'
    return resp
