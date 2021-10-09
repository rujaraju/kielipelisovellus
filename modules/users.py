from modules.db import db
from flask import session, flash
from os import abort
import secrets

def getAll():
    sql = "select * from users WHERE username NOT IN ('admin') ORDER BY active DESC, username"
    result = db.session.execute(sql)
    users = result.fetchall()
    return users

def getWaiting():
    sql = "select * from awaitingapproval LEFT JOIN users on users.id=awaitingapproval.user_id ORDER BY username"
    result = db.session.execute(sql)
    awaiting = result.fetchall()
    return awaiting


def login(form):
    username = form["username"]
    passwToCheck = form["passw"]
    if len(username) < 0 and len(passwToCheck) < 0:
        return False
    sql = "SELECT passw, authority, firstname, id, active FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username": username})
    result = result.fetchone()
    if (result):
        if (result[0] == passwToCheck):
            if not result[4]:
                flash("Tunnuksesi on lukittu", "error")
                return False
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
        flash("Tarkista kirjautumistiedot", "error")
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

def addNew(form):
    username = form["username"]
    firstname = form["firstname"]
    lastname = form["lastname"]
    passw = form["passw"]
    authority = int(form["authority"])
    if len(username) < 2 or len(firstname) < 2 or len(lastname) < 2 or len(passw) < 2:
        flash("Täytä lomake huolellisesti", "error")
        return False
    sql = "SELECT * FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    if result.fetchone():
        flash("Käyttäjänimi on jo käytössä", "error")
        return False
    sql = "INSERT INTO users (username, firstname, lastname, passw, authority) VALUES (:username, :firstname, :lastname, :passw, :authority) RETURNING id"
    result = db.session.execute(sql, {"username":username, "firstname":firstname, "lastname":lastname, "passw": passw, "authority": 0})
    user_id = result.fetchone()[0]
    if authority > 0:#wants to become more than regular user
        sql = "INSERT INTO awaitingapproval (user_id, wantsauthority) VALUES (:user_id, :authority)"
        db.session.execute(sql, {"user_id": user_id, "authority": authority})
        flash("Ylläpitäjä tarkistaa tietosi, ja myöntää laajemmat oikeudet, nyt voit kirjautua tavallisena käyttäjänä", "message")
    db.session.commit()
    return True

def block(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    user_id = form["user_id"]
    sql = "UPDATE users SET active=false WHERE id=:user_id"
    db.session.execute(sql, {"user_id": user_id})
    db.session.commit()

def unblock(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    user_id = form["user_id"]
    sql = "UPDATE users SET active=True WHERE id=:user_id"
    db.session.execute(sql, {"user_id": user_id})
    db.session.commit()

def approve(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    user_id = form["user_id"]
    authority = form["authority"]
    sql = "UPDATE users SET authority=:authority WHERE id=:user_id"
    db.session.execute(sql, {"authority": authority, "user_id": user_id})
    sql = "DELETE FROM awaitingapproval WHERE user_id=:user_id"
    db.session.execute(sql, {"user_id": user_id})
    db.session.commit()

def disapprove(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    user_id = form["user_id"]
    sql = "DELETE FROM awaitingapproval WHERE user_id=:user_id"
    db.session.execute(sql, {"user_id": user_id})
    db.session.commit()