from sqlalchemy.sql import text
from db import db


def get_patch_name(id):
    # Fetch patch name of the patch
    query_patch = text("SELECT name FROM Patches WHERE id = :id;")
    result_patch = db.session.execute(query_patch, {"id": id})
    row = result_patch.fetchone()
    patch_name = row[0]
    return patch_name


def get_created_by_user(id):
    # Fetch user id of the patch
    query_patch = text("SELECT created_by_user FROM Patches WHERE id = :id;")
    result_patch = db.session.execute(query_patch, {"id": id})
    row = result_patch.fetchone()
    created_by_user = row[0]

    query_username = text("SELECT username FROM Users WHERE id = :id;")
    created_by_user = db.session.execute(query_username, {"id": created_by_user})
    created_by_user = created_by_user.fetchone()[0]

    return created_by_user


def get_image(id):
    # Fetch image data
    query_image = text("SELECT data FROM images WHERE patch_id=:patch_id")
    result_image = db.session.execute(query_image, {"patch_id": id})

    return result_image


def patch_into_collection(patch_id, user_id):
    sql_set_timezone = text("SET TIME ZONE 'Europe/Helsinki';")
    db.session.execute(sql_set_timezone)
    sql = text(
        "INSERT INTO UsersToPatches (patch_id, user_id, sent_at) VALUES (:patch_id, :user_id, NOW())"
    )
    db.session.execute(sql, {"patch_id": patch_id, "user_id": user_id})
    db.session.commit()


def delete_patch(patch_id):
    sql = text("DELETE FROM Patches WHERE id = :patch_id")
    db.session.execute(sql, {"patch_id": patch_id})
    db.session.commit()
