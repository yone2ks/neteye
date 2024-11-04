from logging import getLogger

from datatables import ColumnDT, DataTables
from flask import flash, jsonify, redirect,render_template, request, session, url_for
from flask_security import auth_required, roles_required, RegisterForm, hash_password

from neteye.extensions import db
from neteye.blueprints import bp_factory, root_bp
from neteye.user.models import user_datastore, admin_role, user_role, User, Role, RolesUsers

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

    
@user_bp.route('')
@roles_required('admin')
def index():
    return render_template('user/index.html')


@user_bp.route('/data')
@auth_required()
def data():
    columns = [
        ColumnDT(User.id),
        ColumnDT(User.email),
        ColumnDT(User.username),
        ColumnDT(Role.name),
        ColumnDT(User.active),
    ]
    query = db.session.query().select_from(User).join(RolesUsers).join(Role)
    params = request.args.to_dict()
    row_table = DataTables(params, query, columns)
    return jsonify(row_table.output_result())


@user_bp.route('/<id>')
@auth_required()
def show(id):
    user = User.query.get(id)
    return render_template('user/show.html', user=user)


@user_bp.route('/<id>/delete', methods=['POST'])
@auth_required()
def delete(id):
    user = User.query.get(id)
    user.delete()
    return redirect(url_for("user.index"))