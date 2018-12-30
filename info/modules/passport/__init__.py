from flask import  Blueprint

passport_bp=Blueprint('possport',__name__,url_prefix='/passport')

from info.modules.passport.views import *