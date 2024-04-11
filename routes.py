from app import app
from flask import render_template, request, redirect
from flask import session
import users
from sqlalchemy.sql import text
from db import db
from flask import abort
from os import getenv

# import base64 for image encoding
import base64

# for random texts in index.html
import random_text_generator

# module import for sending patches into general collection
import sendpatch

# module for patch_view individual patch
import patch_view


@app.route("/")
def index():
    # get previously displayed text
    previous_text = session.get("random_text")
    # get a new random text
    random_text = random_text_generator.generate_random_text(previous_text)
    # save the new text to session
    session["random_text"] = random_text

    return render_template("index.html", random_text=random_text)


@app.route("/kirjautunut")
def kirjautnut():
    # if user is not logged in dont run sqls etc.
    if users.get_username() == "":
        return render_template("kirjautunut.html")

    # sort patches by id, default is ascending, can be changed by adding ?sort to the url
    sort_order = request.args.get("sort")
    if sort_order == "asc":
        query = text("SELECT id, name FROM Patches ORDER BY id ASC;")
    elif sort_order == "desc":
        query = text("SELECT id, name FROM Patches ORDER BY id DESC;")
    else:
        query = text("SELECT id, name FROM Patches ORDER BY id ASC;")
    result = db.session.execute(query)
    results = result.fetchall()

    # Fetch image data for each patch, encode it to base64 and pass it to the template
    patch_images = []
    for patch in results:
        patch_id = patch[0]
        sql = text("SELECT data FROM Images WHERE patch_id = :patch_id;")
        result = db.session.execute(sql, {"patch_id": patch_id})
        image = result.fetchone()
        if image:
            image = base64.b64encode(image[0]).decode("utf-8")
            patch_images.append(image)
        else:
            patch_images.append(None)

    user_id = users.user_id()
    query = text(
        "SELECT Patches.name, UsersToPatches.sent_at, UsersToPatches.patch_id \
                FROM Patches, UsersToPatches \
                WHERE Patches.id = UsersToPatches.patch_id AND UsersToPatches.user_id = :user_id;"
    )
    own_patches_result = db.session.execute(query, {"user_id": user_id})
    return render_template(
        "kirjautunut.html",
        results=zip(results, patch_images),
        own_patches_result=own_patches_result,
    )


@app.route("/merkki/<int:id>")
def merkki(id):
    # Fetch patch name and user id of the patch
    patch_name = patch_view.get_patch_name(id)
    created_by_user = patch_view.get_created_by_user(id)
    result_image = patch_view.get_image(id)
    try:
        data = result_image.fetchone()[0] if result_image else None
    except:
        data = None

    # If image data is found, encode it to base64 and pass it to the template
    if data is not None:
        response = base64.b64encode(data).decode("utf-8")
        return render_template(
            "merkki.html",
            nimi=patch_name,
            created_by_user=created_by_user,
            id=id,
            photo=response,
        )

    return render_template(
        "merkki.html", nimi=patch_name, created_by_user=created_by_user, id=id
    )


# adding a patch from general collection to user's own collection
@app.route("/send/new/to_collection", methods=["POST"])
def to_collection():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    patch_id = request.form["id"]
    user_id = users.user_id()
    patch_view.patch_into_collection(patch_id, user_id)
    return redirect("/kirjautunut")


# deleting a patch from general collection
@app.route("/deletepatch", methods=["POST"])
def delete_from_collection():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    patch_id = request.form["id"]
    masterpassword = request.form["masterpassword"]
    if masterpassword != getenv("master_key"):
        return redirect("/kirjautunut")
    patch_view.delete_patch(patch_id)
    return redirect("/kirjautunut")


# adding patch to general collection for everyone to see
@app.route("/new/merkki")
def new():
    return render_template("new_merkki.html")


# adding patch to general collection for everyone to see
@app.route("/send/new/merkki", methods=["POST"])
def send():
    name = request.form.get("nimi")
    if len(name) > 100:
        return render_template(
            "new_merkki.html", error="Merkin nimi on liian pitkä, max 100 merkkiä"
        )

    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)

    # get file from html form
    file = request.files.get("file")

    # check if file is empty
    if file:
        file_name = file.filename
        # check if file is jpg or jpeg
        if not file_name.lower().endswith((".jpg", ".jpeg")):
            return render_template(
                "new_merkki.html", error="Vain .jpg ja .jpeg tiedostot sallittu"
            )

    userid = users.user_id()

    # testing if name is already in the database
    # return True if name is already in the database
    if sendpatch.patchname_exists(name) is True:
        # return error message if name is already in the database and break out of function
        return render_template("new_merkki.html", error="Merkki on jo olemassa")

    # insert the patch to the database
    sendpatch.insert_patch_into_generalcollection(name, userid)

    # Get the id of the created patch, for inserting image.
    patch_id = sendpatch.get_patch_id(name)

    if file:
        # insert image to database
        sendpatch.insert_image(file, patch_id)

    # if all is okay return kirjautunut page
    return render_template(
        "new_merkki.html", success="Merkki lisätty yhteiseen kokoelmaan onnistuneesti"
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form["username"]
        if len(username) < 1 or len(username) > 20:
            return render_template(
                "register.html",
                message="Käyttäjätunnuksen tulee olla 1-20 merkkiä pitkä",
            )
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return render_template("register.html", message="Salasanat eroavat")
        if len(password1) < 8 or len(password1) > 20:
            return render_template(
                "register.html", message="Salasanan tulee olla 8-20 merkkiä pitkä"
            )
        if users.register(username, password1):
            return render_template("index.html", message="Rekisteröinti onnistui")
        else:
            return render_template(
                "register.html", message="Rekisteröinti ei onnistunut"
            )


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


@app.route("/profile")
def profile():
    username = users.get_username()

    user_id = users.user_id()
    query = text(
        "SELECT Patches.name, UsersToPatches.sent_at, UsersToPatches.patch_id \
                FROM Patches, UsersToPatches \
                WHERE Patches.id = UsersToPatches.patch_id AND UsersToPatches.user_id = :user_id;"
    )
    result = db.session.execute(query, {"user_id": user_id})
    own_patches_result = result.fetchall()

    return render_template(
        "profile.html",
        username=username,
        own_patches_result=own_patches_result,
        patch_amount=len(own_patches_result),
    )
