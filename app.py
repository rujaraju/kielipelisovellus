#todos: when saving names always capitalize, data security in forms, check that input is ok, game page with score checking

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import getenv, abort
import fixforheroku
import secrets

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = fixforheroku.uri 
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = getenv("SECRET_KEY")

db = SQLAlchemy(app)

import routes