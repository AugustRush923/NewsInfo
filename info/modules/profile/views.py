from flask import g, redirect, render_template, request, session, current_app, jsonify, abort

from . import profile_blu
from info.utils.common import login_user_data
from info.utils.response_code import RET
from info import constants
from ... import db
from info.models import Category, News, User


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


@profile_blu.route("/news_release", methods=['GET', 'POST'])
@login_user_data
def news_release():
    if request.method == 'GET':
        # 获取分类信息
        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
        categories_dict = []
        for category in categories:
            categories_dict.append(category.to_dict())
        categories_dict.pop(0)
        return render_template('news/user_news_release.html', data={'categories': categories_dict})

    if request.method == 'POST':
        # 获取提交信息
        title = request.form.get("title")
        source = "个人发布"
        digest = request.form.get("digest")
        content = request.form.get("content")
        index_image = request.files.get("index_image")
        category_id = request.form.get("category_id")

        print(title, category_id, digest)
        print(content)
        # 判断提交信息是否完整
        if all([title, source, digest, content, category_id]):
            return jsonify(errno=RET.DATAERR, errmsg='数据不完整')

        # 更新新闻模型
        news = News()
        news.title = title
        news.category_id = category_id
        news.digest = digest
        news.content = content
        news.source = source
        news.user_id = g.user.id
        news.status = 1

        # 保存到数据库
        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

        return jsonify(errno=RET.OK, errmsg="提交成功,等待审核")


@profile_blu.route("/news_list")
@login_user_data
def news_list():
    # 获取页数
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    user = g.user
    news_li = []
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
        # 获取当前页数据
        news_li = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []

    for news_item in news_li:
        news_dict_li.append(news_item.to_review_dict())
    data = {"news_list": news_dict_li, "total_page": total_page, "current_page": current_page}
    return render_template('news/user_news_list.html', data=data)


@profile_blu.route('/user_follow')
@login_user_data
def user_follow():
    # 获取页数
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    # 取到当前登录用户
    user = g.user

    follows = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.followed.paginate(p, constants.USER_FOLLOWED_MAX_COUNT, False)
        # 获取当前页数据
        follows = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    user_dict_li = []

    for follow_user in follows:
        user_dict_li.append(follow_user.to_dict())

    data = {
        "users": user_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }

    return render_template('news/user_follow.html', data=data)


@profile_blu.route('/other_info')
@login_user_data
def other_info():
    user = g.user

    user_id = request.args.get("user_id")
    if not user_id:
        return abort(404)

    other = None
    try:
        other = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)

    if not other:
        abort(404)
    # 判断当前登录用户是否关注过该用户
    is_followed = False
    if g.user:
        if other.followers.filter(User.id == user.id).count() > 0:
            is_followed = True

    # 组织数据，并返回
    data = {
        "user_info": user.to_dict(),
        "other_info": other.to_dict(),
        "is_followed": is_followed
    }
    return render_template('news/other.html', data=data)


@profile_blu.route('/other_news_list')
def other_news_list():
    # 获取页数
    p = request.args.get("p", 1)
    user_id = request.args.get("user_id")
    print(p, user_id)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if not all([p, user_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(p, constants.OTHER_NEWS_PAGE_MAX_COUNT, False)
        # 获取当前页数据
        news_li = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    news_dict_li = []

    for news_item in news_li:
        news_dict_li.append(news_item.to_review_dict())
    data = {"news_list": news_dict_li, "total_page": total_page, "current_page": current_page}
    return jsonify(errno=RET.OK, errmsg="OK", data=data)
