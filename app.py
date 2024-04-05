"""
This module initializes the Flask application and imports the routes.
It also sets up the secret key for the application from an environment variable.
"""

from os import getenv
from flask import Flask


app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")


import routes
