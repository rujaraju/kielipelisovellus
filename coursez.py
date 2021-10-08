from db import db
from flask import session, flash
from os import abort

def get():
    sql = "SELECT * from courses WHERE school_id=:school_id AND visible=True"
    result = db.session.execute(sql, {"school_id": session["school"]})
    courses = result.fetchall()
    return courses

def create(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    coursename = form["coursename"]
    info = form["info"]
    if len(coursename) < 3 or len(info) < 10:
        flash("Kurssinimi tai -info oli liian lyhyt", "error")
        return False
    sql = "INSERT INTO courses (coursename, info, school_id) VALUES (:coursename, :info, :school_id) RETURNING id"
    result = db.session.execute(sql, {"coursename":coursename, "info": info, "school_id": session["school"]})
    course_id = result.fetchone()[0]
    db.session.commit()
    session["course"] = course_id
    return True

def edit(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    coursename = form["coursename"]
    info = form["info"]
    if len(coursename) < 3 or len(info) < 10:
        flash("Kurssinimi tai -info oli liian lyhyt", "error")
        return
    sql = "UPDATE courses SET coursename=:coursename, info=:info WHERE id=:id"
    db.session.execute(sql, {"coursename":coursename, "info": info, "id": session["course"]})
    db.session.commit()
    return

def check(id):
    sql = "SELECT * from courses WHERE id=:id AND school_id=:school_id AND visible=True" #gotta check you're only trying to edit your own school
    result = db.session.execute(sql, {"id": id, "school_id": session["school"]})
    course = result.fetchone()
    return course