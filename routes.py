from app import app
from flask import redirect, render_template, request, session, flash 
from os import abort
from os import getenv
from db import db
#import modules.gamez as gamez
from modules import users, languages, schoolz, coursez, gamez
#import users, languages, schoolz, coursez

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
    if (users.login(request.form)):
        return redirect("/")
    flash("Tarkista kirjautumistiedot", "error")    
    return render_template("index.html")

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

@app.route("/tulostaulu")
def scores():
    if users.credentials(None, None):
        if session.get("langname"):#if returning from editing courses
            del session["langname"]
        if session.get("course"):#if returning from editing courses
            del session["course"]
    return render_template("index.html", scores=gamez.scores())

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
    courses = coursez.getRelevant(game_id)
    return render_template("game.html", courses=courses, gamename=game[0], sentences=game[1])

@app.route("/kurssi/<int:id>")
def course(id):
    course = coursez.getPres(id)
    if course:
        return render_template("course.html", course=course)
    return redirect("/")#someone tried something funny

@app.route("/kouluhallinta")
def editschool():
    if not users.credentials(None, "school"):
        return redirect("/")
    school = schoolz.get()
    return render_template("editschool.html", school=school)

@app.route("/playgame", methods=["POST"]) # to add here: page to show result from current game
def playgame():
    result = gamez.checkResult(request.form.getlist("answer"))
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
    if(languages.create(request.form)):
        return redirect("/")
    return redirect("/luokieli")

@app.route("/creategame", methods=["POST"])
def creategame():
    if (gamez.create(request.form)):
        return redirect("/omatpelit")
    return redirect("/luopeli")

@app.route("/createschool", methods=["POST"])
def createschool():
    if schoolz.create(request.form):
        return redirect("/")
    return redirect("/luokoulu")

@app.route("/editschool", methods=["POST"])
def saveeditschool():
    schoolz.edit(request.form)
    return redirect("/kouluhallinta")

@app.route("/createcourse", methods=["POST"])
def createcourse():
    if coursez.create(request.form):
        return redirect("/kurssivalinta")
    return redirect("/luokurssi")

@app.route("/editcourse", methods=["POST"])
def editcourse():
    coursez.edit(request.form)
    return redirect("/kurssihallinta/" + str(session["course"]))

@app.route("/choosegame", methods=["POST"])
def coursegame():
    gamez.choose(request.form)
    return redirect("/kurssihallinta/"+str(session["course"]) +"/"+ session["langname"])

@app.route("/unchoosegame", methods=["POST"])
def delcoursegame():
    gamez.unchoose(request.form)
    if session.get("langname"):#game was unchosen from gamemenu
        return redirect("/kurssihallinta/"+str(session["course"]) +"/"+ session["langname"])
    return redirect("/kurssihallinta/" + str(session["course"]))

@app.route("/hidegame", methods=["POST"])
def hidegame():
    gamez.hide(request.form)
    return redirect("/omatpelit")

@app.route("/showgame", methods=["POST"])
def showgame():
    gamez.show(request.form)
    return redirect("/omatpelit")

@app.route("/kurssivalinta")
def choosecourse():
    if not users.credentials(2, None):
        return redirect("/")
    return render_template("courselist.html", courses=coursez.get())

@app.route("/kurssihallinta/<int:id>")
def managecourse(id):
    if not users.credentials(2, None):
        return redirect("/")
    if session.get("langname"):
        del session["langname"]
    course = coursez.check(id)
    if course:
        session["course"] = id
        return render_template("editcourse.html", course=course, games=gamez.getchosen())
    return redirect("/kurssivalinta")#someone tried something funny, didn't work out

@app.route("/kurssihallinta/<int:id>/kielet")
def managecourselangs(id):
    if not users.credentials(2, None):
        return redirect("/")
    course = coursez.check(id)
    if course:
        session["course"] = id
        return render_template("editcourse.html", course=course, games=gamez.getchosen(), langs=languages.get())
    return redirect("/kurssivalinta")#someone tried something funny, didn't work out

@app.route("/kurssihallinta/<int:id>/<langname>")
def managecoursegames(id, langname):
    if not users.credentials(2, None):
        return redirect("/")
    lang_id = languages.getId(langname)
    if (lang_id):
        session["langname"] = langname
        course = coursez.check(id)
        if course:
            return render_template("editcourse.html", langs=languages.get(), gameview=True, course=course, games=gamez.getByLang(lang_id), chosen=gamez.getchosen())
    return redirect("/kurssivalinta")#someone tried something funny, didn't work out