from db import db
from flask import session, flash
from os import abort

def get():
    sql = "SELECT id, langname FROM langs ORDER BY langname"
    result = db.session.execute(sql)
    langs = result.fetchall()
    return langs

def getId(langname):
    langname = langname.capitalize()
    sql = "SELECT id FROM langs where langname=:langname"
    result = db.session.execute(sql, {"langname":langname})
    result = result.fetchone()
    if result:
        return result[0]
    return None

def create(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    langname = form["langname"]
    if len(langname) < 3:
        flash("Kielen nimi liian lyhyt", "error")
        return False
    langname = langname.capitalize()
    sql = "SELECT * FROM langs WHERE langname=:langname"
    result = db.session.execute(sql, {"langname":langname})
    if result.fetchone():
        flash("Kieli on jo tallennettu", "error")
        return False
    sql = "INSERT INTO langs (langname) VALUES (:langname) RETURNING id"
    result = db.session.execute(sql, {"langname":langname})
    lang_id = result.fetchone()[0]
    db.session.commit()
    return True