from app import app
from flask_sqlalchemy import SQLAlchemy
from os import getenv

DATABASE_URL = getenv("DATABASE_URL")

FLY_DEPLOYMENT = getenv("FLY_DEPLOYMENT")

if FLY_DEPLOYMENT == "True":
    DATABASE_URL = DATABASE_URL.replace("://", "ql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
db = SQLAlchemy(app)

print("DATABASE_URL: ", DATABASE_URL)


