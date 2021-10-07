from db import db
from flask import session

def get():
    sql = "SELECT * FROM games WHERE creator_id=:user_id ORDER BY visible"
    result = db.session.execute(sql, {"user_id": session["user_id"]})
    games = result.fetchall()
    return games

def getByLang(lang_id):
        sql = "SELECT id, gamename FROM games where lang_id=:lang_id"
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
    