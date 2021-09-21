#todos: when saving names always capitalize, data security in forms, check that input is ok, game page with score checking

from flask import Flask
from flask import redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from os import getenv
import fixforheroku

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = fixforheroku.uri #getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = getenv("SECRET_KEY")

db = SQLAlchemy(app)

@app.route("/newuser")
def newuser():
    if (session.get("user_id")):
        return redirect("/")
    return render_template("newuser.html")

@app.route("/newlanguage")
def newlanguage():
    return render_template("newlanguage.html")

@app.route("/newgame")
def newgame():
    sql = "SELECT id, langname FROM langs"
    result = db.session.execute(sql)
    langs = result.fetchall()
    return render_template("newgame.html", langs=langs)
    
@app.route("/login",methods=["POST"]) # add message if wrong credentials
def login():
    username = request.form["username"]
    passwToCheck = request.form["passw"]
    sql = "SELECT passw, authority, points, firstname, id FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username": username})
    result = result.fetchone()
    if (result):
        if (result[0] == passwToCheck):
            session["authority"] = result[1]
            session["points"] = result[2]
            session["firstname"] = result[3]
            session["user_id"] = result[4]
            return redirect("/")    
    return render_template("index.html", message="Tarkista kirjautumistietosi.")

@app.route("/logout")
def logout():
    del session["user_id"], session["authority"], session["points"], session["firstname"]
    return redirect("/")

@app.route("/")
def index():
    sql = "SELECT langname FROM langs ORDER BY langname"
    result = db.session.execute(sql)
    langs = result.fetchall()
    return render_template("index.html", langs=langs)

@app.route("/kieli/<langname>")
def language(langname):
    if not session.get("user_id"):
        return redirect("/")
    print(langname)
    langname = langname.capitalize()
    print(langname)
    sql = "SELECT id FROM langs where langname=:langname"
    result = db.session.execute(sql, {"langname":langname})
    result = result.fetchone()
    if (result):
        lang_id = result[0]
        print(str(lang_id))
        sql = "SELECT id, gamename FROM games where lang_id=:lang_id"
        result = db.session.execute(sql, {"lang_id":lang_id})
        games = result.fetchall()
        return render_template("games.html", games=games)
    return redirect("/")

@app.route("/peli/<int:id>")
def game(id):
    if not session.get("user_id"):
        return redirect("/")
    sql = "SELECT gamename FROM games where id=:id"
    result = db.session.execute(sql, {"id":id})
    gamename = result.fetchone()[0]
    sql = "SELECT id, info FROM sentences WHERE games_id=:id"
    result = db.session.execute(sql, {"id":id})
    sentences = result.fetchall()
    session["playing"] = id
    return render_template("game.html", gamename=gamename, sentences=sentences)

@app.route("/playgame", methods=["POST"])
def playgame():
    answers = request.form.getlist("answer")
    sql = "SELECT rightanswer FROM sentences WHERE games_id=:id"
    result = db.session.execute(sql, {"id":session["playing"]})
    rightanswers = result.fetchall()
    print(rightanswers) 
    print(answers)
    i = 0
    points = 0
    while i < len(rightanswers):
        if rightanswers[i][0] == answers[i]:
            points += 1
        i += 1
    #sql = "INSERT INTO points (user_id, game_id, points) VALUES (:user_id, game_id"
    sql = "SELECT points FROM users WHERE id=:user_id"
    result = db.session.execute(sql, {"user_id":session["user_id"]})
    userpoints = result.fetchone()[0]
    print(str(userpoints))
    userpoints += points
    print(str(userpoints))
    sql = "UPDATE users SET points=:userpoints WHERE id=:user_id"
    db.session.execute(sql, {"user_id":session["user_id"], "userpoints": userpoints})
    db.session.commit()
    session["playing"] = None
    session["points"] = userpoints
    return redirect("/")

@app.route("/createuser", methods=["POST"])
def createuser():
    username = request.form["username"]
    firstname = request.form["firstname"]
    lastname = request.form["lastname"]
    passw = request.form["passw"]
    authority = int(request.form["authority"])
    sql = "SELECT * FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    if result.fetchone():
        print("User exists")
        return redirect("/newuser")
    sql = "INSERT INTO users (username, firstname, lastname, passw, authority, points) VALUES (:username, :firstname, :lastname, :passw, :authority, :points) RETURNING id"
    result = db.session.execute(sql, {"username":username, "firstname":firstname, "lastname":lastname, "passw": passw, "authority": authority, "points":0})
    user_id = result.fetchone()[0]
    print(user_id)
    db.session.commit()
    return redirect("/newuser")

@app.route("/createlang", methods=["POST"])
def createlang():
    langname = request.form["langname"]
    langname = langname.capitalize()
    sql = "SELECT * FROM langs WHERE langname=:langname"
    result = db.session.execute(sql, {"langname":langname})
    if result.fetchone():
        print("Language exists")
        return redirect("/newlanguage")
    sql = "INSERT INTO langs (langname) VALUES (:langname) RETURNING id"
    result = db.session.execute(sql, {"langname":langname})
    lang_id = result.fetchone()[0]
    print(lang_id)
    db.session.commit()
    return redirect("/newlanguage")

@app.route("/creategame", methods=["POST"])
def creategame():
    gamename = request.form["gamename"]
    lang_id = request.form["lang_id"]
    sql = "SELECT * FROM games WHERE gamename=:gamename"
    result = db.session.execute(sql, {"gamename":gamename})
    if result.fetchone():
        print("game exists")
        return redirect("/newgame") # to add: errormessage
    sql = "INSERT INTO games (gamename, lang_id) VALUES (:gamename, :lang_id) RETURNING id"
    result = db.session.execute(sql, {"gamename":gamename, "lang_id":lang_id})
    games_id = result.fetchone()[0]
    print("games id " + str(games_id))
    sentences = request.form.getlist("sentence")
    rightanswers = request.form.getlist("rightanswer")
    for i in range(len(sentences)):
        if (len(sentences[i])) == 0:
            break
        sql = "INSERT INTO sentences (games_id, info, rightanswer, created_at) VALUES (:games_id, :info, :rightanswer, NOW())"
        db.session.execute(sql, {"games_id": games_id, "info": sentences[i], "rightanswer": rightanswers[i]})
    db.session.commit()
    return redirect("/newgame")