from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin
from .admin_views import AdminModelView

import hashlib

ROZMIARY=(15,10)

db_file_name = "db/oferty.db"

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'infosharepythonsredniozaawansowany2019'
app.config['PANDAS_DATABASE_URI'] = 'sqlite:///%s/%s' % (__name__, db_file_name)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % (db_file_name)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
from . import models
db.create_all()

all_user_rows = models.User.query.count()
if all_user_rows == 0:
    user = models.User()
    user.login = 'Jan'

    password = 'Nowak'
    user.password = hashlib.md5(password.encode()).hexdigest()
    db.session.add(user)
    db.session.commit()


from . import views

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(models.User).get(user_id)

admin = Admin(app, name='Projekt#2')
admin.add_view(AdminModelView(models.Oferty, db.session))
admin.add_view(AdminModelView(models.Kampanie, db.session))
admin.add_view(AdminModelView(models.Portale, db.session))
admin.add_view(AdminModelView(models.User, db.session))
