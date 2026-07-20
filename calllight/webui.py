"""
Flask Web UI.

The web button is a full virtual button: it goes through exactly
the same press handling as the hardware button, so the sound desk
can raise and clear Calls like anyone on stage.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request

from . import updater


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def create_web_app(calllight) -> Flask:
    """
    Create the Flask application.
    """

    app = Flask(
        __name__,
        template_folder=str(TEMPLATE_DIR),
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

    @app.route("/api/peers")
    def api_peers():

        return jsonify(calllight.peer_snapshot())

    @app.route("/api/events")
    def api_events():

        return jsonify(calllight.event_snapshot())

    @app.route("/api/overview")
    def api_overview():

        #
        # One call for the polling UI.
        #

        return jsonify({
            "status": calllight.status(),
            "peers": calllight.peer_snapshot(),
            "events": calllight.event_snapshot(),
        })

    @app.route("/api/press", methods=["POST"])
    def api_press():

        event_type = calllight.press("web")

        return jsonify({"event": event_type})

    @app.route("/api/settings")
    def api_settings():

        return jsonify(calllight.settings())

    @app.route("/api/settings", methods=["POST"])
    def api_settings_update():

        body = request.get_json(silent=True) or {}

        changed = calllight.update_settings(
            display_name=body.get("display_name"),
            flash_rate_ms=body.get("flash_rate_ms"),
            led_brightness=body.get("led_brightness"),
        )

        return jsonify({
            "changed": changed,
            "settings": calllight.settings(),
        })

    @app.route("/api/update/check")
    def api_update_check():

        return jsonify(updater.check_for_update())

    @app.route("/api/update", methods=["POST"])
    def api_update():

        return jsonify(updater.start_update(calllight.logger))

    @app.route("/health")
    def health():

        return {
            "status": "ok"
        }

    return app
