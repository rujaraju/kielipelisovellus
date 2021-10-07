from app import app
from flask import redirect, render_template, request, session, flash 
from os import abort
from os import getenv
from db import db
import users, languages, gamez, schoolz

app.secret_key = getenv("SECRET_KEY")

@app.route("/luotunnukset")
def newuser():
    if users.credentials(None, None):
        return redirect("/")
    return render_template("newuser.html")

@app.route("/luokurssi")
def newcourse():
    if not users.credentials(2, None):
        return redirect("/")
    return render_template("newcourse.html")

@app.route("/luokieli")
def newlanguage():
    if not users.credentials(10000, None):#only admins can add languages
        return redirect("/")
    return render_template("newlanguage.html")

@app.route("/luopeli")
def newgame():
    if not users.credentials(1, None):
        return redirect("/")
    langs = languages.get()
    return render_template("newgame.html", langs=langs)

@app.route("/luokoulu")
def newschool():
    return render_template("newschool.html")

@app.route("/login",methods=["POST"]) # add message if wrong credentials
def login():
    username = request.form["username"]
    passwToCheck = request.form["passw"]
    if len(username) > 0 and len(passwToCheck) > 0:
        if(users.login(username, passwToCheck)):
            return redirect("/")    
    return render_template("index.html", error="Tarkista kirjautumistietosi.")

@app.route("/logout")
def logout():
    users.logout()
    return redirect("/")

@app.route("/")
def index():
    if users.credentials(None, None):
        if session.get("langname"):#if returning from editing courses
            del session["langname"]
        if session.get("course"):#if returning from editing courses
            del session["course"]
    langs = languages.get()
    return render_template("index.html", langs=langs)

@app.route("/omatpelit")
def ownGames():
    games = gamez.get()
    return render_template("owngames.html", games=games)

@app.route("/kieli/<langname>")
def language(langname):
    if not users.credentials(None, None):
        return redirect("/")
    lang_id = languages.getId(langname)
    if (lang_id):
        return render_template("games.html", games=gamez.getByLang(lang_id))
    return redirect("/")

@app.route("/peli/<int:game_id>")
def game(game_id):
    if not users.credentials(None, None):
        return redirect("/")
    game = gamez.getGame(game_id)
    return render_template("game.html", gamename=game[0], sentences=game[1])

@app.route("/kouluhallinta")
def editschool():
    if not users.credentials(None, "school"):
        return redirect("/")
    school = schoolz.get()
    return render_template("editschool.html", school=school)

@app.route("/playgame", methods=["POST"]) # to add here: page to show result from current game
def playgame():
    answers = request.form.getlist("answer")
    result = gamez.checkResult(answers)
    if result[0]:
        flash("Onnittelut, ansaitsit " + str(result[1]) + " pistettä!", "message")#move to gamezmodule?
    else:
        flash("Sait " + str(result[1]) + " pistettä, mutta tämä ei ollut parempaa tulosta kuin viimeksi", "message")
    return redirect("/")

@app.route("/createuser", methods=["POST"])
def createuser():
    success = users.addNew(request.form)
    if not success:
        return redirect("/luotunnukset")
    return redirect("/")

@app.route("/createlang", methods=["POST"])
def createlang():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    langname = request.form["langname"]
    if len(langname) < 3:
        flash("Kielen nimi liian lyhyt", "error")
        return redirect("/luokieli")
    langname = langname.capitalize()
    sql = "SELECT * FROM langs WHERE langname=:langname"
    result = db.session.execute(sql, {"langname":langname})
    if result.fetchone():
        flash("Kieli on jo tallennettu", "error")
        return redirect("/luokieli")
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
    sentences = request.form.getlist("sentence")
    rightanswers = request.form.getlist("rightanswer")
    if len(gamename) < 3:
        flash("Kielen nimi on lian lyhyt", "error")
        return redirect("/luopeli")
    if not lang_id:
        flash("Valitse kieli", "error")
        return redirect("/luopeli")
    for i in range(len(sentences)):
        if (len(sentences[i])) == 0:
            if i < 3:
                flash("Kirjoita ainakin kolme lausetta, kiitos", "error")
                return redirect("/luopeli")
    sql = "SELECT * FROM games WHERE gamename=:gamename"
    result = db.session.execute(sql, {"gamename":gamename})
    if result.fetchone():
        flash("Kielen nimi on jo käytössä", "error")
        return redirect("/luopeli")
    sql = "INSERT INTO games (gamename, lang_id, creator_id) VALUES (:gamename, :lang_id, :user_id) RETURNING id"
    result = db.session.execute(sql, {"gamename":gamename, "lang_id":lang_id, "user_id": session["user_id"]})
    games_id = result.fetchone()[0]
    for i in range(len(sentences)):
        if (len(sentences[i])) == 0:
            break
        sql = "INSERT INTO sentences (games_id, info, rightanswer) VALUES (:games_id, :info, :rightanswer)"
        db.session.execute(sql, {"games_id": games_id, "info": sentences[i], "rightanswer": rightanswers[i]})
    db.session.commit()
    return redirect("/omatpelit")

@app.route("/createschool", methods=["POST"])
def createschool():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    schoolname = request.form["schoolname"]
    info = request.form["info"]
    address = request.form["address"]
    phone = request.form["phone"]
    www = request.form["www"]
    if len(schoolname) < 3 or len(info) < 10 or len(address) < 10 or len(phone) < 4 or len(www) < 3:
        flash("Tarkista, että kaikki kentät ovat oikein täytetty", "error")
        return redirect("/luokoulu")
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
    if len(schoolname) < 3 or len(info) < 10 or len(address) < 10 or len(phone) < 4 or len(www) < 3:
        flash("Tarkista, että kaikki kentät ovat oikein täytetty", "error")
        return redirect("/kouluhallinta")
    sql = "SELECT schoolname FROM schools WHERE id=:id"
    result = db.session.execute(sql, {"id": session["school"]})
    oldname = result.fetchone()[0]
    if oldname != schoolname: # someone wants to change the name of the school
        sql = "SELECT * FROM schools WHERE schoolname=:schoolname"
        result = db.session.execute(sql, {"schoolname": schoolname})
        if result.fetchone():
            flash("Tämä koulunimi on jo käytössä muualla", "error")
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
    if len(coursename) < 3 or len(info) < 10:
        flash("Kurssinimi tai -info oli liian lyhyt", "error")
        return redirect("/luokurssi")
    sql = "INSERT INTO courses (coursename, info, school_id) VALUES (:coursename, :info, :school_id) RETURNING id"
    result = db.session.execute(sql, {"coursename":coursename, "info": info, "school_id": session["school"]})
    course_id = result.fetchone()[0]
    db.session.commit()
    session["course"] = course_id
    return redirect("/kielivalinta")

@app.route("/editcourse", methods=["POST"])
def editcourse():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    coursename = request.form["coursename"]
    info = request.form["info"]
    if len(coursename) < 3 or len(info) < 10:
        flash("Kurssinimi tai -info oli liian lyhyt", "error")
        return redirect("/kurssihallinta/" + str(session["course"]))
    sql = "UPDATE courses SET coursename=:coursename, info=:info WHERE id=:id"
    db.session.execute(sql, {"coursename":coursename, "info": info, "id": session["course"]})
    db.session.commit()
    return redirect("/kurssihallinta/" + str(session["course"]))

@app.route("/choosegame", methods=["POST"])
def coursegame():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    game_id = request.form["game_id"]
    sql = "INSERT INTO coursegames (game_id, course_id) VALUES (:game_id, :course_id)"
    db.session.execute(sql, {"game_id": game_id, "course_id": session["course"]})
    db.session.commit()
    return redirect("/kurssihallinta/"+str(session["course"]) +"/"+ session["langname"])

@app.route("/unchoosegame", methods=["POST"])
def delcoursegame():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    game_id = request.form["game_id"]
    sql = "DELETE FROM coursegames WHERE game_id=:game_id AND course_id=:course_id"
    db.session.execute(sql, {"game_id": game_id, "course_id": session["course"]})
    db.session.commit()
    if session.get("langname"):#game was unchosen from gamemenu
        return redirect("/kurssihallinta/"+str(session["course"]) +"/"+ session["langname"])
    return redirect("/kurssihallinta/" + str(session["course"]))

@app.route("/kurssivalinta")
def choosecourse():
    if not users.credentials(2, None):
        return redirect("/")
    sql = "SELECT * from courses WHERE school_id=:school_id AND visible=True"
    result = db.session.execute(sql, {"school_id": session["school"]})
    courses = result.fetchall()
    return render_template("courselist.html", courses=courses)#something ain't right if this happens

@app.route("/kurssihallinta/<int:id>")
def managecourse(id):
    if not users.credentials(2, None):
        return redirect("/")
    if session.get("langname"):
        del session["langname"]
    sql = "SELECT * from courses WHERE id=:id AND school_id=:school_id AND visible=True" #gotta check you're only trying to edit your own school
    result = db.session.execute(sql, {"id": id, "school_id": session["school"]})
    course = result.fetchone()
    if course:
        session["course"] = id
        sql = "SELECT games.id, games.gamename FROM coursegames LEFT JOIN games ON coursegames.game_id=games.id WHERE coursegames.course_id=:course_id"
        result = db.session.execute(sql, {"course_id": session["course"]})
        games = result.fetchall()
        return render_template("editcourse.html", course=course, games=games)
    return redirect("/kurssivalinta")#someone tried something funny, didn't work out

@app.route("/kurssihallinta/<int:id>/kielet")
def managecourselangs(id):
    if not users.credentials(2, None):
        return redirect("/")
    sql = "SELECT * from courses WHERE id=:id AND school_id=:school_id AND visible=True" #gotta check you're only trying to edit your own school
    result = db.session.execute(sql, {"id": id, "school_id": session["school"]})
    course = result.fetchone()
    if course:
        session["course"] = id
        sql = "SELECT games.id, games.gamename FROM coursegames LEFT JOIN games ON coursegames.game_id=games.id WHERE coursegames.course_id=:course_id"
        result = db.session.execute(sql, {"course_id": session["course"]})
        games = result.fetchall()
        sql = "SELECT langname FROM langs ORDER BY langname"
        result = db.session.execute(sql)
        langs = result.fetchall()
        return render_template("editcourse.html", course=course, games=games, langs=langs)
    return redirect("/kurssivalinta")#someone tried something funny, didn't work out

@app.route("/kurssihallinta/<int:id>/<langname>")
def managecoursegames(id, langname):
    if not users.credentials(2, None):
        return redirect("/")
    langname = langname.capitalize()
    sql = "SELECT id FROM langs where langname=:langname"
    result = db.session.execute(sql, {"langname":langname})
    result = result.fetchone()
    if (result):
        lang_id = result[0]
        sql = "SELECT id, gamename FROM games WHERE lang_id=:lang_id;"
        result = db.session.execute(sql, {"lang_id":lang_id})
        games = result.fetchall()
        sql = "SELECT game_id from coursegames WHERE course_id=:course_id"
        result = db.session.execute(sql, {"course_id":session["course"]})
        chosen = result.fetchall()
        session["langname"] = langname
        sql = "SELECT * from courses WHERE id=:id AND school_id=:school_id AND visible=True" #gotta check you're only trying to edit your own school
        result = db.session.execute(sql, {"id": id, "school_id": session["school"]})
        course = result.fetchone()
        if course:
            sql = "SELECT langname FROM langs ORDER BY langname"
            result = db.session.execute(sql)
            langs = result.fetchall()
            return render_template("editcourse.html", langs=langs, gameview=True, course=course, games=games, chosen=chosen)
    return redirect("/kurssivalinta")#someone tried something funny, didn't work out