from db import db
from flask import session

def get():
    sql = "SELECT * FROM schools WHERE id=:school_id"
    result = db.session.execute(sql, {"school_id": session["school"]})
    school = result.fetchone()
    return school