# init.py

from flask import Flask, redirect, url_for
# from flask_admin import Admin, expose, AdminIndexView
# from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'very_big+secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    #from .admin import UserView
    from .models import User
    #admin = Admin(app, name='Администрирование', template_mode='bootstrap3')

    #class Home(ModelView):
        #@expose('/')
        #def index(self):
            #return redirect(url_for('main.index'))

    #admin.add_view(UserView(User, db.session, name='Пользователи', category='База данных'))
    #admin.add_view(Home(User, db.session, name='Покинуть панель администратора'))

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .parser import update, send
    scheduler = BackgroundScheduler()
    scheduler.add_job(update, trigger="interval", seconds=60)
    scheduler.add_job(send, 'cron', hour=7, minute=00)
    scheduler.start()


    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    return app
