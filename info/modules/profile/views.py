from flask import g, redirect, render_template, request, session, current_app, jsonify

from . import profile_blu
from info.utils.common import login_user_data
from info.utils.response_code import RET
from ... import db


@profile_blu.route("/info")
@login_user_data
def user_profile():
    user = g.user
    if not user:
        return redirect('/')

    data = {
        'user_info': user.to_dict(),
    }
    return render_template("news/user.html", data=data)


@profile_blu.route("/user_info", methods=["GET", "POST"])
@login_user_data
def user_info():
    """
        用户基本信息
        1. 获取用户登录信息
        2. 获取到传入参数
        3. 更新并保存数据
        4. 返回结果
        :return:
    """
    user = g.user
    if request.method == 'GET':
        data = {
            'user': user.to_dict()
        }
        return render_template("news/user_base_info.html", data=data)

    if request.method == 'POST':
        nick_name = request.json.get('nick_name')
        signature = request.json.get('signature')
        gender = request.json.get('gender')
        
        if not all([nick_name, signature, gender]):
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

        if gender not in ['MAN', 'WOMAN']:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        user.nick_name = nick_name
        user.signature = signature
        user.gender = gender

        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DATAERR, errmsg="保存失败")

        session['nick_name'] = nick_name

        return jsonify(errno=RET.OK, errmsg="更新成功")