from flask import Flask,session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from redis import StrictRedis
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand


class Config(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    SECRET_KEY = "HFDSEUUHSKH$#*(UIWOhdsj&^fhsue4jfi6se&*^jiJFDKJSIECVMNBQER"

    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    SESSION_TYPE = 'redis'
    SESSION_USE_SIGNE = True
    SESSION_REDIS=StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    PERMANENT_SESSION_LIFETIME = 86400


app = Flask(__name__)

app.config.from_object(Config)

db = SQLAlchemy(app)

CSRFProtect(app)


redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)

Session(app)
@app.route('/')
def index():
    return "hello world"





if  __name__ =='__main__':
       manager.run()