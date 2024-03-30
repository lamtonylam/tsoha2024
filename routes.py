from app import app
from flask import render_template, request, redirect
from flask import session
import users
from sqlalchemy.sql import text
from db import db


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/kirjautunut")
def kirjautnut():
    query = text('SELECT id, nimi FROM Merkit;')
    result = db.session.execute(query)
    results = result.fetchall()
    return render_template("kirjautunut.html", results=results)

@app.route("/merkki/<int:id>")
def merkki(id):
    query = text('SELECT nimi FROM Merkit WHERE id = :id;')
    result = db.session.execute(query, {"id": id})
    nimi = result.fetchone()[0]
    return render_template("merkki.html", nimi=nimi)


@app.route("/new/merkki")
def new():
    return render_template("new_merkki.html")

@app.route("/send/new/merkki", methods=["POST"])
def send():
    nimi = request.form.get("nimi")
    sql = text("INSERT INTO Merkit(nimi) VALUES (:nimi)")  
    db.session.execute(sql, {"nimi": nimi})
    db.session.commit()
    return redirect("/kirjautunut")

@app.route("/register", methods=["GET"])
def register_get():
    return render_template("register.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return render_template("error.html", message="Salasanat eroavat")
        if users.register(username, password1):
            return redirect("/")
        else:
            return render_template("error.html", message="Rekisteröinti ei onnistunut")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if users.login(username, password):
            return redirect("/")
        else:
            return render_template("error.html", message="Väärä tunnus tai salasana")

@app.route("/logout")
def logout():
    users.logout()
    return redirect("/")