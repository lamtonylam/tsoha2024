from flask import Flask
from flask import redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from os import getenv



app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")


import routes