import logging

from flask import jsonify, render_template, request

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify(error=str(e)), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal server error")
        if request.path.startswith("/api/"):
            return jsonify(error="Internal server error"), 500
        return render_template("errors/500.html"), 500
