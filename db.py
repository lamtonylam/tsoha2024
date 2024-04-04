"""
This module sets up the database connection for the application using Flask-SQLAlchemy.
It reads the database URL from environment variables and configures the SQLAlchemy instance.
"""
from os import getenv
from flask_sqlalchemy import SQLAlchemy
from app import app

DATABASE_URL = getenv("DATABASE_URL")

FLY_DEPLOYMENT = getenv("FLY_DEPLOYMENT")

if FLY_DEPLOYMENT == "True":
    DATABASE_URL = DATABASE_URL.replace("://", "ql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
db = SQLAlchemy(app)

print("DATABASE_URL: ", DATABASE_URL)
