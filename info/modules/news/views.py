from flask import render_template, current_app, abort, g, request, jsonify

from . import news_blu
from info.models import News
from info import constants, db
from info.utils.response_code import RET
from info.utils.common import login_user_data


@news_blu.route("/<int:news_id>")
@login_user_data
def detail(news_id):
    # 判断是否收藏该新闻，默认值为 false
    is_collected = False
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
    mew_list = None
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
        click_news_list = []
        for rank_news in news_list if news_list else []:
            click_news_list.append(rank_news.to_basic_dict())
    except Exception as e:
        current_app.logger.error(e)

    if user:
        if news in user.collection_news:
            is_collected = True

    data = {
        "user_info": user.to_dict() if user else None,
        "news": news.to_dict(),
        "click_news_list": click_news_list,
        "is_collected": is_collected
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