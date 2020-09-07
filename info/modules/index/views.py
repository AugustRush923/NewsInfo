from . import index_blu
from flask import render_template, current_app, session, request, jsonify

from info.models import News, User, Category
from info import constants
from info.utils.response_code import RET


@index_blu.route('/')
def index():
    # 获取当前用户登录的ID
    user_id = session.get('user_id')
    # 通过ID获取用户信息
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    # 获取点击排行数据
    news_list = None
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
        print(news_list)
    except Exception as e:
        current_app.logger.error(e)

    click_news_list = []
    for news in news_list if news_list else []:
        click_news_list.append(news.to_basic_dict())

    # 获取分类数据
    categories = Category.query.all()
    print(categories)
    categories_dicts = []
    for category in categories:
        categories_dicts.append(category.to_dict())
    print(categories_dicts)
    data = {
        "user_info": user.to_dict() if user else None,
        "click_news_list": click_news_list,
        "categories": categories_dicts
    }

    return render_template('news/index.html', data=data)


@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


@index_blu.route("/news_list")
def new_list():
    """
       获取指定分类的新闻列表
       1. 获取参数
       2. 校验参数
       3. 查询数据
       4. 返回数据
       :return:
   """
    # 获取参数
    cid = request.args.get("cid")
    page = request.args.get('page', 1)
    per_page = request.args.get("per_page", constants.HOME_PAGE_MAX_NEWS)

    # 校验参数
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数")
    filters = [News.status == 0]
    if cid != 1:
        filters.append(News.category_id == cid)
    print(filters)

    # 查询数据
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
        # 获取查询出来的数据
        items = paginate.items
        # 获取到总页数
        total_page = paginate.pages
        current_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    news_li = []
    for news in items:
        news_li.append(news.to_basic_dict())

    print(news_li)
    data = {
        "total_page": total_page,
        "current_page": current_page,
        "news_dict_li": news_li
    }
    return jsonify(errno=RET.OK, errmsg="OK", data=data)