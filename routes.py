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
import random


@app.route("/")
def index():
    random_texts = ["Haalarimerkit on niin kuin Pokemonit eiks jeh?", \
                    "Haalarimerkkejä ei voi olla liikaa.", \
                    "Haalarimerkit on kuin tatuoinnit, mutta ei niin kivuliaita.", \
                    "Haalarimerkit on kuin karkkia, ei voi olla liikaa.", \
                    "Haalarimerkkien kokoelma: Jokainen merkki on kuin muisto opiskelijaelämän matkalta", \
                    "Haalarimerkit on kuin kunniamerkkejä, mutta parempia.", \
                    "Haalarimerkit: Elämän merkkejä, joita kannamme ylpeinä opiskelijoina", \
                    "Haalarimerkit: Jokainen merkki kertoo tarinan", \
                    "Haalarimerkit: Jokainen merkki on kuin palanen elämää", \
                    "Haalarimerkit: Jokainen merkki on kuin palanen historiaa", \
                    "Haalarimerkit: Jokainen merkki on kuin palanen sinua", \
                    "Haalarimerkit: Opiskelijoiden tapa ilmaista itseään, yhtä värikäs kuin elämä itse" ,\
    ]
    random_text = random.choice(random_texts)
    return render_template("index.html" , random_text = random_text)

@app.route("/kirjautunut")
def kirjautnut():
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
    # Fetch patch name
    query_patch = text('SELECT name FROM Patches WHERE id = :id;')
    result_patch = db.session.execute(query_patch, {"id": id})
    patch_name = result_patch.fetchone()[0] if result_patch else None

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
        return render_template("merkki.html", nimi=patch_name, id=id, photo=response)
    else:
        return render_template("merkki.html", nimi=patch_name, id=id)


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
    # sending the patch to the general collection
    name = request.form.get("nimi")
    sql = text("INSERT INTO Patches(name) VALUES (:name)")  
    db.session.execute(sql, {"name": name})
    db.session.commit()

    # Get the id of the created patch
    query = text("SELECT id FROM Patches WHERE name = :name")
    result = db.session.execute(query, {"name": name})
    patch_id = result.fetchone()[0]

    file = request.files["file"]
    name = file.filename
    if not name.lower().endswith((".jpg", ".jpeg")):
        return "Invalid filename"
    
    #luetaan kuvan data
    image_data = file.read()
    image = Image.open(BytesIO(image_data))
    
    # 200 x 200
    image.thumbnail((200, 200))
    output = BytesIO()
    # compress the image 60% quality
    image.save(output, format='JPEG', quality=60)
    data = output.getvalue()

    # Insert the compressed and resized image into the database
    sql = text("INSERT INTO Images(patch_id, data) VALUES (:patch_id, :data)")
    db.session.execute(sql, {"patch_id": patch_id, "data": data })
    db.session.commit()
    print("kuva tallennettu onnistuneesti")

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