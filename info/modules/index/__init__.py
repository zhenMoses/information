from flask import Blueprint


index_bp=Blueprint("index",__name__,static_folder="../../static/news",static_url_path="")
from info.modules.index.views import *