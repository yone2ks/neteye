from neteye.blueprints import bp_factory
from flask import request, redirect, url_for, render_template, flash, session


base_bp = bp_factory('base')

@base_bp.route('/')
def index():
    return render_template('index.html')
