from flask import Flask
from flask import redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///user"
db = SQLAlchemy(app)



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sisaankirjautunut")
def kirjautnut():
    return render_template("kirjautunut.html")

@app.route("/new")
def new():
    return render_template("new.html")

@app.route("/send", methods=["POST"])
def send():
    nimi = request.form["nimi"]
    tapahtuma_vai_ostettu = request.form["tapahtuma_vai_ostettu"]

    sql = "INSERT INTO Merkit(nimi, tapahtuma_vai_ostettu) VALUES (:nimi, :tapahtuma_vai_ostettu)"
    db.session.execute(sql, {"nimi":nimi, "tapahtuma_vai_ostettu":tapahtuma_vai_ostettu})
    db.session.commit()

    return redirect("/sisaankirjautunut")