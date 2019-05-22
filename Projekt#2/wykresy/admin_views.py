from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask_admin import AdminIndexView


class AuthMixin(object):
    def is_accessible(self):
        return current_user.is_authenticated


class AdminModelView(AuthMixin, ModelView):
    pass


class AdminIndex(AuthMixin, AdminIndexView):
    pass

