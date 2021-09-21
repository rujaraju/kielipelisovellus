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
    if (session.get("username")):
        return redirect("/")
    return render_template("newuser.html")
    
@app.route("/login",methods=["POST"])
def login():
    username = request.form["username"]
    passwToCheck = request.form["passw"]
    sql = "SELECT passw, authority, points, firstname FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username": username})
    result = result.fetchone()
    if (result):
        if (result[0] == passwToCheck):
            session["username"] = username
            session["authority"] = result[1]
            session["points"] = result[2]
            session["firstname"] = result[3]
            return redirect("/")    
    return render_template("index.html", message="Tarkista kirjautumistietosi.")

@app.route("/logout")
def logout():
    del session["username"], session["authority"], session["points"], session["firstname"]
    return redirect("/")

@app.route("/")
def index():
    sql = "SELECT langname FROM langs ORDER BY langname"
    result = db.session.execute(sql)
    langs = result.fetchall()
    return render_template("index.html", langs=langs)