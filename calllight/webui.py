"""
Flask Web UI.
"""

from __future__ import annotations

from flask import Flask
from flask import jsonify
from flask import render_template


def create_web_app(calllight) -> Flask:
    """
    Create the Flask application.
    """

    app = Flask(
        __name__,
        template_folder="templates",
    )

    @app.route("/")
    def index():

        return render_template(
            "index.html",
            status=calllight.status(),
        )

    @app.route("/api/status")
    def api_status():

        return jsonify(calllight.status())

    @app.route("/health")
    def health():

        return {
            "status": "ok"
        }

    return app
