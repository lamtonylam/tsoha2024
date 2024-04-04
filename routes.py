from app import app
from flask import render_template, request, redirect
from flask import session
import users
from sqlalchemy.sql import text
from db import db
from flask import make_response

# import base64 for image encoding
import base64

# pillow image compression
from PIL import Image
from io import BytesIO

# for random texts in index.html
import random_text_generator

# module import for sending patches into general collection
import sendpatch

@app.route("/")
def index():
    # get previously displayed text
    previous_text = session.get("random_text")
    # get a new random text
    random_text = random_text_generator.generate_random_text(previous_text)
    # save the new text to session
    session["random_text"] = random_text

    return render_template("index.html" , random_text = random_text)

@app.route("/kirjautunut")
def kirjautnut():
    # if user is not logged in dont run sqls etc.
    if users.get_username() == "":
        return render_template("kirjautunut.html")

    query = text('SELECT id, name FROM Patches;')
    result = db.session.execute(query)
    results = result.fetchall()

    user_id = users.user_id()
    query = text("SELECT Patches.name, UsersToPatches.sent_at, UsersToPatches.patch_id \
                FROM Patches, UsersToPatches \
                WHERE Patches.id = UsersToPatches.patch_id AND UsersToPatches.user_id = :user_id;")
    own_patches_result = db.session.execute(query, {"user_id": user_id})
    return render_template("kirjautunut.html", results=results, own_patches_result=own_patches_result)

@app.route("/merkki/<int:id>")
def merkki(id):
    # Fetch patch name and user id of the patch
    query_patch = text('SELECT name, created_by_user FROM Patches WHERE id = :id;')
    result_patch = db.session.execute(query_patch, {"id": id})
    row = result_patch.fetchone()
    patch_name = row[0]
    created_by_user = row[1]

    # Fetch image data
    query_image = text("SELECT data FROM images WHERE patch_id=:patch_id")
    result_image = db.session.execute(query_image, {"patch_id": id})
    try:
        data = result_image.fetchone()[0] if result_image else None
    except:
        data = None

    # If image data is found, encode it to base64 and pass it to the template
    if data is not None:
        response = base64.b64encode(data).decode("utf-8")
        return render_template("merkki.html", nimi=patch_name, created_by_user = created_by_user, id=id, photo=response)

    return render_template("merkki.html", nimi=patch_name, created_by_user = created_by_user, id=id)


# adding a patch from general collection to user's own collection
@app.route("/send/new/to_collection", methods=["POST"])
def to_collection():
    patch_id = request.form["id"]
    user_id = users.user_id()
    sql = text("INSERT INTO UsersToPatches (patch_id, user_id, sent_at) VALUES (:patch_id, :user_id, NOW())")
    db.session.execute(sql, {"patch_id": patch_id, "user_id": user_id})
    db.session.commit()
    return redirect("/kirjautunut")

# adding patch to general collection for everyone to see
@app.route("/new/merkki")
def new():
    return render_template("new_merkki.html")

# adding patch to general collection for everyone to see
@app.route("/send/new/merkki", methods=["POST"])
def send():
    name = request.form.get("nimi")
    username = users.get_username()

    # testing if name is already in the database
    # return True if name is already in the database
    if sendpatch.patchname_exists(name) is True:
        # return error message if name is already in the database and break out of function
        return render_template("new_merkki.html", error="Merkki on jo olemassa")

    # insert the patch to the database
    sendpatch.insert_patch_into_generalcollection(name, username)

    # Get the id of the created patch, for inserting image.
    patch_id = sendpatch.get_patch_id(name)


    # get file from html form
    file = request.files.get("file")

    # if file is not empty, then execute the sqls to insert the image.
    if file:
        file_name = file.filename
        # check if file is jpg or jpeg
        if not file_name.lower().endswith((".jpg", ".jpeg")):
            return render_template("new_merkki.html", error="Vain .jpg ja .jpeg tiedostot sallittu")

        # insert image to database
        sendpatch.insert_image(file, patch_id)

    # if all is okay return kirjautunut page
    return render_template("new_merkki.html", success="Merkki lisätty yhteiseen kokoelmaan onnistuneesti")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form["username"]
        if len(username) < 1 or len(username) > 20:
            return render_template("register.html", message="Käyttäjätunnuksen tulee olla 1-20 merkkiä pitkä")
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return render_template("register.html", message="Salasanat eroavat")
        if len(password1) < 8 or len(password1) > 20:
            return render_template("register.html", message="Salasanan tulee olla 8-20 merkkiä pitkä")
        if users.register(username, password1):
            return render_template("index.html", message="Rekisteröinti onnistui")
        else:
            return render_template("register.html", message="Rekisteröinti ei onnistunut")

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
            return render_template("login.html", message="Väärä tunnus tai salasana")

@app.route("/logout")
def logout():
    users.logout()
    return redirect("/")
