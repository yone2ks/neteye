from flask import request, redirect, url_for, render_template, flash, session
from flask_restx import Resource
from flask_security import auth_required

from neteye.blueprints import bp_factory


api_bp = bp_factory("api")


class AuthenticatedResource(Resource):
    """Flask-RestX Resource base class that requires a valid login session.

    Inherit from this instead of ``Resource`` for any endpoint that must be
    protected.  ``/api/auth/login`` (and similar public auth endpoints) should
    continue to inherit directly from ``Resource``.
    """
    method_decorators = [auth_required("session", "token")]
