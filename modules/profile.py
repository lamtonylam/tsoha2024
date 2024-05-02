from sqlalchemy.sql import text
from modules import users
from db import db

def user_submitted_patches():
    sql = text("SELECT * FROM Patches WHERE created_by_user = :user_id")
    result = db.session.execute(sql, {"user_id": users.user_id()})
    return result.fetchall()

def own_patches():
    user_id = users.user_id()
    sql = text(
        "SELECT Patches.name, UsersToPatches.sent_at, UsersToPatches.patch_id, Patches.data, UsersToPatches.id \
                FROM Patches, UsersToPatches \
                WHERE Patches.id = UsersToPatches.patch_id AND UsersToPatches.user_id = :user_id;"
    )
    result = db.session.execute(sql, {"user_id": user_id})
    return result.fetchall()