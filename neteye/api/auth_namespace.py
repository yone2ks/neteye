from flask import request
from flask_restx import Namespace, Resource, fields
from flask_security import login_user, logout_user, current_user, login_required
from flask_security.utils import verify_password

from neteye.extensions import api
from neteye.user.models import User

# Create auth namespace
auth_ns = Namespace('auth', description='Authentication operations')
api.add_namespace(auth_ns)

# Request/response models
login_model = auth_ns.model('Login', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

user_model = auth_ns.model('User', {
    'id': fields.Integer(description='User ID'),
    'email': fields.String(description='User email'),
    'username': fields.String(description='Username'),
    'active': fields.Boolean(description='Whether the user is active'),
    'roles': fields.List(fields.String, description='User roles')
})

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model, validate=True)
    @auth_ns.response(200, 'Login successful', user_model)
    @auth_ns.response(400, 'Invalid credentials')
    def post(self):
        """User login"""
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return {'message': 'Email and password are required'}, 400
            
        user = User.query.filter_by(email=email).first()
        
        if not user or not verify_password(password, user.password):
            return {'message': 'Invalid email or password'}, 400
            
        if not user.active:
            return {'message': 'Account is disabled'}, 403
            
        login_user(user)
        
        return {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'active': user.active,
            'roles': [role.name for role in user.roles]
        }

@auth_ns.route('/logout')
class Logout(Resource):
    @login_required
    def post(self):
        """User logout"""
        logout_user()
        return {'message': 'Successfully logged out'}

@auth_ns.route('/me')
class UserInfo(Resource):
    @login_required
    @auth_ns.marshal_with(user_model)
    def get(self):
        """Get current user info"""
        return {
            'id': current_user.id,
            'email': current_user.email,
            'username': current_user.username,
            'active': current_user.active,
            'roles': [role.name for role in current_user.roles]
        }
