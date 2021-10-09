from modules.db import db
from flask import session, flash
from os import abort

def getAll():#used by admin
    sql = "SELECT * FROM games;"
    result = db.session.execute(sql)
    games = result.fetchall()
    return games

def get():
    sql = "SELECT * FROM games WHERE creator_id=:user_id ORDER BY visible"
    result = db.session.execute(sql, {"user_id": session["user_id"]})
    games = result.fetchall()
    return games

def getByLang(lang_id):
        sql = "SELECT id, gamename FROM games where lang_id=:lang_id AND visible=True"
        result = db.session.execute(sql, {"lang_id":lang_id})
        games = result.fetchall()
        return games

def getGame(game_id):
    sql = "SELECT gamename FROM games where id=:id"
    result = db.session.execute(sql, {"id":game_id})
    gamename = result.fetchone()[0]
    sql = "SELECT id, info FROM sentences WHERE games_id=:id"
    result = db.session.execute(sql, {"id":game_id})
    sentences = result.fetchall()
    sql = "SELECT points FROM points WHERE user_id=:user_id AND game_id=:game_id"
    result = db.session.execute(sql, {"user_id": session["user_id"], "game_id": game_id})
    result = result.fetchone()
    if result:
        session["current_points"] = result[0]
    else:
        if session.get("current_points"):
            del session["current_points"]
    session["game_id"] = game_id
    return (gamename, sentences)

def checkResult(answers):
    sql = "UPDATE games SET playcount=playcount+1 where id=:id"
    db.session.execute(sql, {"id": session["game_id"]})
    sql = "SELECT rightanswer FROM sentences WHERE games_id=:id"
    result = db.session.execute(sql, {"id":session["game_id"]})
    rightanswers = result.fetchall()
    i = 0
    points = 0
    while i < len(rightanswers):
        if rightanswers[i][0] == answers[i]:
            points += 1
        i += 1
    if session.get("current_points"): #user has played this game before
        if points > session["current_points"]: #only update if got more points this time around
            sql = "UPDATE points SET points=:points WHERE game_id=:game_id AND user_id=:user_id"
            db.session.execute(sql, {"points": points, "game_id": session["game_id"], "user_id": session["user_id"]})
            session["points"] = session["points"] - session["current_points"] + points
            db.session.commit()
            return (True, points)
        del session["current_points"]
        del session["game_id"]
        return (False, points)
    else:
        sql = "INSERT INTO points (user_id, game_id, points) VALUES (:user_id, :game_id, :points)"
        db.session.execute(sql, {"user_id": session["user_id"], "game_id": session["game_id"], "points": points})
        session["points"] = session["points"] + points
        db.session.commit()
        del session["game_id"]
        return (True, points)

def create(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    gamename = form["gamename"]
    lang_id = form["lang_id"]
    sentences = form.getlist("sentence")
    rightanswers = form.getlist("rightanswer")
    if len(gamename) < 3:
        flash("Kielen nimi on lian lyhyt", "error")
        return False
    if not lang_id:
        flash("Valitse kieli", "error")
        return False
    for i in range(len(sentences)):
        if (len(sentences[i])) == 0:
            if i < 3:
                flash("Kirjoita ainakin kolme lausetta, kiitos", "error")
                return False
    sql = "SELECT * FROM games WHERE gamename=:gamename"
    result = db.session.execute(sql, {"gamename":gamename})
    if result.fetchone():
        flash("Kielen nimi on jo käytössä", "error")
        return False
    sql = "INSERT INTO games (gamename, lang_id, creator_id) VALUES (:gamename, :lang_id, :user_id) RETURNING id"
    result = db.session.execute(sql, {"gamename":gamename, "lang_id":lang_id, "user_id": session["user_id"]})
    games_id = result.fetchone()[0]
    for i in range(len(sentences)):
        if (len(sentences[i])) == 0:
            break
        sql = "INSERT INTO sentences (games_id, info, rightanswer) VALUES (:games_id, :info, :rightanswer)"
        db.session.execute(sql, {"games_id": games_id, "info": sentences[i], "rightanswer": rightanswers[i]})
    db.session.commit()
    return True

def getchosen():
    sql = "SELECT games.id, games.gamename FROM coursegames LEFT JOIN games ON coursegames.game_id=games.id WHERE coursegames.course_id=:course_id AND games.visible=True"
    result = db.session.execute(sql, {"course_id": session["course"]})
    chosen = result.fetchall()
    print("chosen")
    print(chosen)
    return chosen

def choose(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    game_id = form["game_id"]
    sql = "INSERT INTO coursegames (game_id, course_id) VALUES (:game_id, :course_id)"
    db.session.execute(sql, {"game_id": game_id, "course_id": session["course"]})
    db.session.commit()

def unchoose(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    game_id = form["game_id"]
    sql = "DELETE FROM coursegames WHERE game_id=:game_id AND course_id=:course_id"
    db.session.execute(sql, {"game_id": game_id, "course_id": session["course"]})
    db.session.commit()

def hide(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    game_id = form["game_id"]
    sql = "UPDATE games SET visible=false WHERE id=:game_id"
    db.session.execute(sql, {"game_id": game_id})
    db.session.commit()

def show(form):
    if session["csrf_token"] != form["csrf_token"]:
        abort(403)
    game_id = form["game_id"]
    sql = "UPDATE games SET visible=True WHERE id=:game_id"
    db.session.execute(sql, {"game_id": game_id})
    db.session.commit()

def scores():
    sql = "SELECT users.username AS username, SUM (points.points) AS points FROM points LEFT JOIN users ON users.id=points.user_id group by users.username ORDER BY sum(points.points) DESC LIMIT 20"
    result = db.session.execute(sql)
    scores = result.fetchall()
    return scores