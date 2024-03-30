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
    query = text('SELECT id, name FROM Patches;')
    result = db.session.execute(query)
    results = result.fetchall()

    user_id = users.user_id()
    query = text("SELECT Patches.name, UsersToPatches.sent_at, UsersToPatches.merkki_id \
                FROM Patches, UsersToPatches \
                WHERE Patches.id = UsersToPatches.merkki_id AND UsersToPatches.user_id = :user_id;")
    own_patches_result = db.session.execute(query, {"user_id": user_id})
    return render_template("kirjautunut.html", results=results, own_patches_result=own_patches_result)

@app.route("/merkki/<int:id>")
def merkki(id):
    query = text('SELECT name FROM Patches WHERE id = :id;')
    result = db.session.execute(query, {"id": id})
    nimi = result.fetchone()[0]
    return render_template("merkki.html", nimi=nimi, id=id)

# adding a patch from general collection to user's own collection
@app.route("/send/new/to_collection", methods=["POST"])
def to_collection():
    merkki_id = request.form["id"]
    user_id = users.user_id()
    sql = text("INSERT INTO UsersToPatches (merkki_id, user_id, sent_at) VALUES (:merkki_id, :user_id, NOW())")
    db.session.execute(sql, {"merkki_id": merkki_id, "user_id": user_id})
    db.session.commit()
    return redirect("/kirjautunut")

# adding patch to general collection for everyone to see
@app.route("/new/merkki")
def new():
    return render_template("new_merkki.html")

@app.route("/send/new/merkki", methods=["POST"])
def send():
    name = request.form.get("nimi")
    sql = text("INSERT INTO Patches(name) VALUES (:name)")  
    db.session.execute(sql, {"name": name})
    db.session.commit()
    return redirect("/kirjautunut")


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