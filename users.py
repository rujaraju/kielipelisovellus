from db import db
from flask import session
import secrets

def login(username, passwToCheck):
    sql = "SELECT passw, authority, firstname, id FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username": username})
    result = result.fetchone()
    if (result):
        if (result[0] == passwToCheck):
            session["csrf_token"] = secrets.token_hex(16)
            session["authority"] = result[1]
            session["firstname"] = result[2]
            session["user_id"] = result[3]
            sql = "SELECT SUM(points) FROM points WHERE user_id=:user_id"
            result = db.session.execute(sql, {"user_id":session["user_id"]})
            points = result.fetchone()[0]
            if points:
                session["points"] = points
            else:
                session["points"] = 0
            sql = "SELECT school_id FROM schooladmins WHERE user_id=:user_id"
            result = db.session.execute(sql, {"user_id": session["user_id"]})
            result = result.fetchone()
            if result:
                session["school"] = result[0]
            return True
        return False
    return False

def logout():
    keys = []
    for key in session:
        keys.append(key)
    for key in keys:
        del session[key]

def credentials(authority, specific):
    if not session.get("user_id"):
        return False
    if authority:
        if session["authority"] < authority:#smallest authorityvalue accepted
            return False
    if specific:
        if not session.get(specific):
            return False
    return True