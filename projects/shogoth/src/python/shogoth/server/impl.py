#!/usr/bin/env python3

"""The implementation of a Shogoth evaluation server."""

import flask


app = flask.Flask(__name__)

@app.route("/api/v0/login", method=["POST"])
def login():
    pass


@app.route("/api/v0/logout", method=["POST"])
def logout():
    pass


@app.route("/api/v0/session", method=["GET"])
def get_session():
    pass

@app.route("/api/v0/session", method=["POST"])
def make_session():
    pass
