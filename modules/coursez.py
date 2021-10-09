from modules.db import db
from flask import session, flash
from os import abort

def getAll():
    sql = "SELECT * from courses;"
    result = db.session.execute(sql)
    courses = result.fetchall()
    return courses

def get():
    sql = "SELECT * from courses WHERE school_id=:school_id"
    result = db.session.execute(sql, {"school_id": session["school"]})
    courses = result.fetchall()
    return courses

def getPres(id):
    sql = "SELECT courses.coursename AS coursename, courses.info AS courseinfo, schools.schoolname AS schoolname, schools.info AS schoolinfo, schools.address AS address, schools.phone AS phone, schools.www AS www FROM courses LEFT JOIN schools ON courses.school_id=schools.id WHERE courses.id=:id"
    result = db.session.execute(sql, {"id": id})
    course = result.fetchone()
    return course

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
    sql = "SELECT * from courses WHERE id=:id AND school_id=:school_id" #gotta check you're only trying to edit your own school
    result = db.session.execute(sql, {"id": id, "school_id": session["school"]})
    course = result.fetchone()
    return course

def getRelevant(game_id):
    sql = "select courses.id AS id, courses.coursename AS coursename, courses.info AS info from courses LEFT JOIN coursegames ON courses.id=coursegames.course_id LEFT JOIN games ON coursegames.game_id=games.id WHERE games.id=:game_id AND courses.visible=True ORDER BY RANDOM () LIMIT 4"
    result = db.session.execute(sql, {"game_id": game_id})
    courses = result.fetchall()
    return courses

def hide(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    course_id = form["course_id"]
    sql = "UPDATE courses SET visible=false WHERE id=:course_id"
    db.session.execute(sql, {"course_id": course_id})
    db.session.commit()

def show(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    course_id = form["course_id"]
    sql = "UPDATE courses SET visible=True WHERE id=:course_id"
    db.session.execute(sql, {"course_id": course_id})
    db.session.commit()