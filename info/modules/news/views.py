from info.modules.news import news_bp
from flask import render_template, session


@news_bp.route('/<int:news_id>')
def news_detail(news_id):
    """新闻详情页面展示"""

    data={}

    return render_template('news/detail.html',data=data)