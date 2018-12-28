from flask import Blueprint


index_bp=Blueprint("index",__name__)
from info.modules.index.views import *