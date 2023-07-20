from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for
from flask_login import current_user


class UserView(ModelView):
    column_display_pk = True
    column_list = ['id', 'login', 'name']
    column_searchable_list = ('login', 'name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def is_accessible(self):
        if current_user.is_authenticated:
            return True
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('auth.login'))
