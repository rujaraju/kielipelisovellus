from app import app
from flask_sqlalchemy import SQLAlchemy
from os import getenv
import fixforheroku

app.config["SQLALCHEMY_DATABASE_URI"] = fixforheroku.uri 
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True


db = SQLAlchemy(app)