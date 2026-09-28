import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)


class APIError(Exception):
    """Raise this from a route to send a JSON error to the client."""

    def __init__(self, message, status=400, fields=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.fields = fields or {}


def error_response(message, status, fields=None):
    body = {"message": message}
    if fields:
        body["fields"] = fields
    return jsonify(body), status


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(err):
        return error_response(err.message, err.status, err.fields)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return error_response(err.description or err.name, err.code)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        log.exception("Unhandled error")
        return error_response("Something went wrong on the server.", 500)
