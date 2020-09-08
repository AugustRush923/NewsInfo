from flask import g, redirect, render_template, request, session, current_app, jsonify

from . import profile_blu
from info.utils.common import login_user_data
from info.utils.response_code import RET
from info import constants
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


@profile_blu.route("/change_password", methods=["GET", "POST"])
@login_user_data
def change_password():
    user = g.user
    if request.method == 'GET':
        return render_template("news/user_pass_info.html")
    if request.method == 'POST':
        old_password = request.json.get('old_password')
        new_password = request.json.get('new_password')
        if not all([old_password, new_password]):
            return jsonify(errno=RET.DATAERR, errmsg="参数错误")

        if not user.check_password(old_password):
            return jsonify(errno=RET.USERERR, errmsg="原密码错误")

        user.password_hash = user.sha1_passowrd(new_password)
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存失败")

        return jsonify(errno=RET.OK, errmsg="更改密码成功")


@profile_blu.route("/collection")
@login_user_data
def collection():
    p = request.args.get('p', 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1
    user = g.user
    collect_list = []
    current_page = 1
    total_page = 1

    try:
        paginate = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
        collections = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    for news in collections:
        collect_list.append(news.to_basic_dict())
    data = {
        'collections': collect_list,
        'current_page': current_page,
        'total_page': total_page
    }
    return render_template("news/user_collection.html", data=data)