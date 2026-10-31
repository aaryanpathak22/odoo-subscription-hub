import os

from dotenv import load_dotenv
import re

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

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
        session["user_email"] = user["email"]
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

    subscription = db.subscriptions.find_one({
        "user_id": session["user_id"],
        "status": "active"
    })

    subscription_history = list(
        db.subscriptions.find({
            "user_id": session["user_id"]
        }).sort("_id", -1)
    )

    return render_template(
        "dashboard.html",
        subscription=subscription,
        subscription_history=subscription_history
    )

@app.route("/products")
def products():
    product_list = list(db.products.find({"status": "active"}))

    return render_template(
        "products.html",
        products=product_list
    )

@app.route("/plans")
def plans():
    plan_list = list(db.plans.find({"status": "active"}))

    return render_template(
        "plans.html",
        plans=plan_list
    )


@app.route("/subscribe/<plan_id>")
def subscribe(plan_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    plan = db.plans.find_one({"_id": ObjectId(plan_id)})

    if not plan:
        return redirect(url_for("plans"))
    db.subscriptions.update_many(
    {
        "user_id": session["user_id"],
        "status": "active"
    },
    {
        "$set": {"status": "cancelled"}
    }
)
    subscription = {
    "user_id": session["user_id"],
    "user_name": session["user_name"],
    "user_email": session.get("user_email", ""),
    "plan_id": str(plan["_id"]),
    "plan_name": plan["name"],
    "price": plan["price"],
    "billing_cycle": plan["billing_cycle"],
    "status": "active",
    "created_at": datetime.now()
}

    db.subscriptions.insert_one(subscription)

    return redirect(url_for("dashboard"))

@app.route("/cancel-subscription")
def cancel_subscription():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db.subscriptions.update_one(
        {
            "user_id": session["user_id"],
            "status": "active"
        },
        {
            "$set": {"status": "cancelled"}
        }
    )

    return redirect(url_for("dashboard"))

@app.route("/admin")
def admin():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    total_users = db.users.count_documents({
        "role": "customer"
    })

    active_subscriptions = db.subscriptions.count_documents({
        "status": "active"
    })

    total_plans = db.plans.count_documents({
        "status": "active"
    })

    customer_list = list(
        db.users.find(
            {"role": "customer"},
            {"password": 0}
        )
    )
    subscriptions = list(
        db.subscriptions.find().sort("created_at", -1)
 )
    return render_template(
        "admin.html",
        total_users=total_users,
        active_subscriptions=active_subscriptions,
        total_plans=total_plans,
        customers=customer_list,
        subscriptions=subscriptions
    )

if __name__ == "__main__":
    app.run(debug=True)