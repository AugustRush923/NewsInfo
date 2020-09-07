from . import index_blu
from flask import render_template, current_app, session

from info.models import News, User, Category
from info import constants


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
