from modules.db import db
from flask import session, flash
from os import abort

def get():
    sql = "SELECT * FROM schools WHERE id=:school_id"
    result = db.session.execute(sql, {"school_id": session["school"]})
    school = result.fetchone()
    return school

def create(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    schoolname = form["schoolname"]
    info = form["info"]
    address = form["address"]
    phone = form["phone"]
    www = form["www"]
    if len(schoolname) < 3 or len(info) < 10 or len(address) < 10 or len(phone) < 4 or len(www) < 3:
        flash("Tarkista, että kaikki kentät ovat oikein täytetty", "error")
        return False
    sql = "INSERT INTO schools (schoolname, info, address, phone, www, visible) VALUES (:schoolname, :info, :address, :phone, :www, :visible) RETURNING id"
    result = db.session.execute(sql, {"schoolname":schoolname, "info": info, "address": address, "phone": phone, "www": www, "visible": True})
    school_id = result.fetchone()[0]
    sql = "INSERT INTO schooladmins (user_id, school_id) VALUES (:user_id, :school_id)"
    db.session.execute(sql, {"user_id":session["user_id"], "school_id": school_id})
    db.session.commit()
    session["school"] = school_id
    return True

def edit(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    schoolname = form["schoolname"]
    info = form["info"]
    address = form["address"]
    phone = form["phone"]
    www = form["www"]
    if len(schoolname) < 3 or len(info) < 10 or len(address) < 10 or len(phone) < 4 or len(www) < 3:
        flash("Tarkista, että kaikki kentät ovat oikein täytetty", "error")
        return False
    sql = "SELECT schoolname FROM schools WHERE id=:id"
    result = db.session.execute(sql, {"id": session["school"]})
    oldname = result.fetchone()[0]
    if oldname != schoolname: # someone wants to change the name of the school
        sql = "SELECT * FROM schools WHERE schoolname=:schoolname"
        result = db.session.execute(sql, {"schoolname": schoolname})
        if result.fetchone():
            flash("Tämä koulunimi on jo käytössä muualla", "error")
            return False
    sql = "UPDATE schools SET schoolname=:schoolname, info=:info, address=:address, phone=:phone, www=:www WHERE id=:id"
    db.session.execute(sql, {"schoolname": schoolname, "info": info, "address": address, "phone": phone, "www": www, "id": session["school"]})
    db.session.commit()
    return True
