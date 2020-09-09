from datetime import datetime

from flask import current_app, jsonify, session
from flask import make_response
from flask import request, redirect
from flask_wtf.csrf import generate_csrf

from info import constants, db
from info import redis_store
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blu
from info.models import User


@passport_blu.after_request
def add_csrf2front(response):
    csrf_token = generate_csrf()
    print(csrf_token)
    response.set_cookie('csrf_token', csrf_token)
    return response


@passport_blu.route("/image_code")
def image_code():
    # 1. 获取到当前的图片编号id
    code_id = request.args.get('imageCodeId')
    print(code_id)
    # 2. 生成验证码
    name, text, image = captcha.generate_captcha()
    print(name, text, image)
    # 保存当前生成的图片验证码内容
    try:
        redis_store.setex('ImageCode_' + code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return make_response(jsonify(errno=RET.DATAERR, errmsg='保存图片验证码失败'))

    # 返回响应内容
    resp = make_response(image)
    # 设置内容类型
    resp.headers['Content-type'] = "image/jpg"
    return resp


@passport_blu.route("/register", methods=["POST"])
def register():
    """
       1. 获取参数和判断是否有值
       2. 从redis中获取指定手机号对应的短信验证码的
       3. 校验验证码
       4. 初始化 user 模型，并设置数据并添加到数据库
       5. 保存当前用户的状态
       6. 返回注册的结果
       :return:
       """
    # 1. 获取账号密码
    json_data = request.json
    print(json_data)
    mobile = json_data.get('mobile')
    password = json_data.get('password')

    # 2. 判断是否有值
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 4. 初始化 user 模型，并设置数据并添加到数据库
    user = User()
    user.nick_name = mobile
    user.mobile = mobile
    # 对密码进行处理
    user.password_hash = user.sha1_passowrd(password)

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        # 数据保存错误
        return jsonify(errno=RET.DATAERR, errmsg="数据保存错误")
    # 5. 保存用户登录状态
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile

    # 6. 返回注册结果
    return jsonify(errno=RET.OK, errmsg="OK")


@passport_blu.route('/login', methods=["POST"])
def login():
    """
    1. 获取参数和判断是否有值
    2. 从数据库查询出指定的用户
    3. 校验密码
    4. 保存用户登录状态
    5. 返回结果
    :return:
    """

    # 1. 获取参数和判断是否有值
    json_data = request.json

    mobile = json_data.get("mobile")
    password = json_data.get("password")
    print(mobile, password)
    if not all([mobile, password]):
        # 参数不全
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 2. 从数据库查询出指定的用户
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据错误")

    if not user:
        return jsonify(errno=RET.USERERR, errmsg="用户不存在")

    # 3. 校验密码
    if not user.password_hash == user.sha1_passowrd(password):
        return jsonify(errno=RET.PWDERR, errmsg="密码错误")

    # 4. 保存用户登录状态
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    # 记录用户最后一次登录时间
    user.last_login = datetime.now()
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
    # 5. 登录成功
    return jsonify(errno=RET.OK, errmsg="OK")


@passport_blu.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('nick_name', None)
    session.pop('mobile', None)
    session.pop('is_admin', None)
    return redirect("/")
