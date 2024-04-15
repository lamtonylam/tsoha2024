from app import app
from flask import render_template, request, redirect
from flask import session
from flask import flash
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

from PIL import Image
import io
import base64


@app.route("/")
def index():
    # get previously displayed text
    previous_text = session.get("random_text")
    # get a new random text
    random_text = random_text_generator.generate_random_text(previous_text)
    # save the new text to session
    session["random_text"] = random_text

    return render_template("index.html", random_text=random_text)


# logged in page, shows all patches and user's own patches
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

    return render_template(
        "kirjautunut.html",
        # zipping results and patch images together, so that they are together
        results=zip(results, patch_images),
    )


# individual patch view
@app.route("/merkki/<int:id>")
def merkki(id):
    # Fetch patch name and user id of the patch
    patch_name = patch_view.get_patch_name(id)
    created_by_user = patch_view.get_created_by_user(id)
    result_image = patch_view.get_image(id)
    comments = patch_view.get_comments(id)
    
    # Check if user is using a mobile device
    user_agent = request.headers.get('User-Agent')
    print(user_agent)
    is_mobile = "Mobile" in user_agent
    print(is_mobile)

    try:
        data = result_image.fetchone()[0] if result_image else None
    except:
        data = None

    logged_in_username = users.get_username()

    # If image data is found, upscale it and encode it to base64
    if data is not None:
        img = Image.open(io.BytesIO(data))

        upscaled_img = img.resize((img.width * 3, img.height * 3), Image.BICUBIC)

        byte_arr = io.BytesIO()
        upscaled_img.save(byte_arr, format="JPEG")
        encoded_img = base64.b64encode(byte_arr.getvalue()).decode("utf-8")

        return render_template(
            "merkki.html",
            nimi=patch_name,
            created_by_user=created_by_user,
            id=id,
            photo=encoded_img,
            comments=comments,
            is_mobile=is_mobile
        )

    return render_template(
        "merkki.html",
        nimi=patch_name,
        created_by_user=created_by_user,
        id=id,
        comments=comments,
        logged_in_username=logged_in_username,
        is_mobile=is_mobile
    )


# adding a patch from general collection to user's own collection
@app.route("/send/new/to_collection", methods=["POST"])
def to_collection():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    patch_id = request.form["id"]
    user_id = users.user_id()
    patch_view.patch_into_collection(patch_id, user_id)
    flash("Merkki lisätty omaan kokoelmaan onnistuneesti")
    return redirect("/kirjautunut")


# deleting a patch from general collection
@app.route("/deletepatch", methods=["POST"])
def delete_from_collection():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    patch_id = request.form["id"]
    patch_creator = patch_view.get_created_by_user(patch_id)
    logged_in_username = users.get_username()
    # if not the creator of the patch, ask for master password
    if logged_in_username != patch_creator:
        # check if master password is correct
        masterpassword = request.form["masterpassword"]
        # get master password from environment variable and check if it matches
        if masterpassword != getenv("master_key"):
            return redirect("/kirjautunut")
    patch_view.delete_patch(patch_id)
    flash("Merkki poistettu onnistuneesti")
    return redirect("/kirjautunut")


# add comment to patch
@app.route("/addcomment", methods=["POST"])
def addcomment():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    patch_id = request.form["id"]
    comment = request.form["comment"]
    user_id = users.user_id()
    patch_view.add_comment(patch_id, user_id, comment)
    return redirect(f"/merkki/{patch_id}#commentform")


# adding patch to general collection for everyone to see
@app.route("/new/merkki", methods=["GET", "POST"])
def send():
    if request.method == "GET":
        return render_template("new_merkki.html")
    elif request.method == "POST":
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

        # get user id
        userid = users.user_id()

        # insert the patch to the database
        try:
            sendpatch.insert_patch_into_generalcollection(name, userid)
        except:
            return render_template(
                "new_merkki.html",
                error="Merkkiä ei voitu lisätä yhteiseen kokoelmaan, olethan varma ettei samalla nimellä ole merkkiä",
            )

        # Get the id of the created patch, for inserting image.
        patch_id = sendpatch.get_patch_id(name)

        if file:
            # insert image to database
            sendpatch.insert_image(file, patch_id)

        # if all is okay return kirjautunut page
        return render_template(
            "new_merkki.html",
            success="Merkki lisätty yhteiseen kokoelmaan onnistuneesti",
        )


# registering user
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
            flash("Rekisteröinti onnistui")
            return redirect("/")
        else:
            return render_template(
                "register.html", message="Rekisteröinti ei onnistunut"
            )


# logging in user
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if users.login(username, password):
            flash("Kirjautuminen onnistui")
            return redirect("/")
        else:
            return render_template("login.html", message="Väärä tunnus tai salasana")


# logging out user
@app.route("/logout")
def logout():
    users.logout()
    flash("Olet kirjautunut ulos onnistuneesti")
    return redirect("/")


# profile page
@app.route("/profile")
def profile():
    username = users.get_username()

    sql = text("SELECT * FROM Patches WHERE created_by_user = :user_id")
    result = db.session.execute(sql, {"user_id": users.user_id()})
    user_submitted_patches = result.fetchall()

    user_id = users.user_id()
    query = text(
        "SELECT Patches.name, UsersToPatches.sent_at, UsersToPatches.patch_id \
                FROM Patches, UsersToPatches \
                WHERE Patches.id = UsersToPatches.patch_id AND UsersToPatches.user_id = :user_id;"
    )
    result = db.session.execute(query, {"user_id": user_id})
    own_patches_result = result.fetchall()

    patch_images = []
    for patch in own_patches_result:
        patch_id = patch[2]
        sql = text("SELECT data FROM Images WHERE patch_id = :patch_id;")
        result = db.session.execute(sql, {"patch_id": patch_id})
        image = result.fetchone()
        if image:
            image = base64.b64encode(image[0]).decode("utf-8")
            patch_images.append(image)
        else:
            patch_images.append(None)

    return render_template(
        "profile.html",
        username=username,
        own_patches_result=zip(own_patches_result, patch_images),
        patch_amount=len(own_patches_result),
        user_submitted_amount=len(user_submitted_patches),
    )
