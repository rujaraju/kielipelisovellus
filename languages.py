from db import db

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