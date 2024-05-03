"""
This module is used for inserting patches.
"""
from sqlalchemy.sql import text
from db import db
from PIL import Image
from PIL import ImageOps
from io import BytesIO


# Function to insert a patch into the general collection
def insert_patch_into_generalcollection(name, userid, category, file=None):
    if file:
        # Read image data
        image_data = file.read()
        image = Image.open(BytesIO(image_data))
        
        # check if image is larger than 10MB
        if len(image_data) > 10000000:
            raise ValueError("Image is too large. Maximum size is 10MB.")
        
        # Rotate the image based on EXIF data
        image = ImageOps.exif_transpose(image)

        # Resize to 200 x 200
        image.thumbnail((400, 400))
        output = BytesIO()
        # Compress the image to 60% quality
        image.save(output, format="JPEG", quality=80)
        data = output.getvalue()

        sql = text(
            "INSERT INTO Patches(name, created_by_user, data, category_id) VALUES (:name, :userid, :data, :category)"
        )
        db.session.execute(
            sql, {"name": name, "userid": userid, "data": data, "category": category}
        )
    else:
        sql = text(
            "INSERT INTO Patches(name, created_by_user, category_id) VALUES (:name, :userid, :category)"
        )
        db.session.execute(sql, {"name": name, "userid": userid, "category": category})

    db.session.commit()


# Function to get the id of a patch by its name
def get_patch_id(name):
    sql = text("SELECT id FROM Patches WHERE name = :name")
    result = db.session.execute(sql, {"name": name})
    return result.fetchone()[0]


# Get categories
def get_categories():
    sql = text("SELECT id, name FROM Categories")
    result = db.session.execute(sql)
    categories = result.fetchall()
    return categories
