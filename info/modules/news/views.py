from flask import render_template, current_app, abort, g, request, jsonify
from flask_wtf.csrf import generate_csrf

from . import news_blu
from info.models import News, Comment, CommentLike, Category
from info import constants, db
from info.utils.response_code import RET
from info.utils.common import login_user_data


@news_blu.after_request
def add_csrf2front(response):
    csrf_token = generate_csrf()
    print(csrf_token)
    response.set_cookie('csrf_token', csrf_token)
    return response


@news_blu.route("/<int:news_id>")
@login_user_data
def detail(news_id):
    # 获取用户信息
    user = g.user

    # 查询新闻数据
    try:
        news = News.query.get(news_id)
        news.clicks += 1

    except Exception as e:
        current_app.logger.error(e)
        abort(404)

    # 获取点击排行数据
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
        click_news_list = []
        for rank_news in news_list if news_list else []:
            click_news_list.append(rank_news.to_basic_dict())
    except Exception as e:
        current_app.logger.error(e)

    # 获取当前新闻的评论
    comments = None
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    comment_like_ids = []
    if user:
        # 如果当前用户已登录
        try:
            comment_ids = [comment.id for comment in comments]
            if len(comment_ids) > 0:
                # 取到当前用户在当前新闻的所有评论点赞的记录
                comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                         CommentLike.user_id == g.user.id).all()
                # 取出记录中所有的评论id
                comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]
        except Exception as e:
            current_app.logger.error(e)

    comment_list = []
    for item in comments if comments else []:
        comment_dict = item.to_dict()
        comment_dict["is_like"] = False
        # 判断用户是否点赞该评论
        if g.user and item.id in comment_like_ids:
            comment_dict["is_like"] = True
        comment_list.append(comment_dict)
    # 判断是否收藏该新闻，默认值为 false
    is_collected = False
    if user:
        if news in user.collection_news:
            is_collected = True

    categories = Category.query.all()
    categories_dicts = []
    for category in categories:
        categories_dicts.append(category.to_dict())

    data = {
        "user_info": user.to_dict() if user else None,
        "news": news.to_dict(),
        "click_news_list": click_news_list,
        "is_collected": is_collected,
        'comments': comment_list,
        'categories': categories_dicts
    }
    return render_template("news/detail.html", data=data)


@news_blu.route("/news_collect", methods=['POST'])
@login_user_data
def news_collect():
    """新闻收藏"""
    # 获取数据
    user = g.user
    json_data = request.json
    news_id = json_data.get("news_id")
    action = json_data.get("action")

    # 校验数据
    if user is None:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    if news_id is None:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if action is None:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if news is None:
        return jsonify(errno=RET.NODATA, errmsg="新闻数据不存在")

    if action == "collect":
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存失败")
    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blu.route("/news_comment", methods=['POST'])
@login_user_data
def news_comment():
    user = g.user
    if user is None:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 获取数据
    json_data = request.json
    news_id = json_data.get('news_id')
    comment = json_data.get('comment')
    parent_id = json_data.get('parent_id')
    print(news_id, comment, parent_id)

    # 检验数据
    if not all([news_id, comment]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="数据不存在")

    # 初始化模型，保存数据
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment
    if parent_id:
        comment.parent_id = parent_id

    # 保存到数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存评论数据失败")

    # 返回响应
    return jsonify(errno=RET.OK, errmsg="评论成功", data=comment.to_dict())


@news_blu.route("/comment_like", methods=['POST'])
@login_user_data
def comment_like():
    user = g.user
    comment_id = request.json.get("comment_id")
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    if not all([comment_id, news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if action not in ("add", "remove"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    # 查询评论数据
    try:
        comment = Comment.query.get('comment_id')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论数据不存在")

    if action == "add":
        comment_like = CommentLike.query.filter_by(comment_id=comment_id, user_id=g.user.id).first()
        if not comment_like:
            comment_like = CommentLike()
            comment_like.comment_id = comment_id
            comment_like.user_id = g.user.id
            db.session.add(comment_like)
            # 增加点赞条数
            comment.like_count += 1
    else:
        # 删除点赞数据
        comment_like = CommentLike.query.filter_by(comment_id=comment_id, user_id=g.user.id).first()
        if comment_like:
            db.session.delete(comment_like)
            # 减小点赞条数
            comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")
    return jsonify(errno=RET.OK, errmsg="操作成功")