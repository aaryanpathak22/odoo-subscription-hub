import os

from dotenv import load_dotenv
import re

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient


# Load values from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME")]


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Check whether email already exists
        if db.users.find_one({"email": email}):
            return render_template(
                "signup.html",
                error="An account with this email already exists."
            )

        # Password must be more than 8 characters
        if len(password) <= 8:
            return render_template(
                "signup.html",
                error="Password must be more than 8 characters."
            )

        # Password must contain uppercase, lowercase and special character
        if (
            not re.search(r"[A-Z]", password)
            or not re.search(r"[a-z]", password)
            or not re.search(r"[^A-Za-z0-9]", password)
        ):
            return render_template(
                "signup.html",
                error="Password must contain uppercase, lowercase and a special character."
            )

        user = {
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "role": "customer"
        }

        db.users.insert_one(user)

        return render_template(
            "signup.html",
            error=None
        )

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.users.find_one({"email": email})

        if not user or not check_password_hash(user["password"], password):
            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        session["user_id"] = str(user["_id"])
        session["user_name"] = user["name"]
        session["role"] = user["role"]

        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)