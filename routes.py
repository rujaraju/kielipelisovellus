from app import app
from flask import redirect, render_template, request, session
from os import abort
import secrets
from os import getenv
from db import db

app.secret_key = getenv("SECRET_KEY")

@app.route("/luotunnukset")
def newuser():
    if (session.get("user_id")):
        return redirect("/")
    return render_template("newuser.html")

@app.route("/luokurssi")
def newcourse():
    if not session.get("user_id"):
        return redirect("/")
    if session["authority"] != 2:
        return redirect("/") #only schooladmins can create courses
    return render_template("newcourse.html")

@app.route("/luokieli")
def newlanguage():
    if not session.get("user_id"):
        return redirect("/")
    if session["authority"] == 0:
        return redirect("/") #normal user can't create games, all others can
    return render_template("newlanguage.html")

@app.route("/luopeli")
def newgame():
    if not session.get("user_id"):
        return redirect("/")
    if session["authority"] == 0:
        return redirect("/") #normal user can't create games, all others can
    sql = "SELECT id, langname FROM langs"
    result = db.session.execute(sql)
    langs = result.fetchall()
    return render_template("newgame.html", langs=langs)

@app.route("/uusikoulu")
def newschool():
    return render_template("newschool.html")

@app.route("/login",methods=["POST"]) # add message if wrong credentials
def login():
    username = request.form["username"]
    passwToCheck = request.form["passw"]
    sql = "SELECT passw, authority, firstname, id FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username": username})
    result = result.fetchone()
    if (result):
        if (result[0] == passwToCheck):
            session["csrf_token"] = secrets.token_hex(16)
            session["authority"] = result[1]
            session["firstname"] = result[2]
            session["user_id"] = result[3]
            #select SUM for pointstable here
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
                session["school"] = result[0] #this app limits the numbers of schools for one schooladmin to 1
            return redirect("/")    
    return render_template("index.html", message="Tarkista kirjautumistietosi.")

@app.route("/logout")
def logout():
    del session["user_id"], session["authority"], session["points"], session["firstname"]
    if session.get("school"):
        del session["school"]
    return redirect("/")

@app.route("/")
def index():
    if session:
        if session.get("langname"):#if returning from editing courses
            del session["langname"]
        if session.get("course"):#if returning from editing courses
            del session["course"]
    sql = "SELECT langname FROM langs ORDER BY langname"
    result = db.session.execute(sql)
    langs = result.fetchall()
    return render_template("index.html", langs=langs)

@app.route("/omatpelit")
def ownGames():
    sql = "SELECT * FROM games WHERE creator_id=:user_id ORDER BY visible"
    result = db.session.execute(sql, {"user_id": session["user_id"]})
    games = result.fetchall()
    return render_template("owngames.html", games=games)

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

@app.route("/peli/<int:game_id>")
def game(game_id):
    if not session.get("user_id"):
        return redirect("/")
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
        print(result)
        session["current_points"] = result[0]
    session["game_id"] = game_id
    return render_template("game.html", gamename=gamename, sentences=sentences)

@app.route("/kouluhallinta")
def editschool():
    if not session.get("school"):
        return redirect("/")
    sql = "SELECT * FROM schools WHERE id=:school_id"
    result = db.session.execute(sql, {"school_id": session["school"]})
    school = result.fetchone()
    return render_template("editschool.html", school=school)

@app.route("/playgame", methods=["POST"]) # to add here: page to show result from current game
def playgame():
    answers = request.form.getlist("answer")
    sql = "SELECT rightanswer FROM sentences WHERE games_id=:id"
    result = db.session.execute(sql, {"id":session["game_id"]})
    rightanswers = result.fetchall()
    print(rightanswers) 
    print(answers)
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
            del session["current_points"]
    else:
        sql = "INSERT INTO points (user_id, game_id, points) VALUES (:user_id, :game_id, :points)"
        db.session.execute(sql, {"user_id": session["user_id"], "game_id": session["game_id"], "points": points})
        session["points"] = session["points"] + points
    db.session.commit()

    del session["game_id"]
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
    sql = "INSERT INTO users (username, firstname, lastname, passw, authority) VALUES (:username, :firstname, :lastname, :passw, :authority) RETURNING id"
    result = db.session.execute(sql, {"username":username, "firstname":firstname, "lastname":lastname, "passw": passw, "authority": authority})
    user_id = result.fetchone()[0]
    print(user_id)
    db.session.commit()
    return redirect("/newuser")

@app.route("/createlang", methods=["POST"])
def createlang():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
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
    return redirect("/")

@app.route("/creategame", methods=["POST"])
def creategame():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    gamename = request.form["gamename"]
    lang_id = request.form["lang_id"]
    sql = "SELECT * FROM games WHERE gamename=:gamename"
    result = db.session.execute(sql, {"gamename":gamename})
    if result.fetchone():
        print("game exists")
        return redirect("/newgame") # to add: errormessage
    sql = "INSERT INTO games (gamename, lang_id, creator_id) VALUES (:gamename, :lang_id, :user_id) RETURNING id"
    result = db.session.execute(sql, {"gamename":gamename, "lang_id":lang_id, "user_id": session["user_id"]})
    games_id = result.fetchone()[0]
    print("games id " + str(games_id))
    sentences = request.form.getlist("sentence")
    rightanswers = request.form.getlist("rightanswer")
    for i in range(len(sentences)):
        if (len(sentences[i])) == 0:
            break
        sql = "INSERT INTO sentences (games_id, info, rightanswer) VALUES (:games_id, :info, :rightanswer)"
        db.session.execute(sql, {"games_id": games_id, "info": sentences[i], "rightanswer": rightanswers[i]})
    db.session.commit()
    return redirect("/omatpelit")

@app.route("/createschool", methods=["POST"])
def createschool():
    schoolname = request.form["schoolname"]
    info = request.form["info"]
    address = request.form["address"]
    phone = request.form["phone"]
    www = request.form["www"]
    sql = "INSERT INTO schools (schoolname, info, address, phone, www, visible) VALUES (:schoolname, :info, :address, :phone, :www, :visible) RETURNING id"
    result = db.session.execute(sql, {"schoolname":schoolname, "info": info, "address": address, "phone": phone, "www": www, "visible": True})
    school_id = result.fetchone()[0]
    sql = "INSERT INTO schooladmins (user_id, school_id) VALUES (:user_id, :school_id)"
    db.session.execute(sql, {"user_id":session["user_id"], "school_id": school_id})
    db.session.commit()
    session["school"] = school_id
    return redirect("/")

@app.route("/editschool", methods=["POST"])
def saveeditschool():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    schoolname = request.form["schoolname"]
    info = request.form["info"]
    address = request.form["address"]
    phone = request.form["phone"]
    www = request.form["www"]
    sql = "SELECT schoolname FROM schools WHERE id=:id"
    result = db.session.execute(sql, {"id": session["school"]})
    oldname = result.fetchone()[0]
    if oldname != schoolname: # someone wants to change the name of the school
        sql = "SELECT * FROM schools WHERE schoolname=:schoolname"
        result = db.session.execute(sql, {"schoolname": schoolname})
        if result.fetchone():
            print("the school already exists")
            return redirect("/kouluhallinta")
    sql = "UPDATE schools SET schoolname=:schoolname, info=:info, address=:address, phone=:phone, www=:www WHERE id=:id"
    db.session.execute(sql, {"schoolname": schoolname, "info": info, "address": address, "phone": phone, "www": www, "id": session["school"]})
    db.session.commit()
    return redirect("/kouluhallinta")

@app.route("/createcourse", methods=["POST"])
def createcourse():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    coursename = request.form["coursename"]
    info = request.form["info"]
    sql = "INSERT INTO courses (coursename, info, school_id) VALUES (:coursename, :info, :school_id) RETURNING id"
    result = db.session.execute(sql, {"coursename":coursename, "info": info, "school_id": session["school"]})
    course_id = result.fetchone()[0]
    db.session.commit()
    session["course"] = course_id
    return redirect("/kielivalinta")

@app.route("/kielivalinta")
def chooselang():
    if not session.get("user_id"):
        return redirect("/")
    if session["authority"] != 2:
        return redirect("/") #only schooladmins can create courses
    sql = "SELECT langname FROM langs ORDER BY langname"
    result = db.session.execute(sql)
    langs = result.fetchall()
    sql = "SELECT coursename FROM courses WHERE id=:course_id"
    result = db.session.execute(sql, {"course_id":session["course"]})
    coursename = result.fetchone()[0]
    return render_template("chooselang.html", langs=langs, coursename=coursename)

@app.route("/pelivalinta/<langname>")
def choosegame(langname):
    if not session.get("user_id"):
        return redirect("/")
    if session["authority"] != 2:
        return redirect("/") #only schooladmins can create courses
    langname = langname.capitalize()
    sql = "SELECT id FROM langs where langname=:langname"
    result = db.session.execute(sql, {"langname":langname})
    result = result.fetchone()
    if (result):
        lang_id = result[0]
        sql = "SELECT games.id, games.gamename FROM games LEFT JOIN coursegames ON games.id=coursegames.game_id WHERE games.lang_id=:lang_id AND coursegames.game_id is null"
        result = db.session.execute(sql, {"lang_id":lang_id, "course_id": session["course"]})
        games = result.fetchall()
        sql = "SELECT coursename FROM courses WHERE id=:course_id"
        result = db.session.execute(sql, {"course_id":session["course"]})
        coursename = result.fetchone()[0]
        sql = "SELECT game_id from coursegames WHERE course_id=:course_id"
        result = db.session.execute(sql, {"course_id":session["course"]})
        chosen = result.fetchall()
        print(chosen)
        session["langname"] = langname
        return render_template("chooselang.html", games=games, coursename=coursename, chosen=chosen)
    return redirect("/kielivalinta")

@app.route("/choosegame", methods=["POST"])
def coursegame():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    games = request.form.getlist("game")
    print(games, session["course"])
    for game in games:
        sql = "INSERT INTO coursegames (game_id, course_id) VALUES (:game_id, :course_id)"
        result = db.session.execute(sql, {"game_id": game, "course_id": session["course"]})
        db.session.commit()
    return redirect("/pelivalinta/" + session["langname"])