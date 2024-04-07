from sqlalchemy.sql import text
from db import db
from PIL import Image
from PIL import ImageOps
from io import BytesIO
from flask import render_template


# Function to check if patchname exists before adding it into Patches which is the general collection.
def patchname_exists(name):
    sql = text("SELECT name FROM Patches WHERE name = :name")
    result = db.session.execute(sql, {"name": name})
    # If the patchname is found, return True
    return result.fetchone() is not None


# Function to insert a patch into the general collection
def insert_patch_into_generalcollection(name, username):
    sql = text("INSERT INTO Patches(name, created_by_user) VALUES (:name, :username)")
    db.session.execute(sql, {"name": name, "username": username})
    db.session.commit()


# Function to get the id of a patch by its name
def get_patch_id(name):
    query = text("SELECT id FROM Patches WHERE name = :name")
    result = db.session.execute(query, {"name": name})
    return result.fetchone()[0]


# Function to insert an image into the database
def insert_image(file, patch_id):
    # Read image data
    image_data = file.read()
    image = Image.open(BytesIO(image_data))

    # Rotate the image based on EXIF data
    image = ImageOps.exif_transpose(image)

    # Resize to 200 x 200
    image.thumbnail((200, 200))
    output = BytesIO()
    # Compress the image to 60% quality
    image.save(output, format="JPEG", quality=60)
    data = output.getvalue()
    # Insert the compressed and resized image into the database
    sql = text("INSERT INTO Images(patch_id, data) VALUES (:patch_id, :data)")
    db.session.execute(sql, {"patch_id": patch_id, "data": data})
    db.session.commit()
    print("kuva lisätty")
