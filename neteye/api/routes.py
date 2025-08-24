from neteye.blueprints import bp_factory
from flask import request, redirect, url_for, render_template, flash, session


api_bp = bp_factory("api")
