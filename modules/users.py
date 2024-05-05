"""
This module contains functions for user login, logut, register and user rights management.
"""

from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import text
import secrets

from flask import flash, redirect, render_template


def handle_login(request):
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if login(username, password):
            flash("Kirjautuminen onnistui", "success")
            return redirect("/")
        else:
            return render_template(
                "login.html", message="Väärä tunnus tai salasana", username=username
            )


def login(username, password):
    sql = text("SELECT id, password, username FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()
    if not user:
        return False
    else:
        if check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["csrf_token"] = secrets.token_hex(16)
            return True
        else:
            return False


def logout():
    try:
        del session["username"]
        del session["user_id"]
        del session["csrf_token"]
        flash("Olet kirjautunut ulos onnistuneesti", "success")
        return redirect("/")
    except Exception as e:
        print(e)
        flash("Uloskirjautuminen ei onnistunut", "error")


def handle_register(request):
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form["username"]
        if len(username) < 1 or len(username) > 20:
            return render_template(
                "register.html",
                message="Käyttäjätunnuksen tulee olla 1-20 merkkiä pitkä",
                username=username,
            )
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return render_template(
                "register.html", message="Salasanat eroavat", username=username
            )
        if len(password1) < 8 or len(password1) > 20:
            return render_template(
                "register.html",
                message="Salasanan tulee olla 8-20 merkkiä pitkä,",
                username=username,
            )
        if register(username, password1):
            flash("Rekisteröinti onnistui", "success")
            return redirect("/")
        else:
            return render_template(
                "register.html",
                message="Rekisteröinti ei onnistunut",
                username=username,
            )


def register(username, password):
    hash_value = generate_password_hash(password)
    try:
        sql = text(
            "INSERT INTO users (username, password) VALUES (:username, :password)"
        )
        db.session.execute(sql, {"username": username, "password": hash_value})
        db.session.commit()
    except Exception as e:
        print(e)
        return False
    return login(username, password)


def user_id():
    return session.get("user_id", 0)


def get_username():
    return session.get("username", "")
