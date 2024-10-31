from logging import getLogger

from flask import flash, redirect, render_template, request, session, url_for
from flask_security import auth_required, roles_required, RegisterForm, hash_password

from neteye.blueprints import bp_factory, root_bp
from neteye.user.models import user_datastore, admin_role, user_role

logger = getLogger(__name__)

user_bp = bp_factory("user")

@root_bp.route('/register', methods=['GET', 'POST'])
@user_bp.route('/register', methods=['GET', 'POST'])
@roles_required('admin')
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = user_datastore.create_user(
            email=form.email.data,
            username=form.email.data,
            password=hash_password(form.password.data),
            active=True,
            roles=[admin_role]
        )
        user.add()
        flash('User registered successfully.', 'success')
        return redirect(url_for(".index")) 
    return render_template('user/register.html', register_user_form=form)