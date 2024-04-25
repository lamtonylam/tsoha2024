from app import app
from flask import render_template, request, redirect
from flask import session
from flask import flash
import modules.users as users
from sqlalchemy.sql import text
from db import db
from flask import abort
from os import getenv

# import base64 for image encoding
import base64

# for random texts in index.html
import modules.random_text_generator as random_text_generator

# module import for sending patches into general collection
import modules.sendpatch as sendpatch

# module for patch_view individual patch
import modules.patch_view as patch_view

from PIL import Image
from io import BytesIO
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

    categories = sendpatch.get_categories()

    # sort patches by id, default is ascending, can be changed by adding ?sort to the url
    sort_order = request.args.get("sort")
    search_argument = request.args.get("query")
    category_argument = request.args.get("category")
    # check if search argument is too long
    try:
        if len(search_argument) > 100:
            return redirect("/kirjautunut")
    except:
        pass
    params = {}

    order_by_sql = ""
    search_sql = ""
    category_sql = ""
    search_category_argument = ""
    if sort_order == "asc":
        order_by_sql = "ORDER BY id ASC"
    elif sort_order == "desc":
        order_by_sql = "ORDER BY id DESC"
    if search_argument:
        search_sql = "LOWER(name) LIKE LOWER(:search_argument)"
        params["search_argument"] = f"%{search_argument}%"

    if category_argument:
        category_sql = "category_id = :category_id"
        params["category_id"] = category_argument

    if search_argument and category_argument:
        search_category_argument = "WHERE " + " AND ".join((search_sql, category_sql))
        search_sql = ""
        category_sql = ""
    elif search_argument:
        search_sql = "WHERE " + search_sql
    elif category_argument:
        category_sql = "WHERE " + category_sql

    base_query = text(
        f"SELECT id, name, data FROM Patches {search_sql} {category_sql} {search_category_argument} {order_by_sql}"
    )
    results = db.session.execute(base_query, params).fetchall()

    # Fetch image data for each patch, encode it to base64 and pass it to the template
    patch_images = []
    for patch in results:
        image = patch[2]
        if image:
            image = base64.b64encode(image).decode("utf-8")
        else:
            image = None
        patch_images.append(image)

    category_searched = ""
    if category_argument:
        for category in categories:
            if category[0] == int(category_argument):
                category_searched = category[0]
                break

    return render_template(
        "kirjautunut.html",
        # zipping results and patch images together, so that they are together
        results=zip(results, patch_images),
        categories=categories,
        search_argument=search_argument,
        category_searched=category_searched,
        sort_order=sort_order,
    )


# individual patch view
@app.route("/merkki/<int:id>")
def merkki(id):
    # referrer for patch site, because of navbar variable
    try:
        referring_page = request.referrer
        referrer = ""
        if "profile" in referring_page:
            referrer = "profile"
        elif "kirjautunut" in referring_page:
            referrer = "kirjautunut"
    # if cant find referrer, redirect to 404
    except Exception as e:
        print(e)
        return redirect("/404")
    # Fetch patch name and user id of the patch
    patch_name = patch_view.get_patch_name(id)
    created_by_user = patch_view.get_created_by_user(id)
    result_image = patch_view.get_image(id)
    comments = patch_view.get_comments(id)
    category = patch_view.get_category(id)

    # Check if user is using a mobile device
    user_agent = request.headers.get("User-Agent")
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
        img = Image.open(BytesIO(data))

        upscaled_img = img.resize((img.width * 3, img.height * 3), Image.BICUBIC)

        output = BytesIO()
        upscaled_img.save(output, format="JPEG")
        output_value = output.getvalue()
        encoded_output = base64.b64encode(output_value)
        encoded_img = encoded_output.decode("utf-8")

        return render_template(
            "merkki.html",
            nimi=patch_name,
            created_by_user=created_by_user,
            id=id,
            photo=encoded_img,
            comments=comments,
            is_mobile=is_mobile,
            category=category,
            referrer=referrer,
        )

    return render_template(
        "merkki.html",
        nimi=patch_name,
        created_by_user=created_by_user,
        id=id,
        comments=comments,
        logged_in_username=logged_in_username,
        is_mobile=is_mobile,
        category=category,
        referrer=referrer,
    )


# adding a patch from general collection to user's own collection
@app.route("/send/new/to_collection", methods=["POST"])
def to_collection():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    patch_id = request.form["id"]
    user_id = users.user_id()
    if patch_view.patch_into_collection(patch_id, user_id):
        flash("Merkki lisätty omaan kokoelmaan onnistuneesti", "success")
    else:
        flash(
            "Merkin lisääminen omaan kokoelmaan epäonnistui, merkki on jo kokoelmassasi",
            "error",
        )
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
    flash("Merkki poistettu onnistuneesti", "success")
    return redirect("/kirjautunut")


# add comment to patch
@app.route("/addcomment", methods=["POST"])
def addcomment():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    patch_id = request.form["id"]
    comment = request.form["comment"]
    if len(comment) > 1000:
        flash("Kommentti ei voi olla yli 1000 merkkiä pitkä", "error")
        return redirect(f"/merkki/{patch_id}#commentform")
    user_id = users.user_id()
    patch_view.add_comment(patch_id, user_id, comment)
    return redirect(f"/merkki/{patch_id}#commentform")


# adding patch to general collection for everyone to see
@app.route("/new/merkki", methods=["GET", "POST"])
def send():
    if request.method == "GET":
        categories = sendpatch.get_categories()
        return render_template(
            "new_merkki.html",
            categories=categories,
        )
    elif request.method == "POST":
        categories = sendpatch.get_categories()
        name = request.form.get("nimi")
        category = request.form.get("category")
        if len(name) > 100:
            flash("Merkkin nimi ei voi olla yli 100 merkkiä pitkä", "error")
            return render_template(
                "new_merkki.html",
                categories=categories,
            )

        if len(name) == 0:
            flash("Merkin nimi ei voi olla tyhjä", "error")
            return render_template(
                "new_merkki.html",
                categories=categories,
            )

        if session["csrf_token"] != request.form["csrf_token"]:
            abort(403)

        if len(category) == 0:
            flash("Valitse kategoria", "error")
            return render_template(
                "new_merkki.html",
                categories=categories,
            )

        # get file from html form
        file = request.files.get("file")

        # check if file is empty
        if file:
            file_name = file.filename
            # check if file is jpg or jpeg
            if not file_name.lower().endswith((".jpg", ".jpeg")):
                flash("Vain .jpg ja .jpeg tiedostot sallittu", "error")
                return render_template(
                    "new_merkki.html",
                    categories=categories,
                )

        # get user id
        userid = users.user_id()

        # if file is empty, insert patch without image
        if not file:
            try:
                sendpatch.insert_patch_into_generalcollection(name, userid, category)
            except Exception as e:
                print(e)
                flash(
                    "Virhe tapahtui, voi olla että merkin nimi on jo olemassa", "error"
                )
                return render_template(
                    "new_merkki.html",
                    categories=categories,
                )
        else:
            try:
                sendpatch.insert_patch_into_generalcollection(
                    name, userid, category, file
                )
            except Exception as e:
                print(e)
                flash(
                    "Virhe tapahtui, voi olla että merkin nimi on jo olemassa", "error"
                )
                return render_template(
                    "new_merkki.html",
                    categories=categories,
                )

        # if all is okay return kirjautunut page
        categories = sendpatch.get_categories()
        flash("Merkki lisätty yhteiseen kokoelmaan onnistuneesti", "success")
        return render_template(
            "new_merkki.html",
            categories=categories,
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
        if users.register(username, password1):
            flash("Rekisteröinti onnistui", "success")
            return redirect("/")
        else:
            return render_template(
                "register.html",
                message="Rekisteröinti ei onnistunut",
                username=username,
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
            flash("Kirjautuminen onnistui", "success")
            return redirect("/")
        else:
            return render_template(
                "login.html", message="Väärä tunnus tai salasana", username=username
            )


# logging out user
@app.route("/logout")
def logout():
    users.logout()
    flash("Olet kirjautunut ulos onnistuneesti", "success")
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
        "SELECT Patches.name, UsersToPatches.sent_at, UsersToPatches.patch_id, Patches.data, UsersToPatches.id \
                FROM Patches, UsersToPatches \
                WHERE Patches.id = UsersToPatches.patch_id AND UsersToPatches.user_id = :user_id;"
    )
    result = db.session.execute(query, {"user_id": user_id})
    own_patches_result = result.fetchall()

    patch_images = []
    for patch in own_patches_result:
        image = patch[3]
        if image:
            image = base64.b64encode(image).decode("utf-8")
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


# page to delete user's own patches
@app.route("/profile/deletepatch", methods=["GET", "POST"])
def delete_own_patch():
    if request.method == "POST":
        if session["csrf_token"] != request.form["csrf_token"]:
            abort(403)
        result_id = request.form["patch_id"]
        user_id = users.user_id()
        try:
            patch_view.delete_patch_from_collection(result_id, user_id)
        except Exception as e:
            print(e)
            flash("Merkkiä ei voitu poistaa", "error")
            return redirect("/profile/deletepatch")
        flash("Merkki poistettu onnistuneesti", "success")
        return redirect("/profile/deletepatch")
    elif request.method == "GET":
        username = users.get_username()

        sql = text("SELECT * FROM Patches WHERE created_by_user = :user_id")
        result = db.session.execute(sql, {"user_id": users.user_id()})

        user_id = users.user_id()
        query = text(
            "SELECT Patches.name, UsersToPatches.sent_at, UsersToPatches.patch_id, Patches.data, UsersToPatches.id \
                    FROM Patches, UsersToPatches \
                    WHERE Patches.id = UsersToPatches.patch_id AND UsersToPatches.user_id = :user_id;"
        )
        result = db.session.execute(query, {"user_id": user_id})
        own_patches_result = result.fetchall()

        patch_images = []
        for patch in own_patches_result:
            image = patch[3]
            if image:
                image = base64.b64encode(image).decode("utf-8")
                patch_images.append(image)
            else:
                patch_images.append(None)

        return render_template(
            "delete_patch.html",
            username=username,
            own_patches_result=zip(own_patches_result, patch_images),
        )
