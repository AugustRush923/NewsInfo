from flask import render_template, request, jsonify, current_app, session, redirect, g, url_for

from . import admin_blu
from info.utils.response_code import RET
from info.models import User
from info.utils.common import login_user_data


@admin_blu.route("/login", methods=['GET', 'POST'])
def admin_login():
    if request.method == "GET":
        return render_template("admin/login.html")

    username = request.form.get('username')
    password = request.form.get('password')

    if not all([username, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    try:
        user = User.query.filter(User.mobile == username).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg="数据查询失败")

    if not user:
        return render_template('admin/login.html', errmsg="用户不存在")

    if not user.check_password(password):
        return render_template('admin/login.html', errmsg="密码错误")

    if not user.is_admin:
        return render_template('admin/login.html', errmsg="用户权限不够")

    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile
    session['is_admin'] = True

    return redirect(url_for("admin.admin_index"))


@admin_blu.route("/index")
@login_user_data
def admin_index():
    user = g.user
    if not user:
        return redirect(url_for("admin.admin_login"))
    if not user.is_admin:
        return redirect(url_for("admin.admin_login"))

    return render_template("admin/index.html", user=user)


