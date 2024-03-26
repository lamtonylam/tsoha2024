from flask import Flask
from flask import redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///tony"
db = SQLAlchemy(app)





@app.route("/")
def index():
    return render_template("index.html")

@app.route("/kirjautunut")
def kirjautnut():
    query = text('SELECT nimi, hankintapaikka FROM Merkit;')
    result = db.session.execute(query)
    results = result.fetchall()
    return render_template("kirjautunut.html", results=results)

@app.route("/new")
def new():
    return render_template("new.html")

@app.route("/send", methods=["POST"])
def send():
    nimi = request.form.get("nimi")
    hankintapaikka = request.form.get("hankintapaikka")

    sql = text("INSERT INTO Merkit(nimi, hankintapaikka) VALUES (:nimi, :hankintapaikka)")  
    db.session.execute(sql, {"nimi": nimi, "hankintapaikka": hankintapaikka})
    db.session.commit()

    return redirect("/sisaankirjautunut")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return render_template("error.html", message="Salasanat eroavat")
        if users.register(username, password1):
            return redirect("/")
        else:
            return render_template("error.html", message="Rekisteröinti ei onnistunut")