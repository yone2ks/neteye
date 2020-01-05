from neteye.blueprints import bp_factory
from flask import request, redirect, url_for, render_template, flash, session


base_bp = bp_factory("base")


@base_bp.route("/")
def index():
    return render_template("index.html")


@base_bp.route("/<path>")
def template(path):
    return render_template(path)


@base_bp.route("/<directory>/<path>")
def subdir_template(directory, path):
    return render_template(directory + "/" + path)
