import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId


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
    product_list = list(
        db.products.find({
            "status": "active"
        })
    )

    return render_template(
        "products.html",
        products=product_list
    )


@app.route("/plans")
def plans():
    plan_list = list(
        db.plans.find({
            "status": "active"
        })
    )

    return render_template(
        "plans.html",
        plans=plan_list
    )


@app.route("/subscribe/<plan_id>")
def subscribe(plan_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    plan = db.plans.find_one({
        "_id": ObjectId(plan_id)
    })

    if not plan:
        return redirect(url_for("plans"))

    # Cancel any currently active subscription
    db.subscriptions.update_many(
        {
            "user_id": session["user_id"],
            "status": "active"
        },
        {
            "$set": {
                "status": "cancelled"
            }
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
            "$set": {
                "status": "cancelled"
            }
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

    # Financial summary
    paid_invoices = list(
        db.invoices.find({
            "status": "paid"
        })
    )

    outstanding_invoices = list(
        db.invoices.find({
            "status": {
                "$in": ["draft", "confirmed"]
            }
        })
    )

    total_revenue = sum(
        invoice.get("amount", 0)
        for invoice in paid_invoices
    )

    amount_owed = sum(
        invoice.get("amount", 0)
        for invoice in outstanding_invoices
    )
    now = datetime.now()

    outstanding_count = len(outstanding_invoices)

    overdue_invoices = []

    for invoice in outstanding_invoices:
        due_date = invoice.get("due_date")

        if not due_date:
            due_date = invoice.get("created_at", now) + timedelta(days=7)

            db.invoices.update_one(
               {"_id": invoice["_id"]},
               {"$set": {"due_date": due_date}}
        )

        invoice["due_date"] = due_date

        if due_date < now:
           overdue_invoices.append(invoice)
 
    overdue_count = len(overdue_invoices)

    customers = list(
        db.users.find(
            {
                "role": "customer"
            },
            {
                "password": 0
            }
        )
    )

    staff_members = list(
    db.users.find(
        {"role": "staff"},
        {"password": 0}
    )
)

    subscriptions = list(
        db.subscriptions.find().sort(
            "created_at",
            -1
        )
    )

    invoice_list = list(
    db.invoices.find().sort(
        "created_at",
        -1
    )
)

    return render_template(
    "admin.html",
    total_users=total_users,
    active_subscriptions=active_subscriptions,
    total_plans=total_plans,
    total_revenue=total_revenue,
    amount_owed=amount_owed,
    outstanding_count=outstanding_count,
    overdue_count=overdue_count,
    customers=customers,
    staff_members=staff_members,
    subscriptions=subscriptions,
    invoices=invoice_list
)


@app.route("/generate-invoice")
def generate_invoice():
    if "user_id" not in session:
        return redirect(url_for("login"))

    subscription = db.subscriptions.find_one({
        "user_id": session["user_id"],
        "status": "active"
    })

    if not subscription:
        return redirect(url_for("dashboard"))

    existing_invoice = db.invoices.find_one({
        "subscription_id": str(subscription["_id"]),
        "status": {
            "$in": ["draft", "confirmed"]
        }
    })

    if existing_invoice:
        return redirect(url_for("invoices"))

    invoice = {
        "subscription_id": str(subscription["_id"]),
        "user_id": session["user_id"],
        "customer_name": session["user_name"],
        "customer_email": session.get("user_email", ""),
        "plan_name": subscription["plan_name"],
        "amount": subscription["price"],
        "status": "draft",
        "created_at": datetime.now()
    }

    db.invoices.insert_one(invoice)

    return redirect(url_for("invoices"))


@app.route("/invoices")
def invoices():
    if "user_id" not in session:
        return redirect(url_for("login"))

    invoice_list = list(
        db.invoices.find({
            "user_id": session["user_id"]
        }).sort("created_at", -1)
    )

    return render_template(
        "invoices.html",
        invoices=invoice_list
    )


@app.route("/confirm-invoice/<invoice_id>")
def confirm_invoice(invoice_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db.invoices.update_one(
        {
            "_id": ObjectId(invoice_id),
            "user_id": session["user_id"],
            "status": "draft"
        },
        {
            "$set": {
                "status": "confirmed"
            }
        }
    )

    return redirect(url_for("invoices"))


@app.route("/pay-invoice/<invoice_id>")
def pay_invoice(invoice_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    invoice = db.invoices.find_one({
        "_id": ObjectId(invoice_id),
        "user_id": session["user_id"],
        "status": "confirmed"
    })

    if not invoice:
        return redirect(url_for("invoices"))

    return render_template(
        "payment.html",
        invoice=invoice
    )


@app.route("/record-payment/<invoice_id>", methods=["POST"])
def record_payment(invoice_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    invoice = db.invoices.find_one({
        "_id": ObjectId(invoice_id),
        "user_id": session["user_id"],
        "status": "confirmed"
    })

    if not invoice:
        return redirect(url_for("invoices"))

    payment = {
        "invoice_id": str(invoice["_id"]),
        "user_id": session["user_id"],
        "customer_name": session["user_name"],
        "customer_email": session.get("user_email", ""),
        "payment_method": request.form["payment_method"],
        "amount": invoice["amount"],
        "payment_date": datetime.now(),
        "note": request.form.get("note", "")
    }

    db.payments.insert_one(payment)

    db.invoices.update_one(
        {
            "_id": invoice["_id"]
        },
        {
            "$set": {
                "status": "paid",
                "paid_at": datetime.now()
            }
        }
    )

    return redirect(url_for("invoices"))

@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    product = {
        "name": request.form.get("name", "").strip(),
        "type": request.form.get("type", "").strip(),
        "sales_price": float(request.form.get("sales_price", 0)),
        "cost_price": float(request.form.get("cost_price", 0)),
        "notes": request.form.get("notes", "").strip(),
        "status": "active",
        "created_at": datetime.now()
    }

    db.products.insert_one(product)

    return redirect(url_for("admin"))


@app.route("/admin/add-plan", methods=["POST"])
def add_plan():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    plan = {
        "name": request.form.get("name", "").strip(),
        "price": float(request.form.get("price", 0)),
        "billing_cycle": request.form.get("billing_cycle", "month"),
        "minimum_quantity": int(request.form.get("minimum_quantity", 1)),
        "status": "active",
        "created_at": datetime.now()
    }

    db.plans.insert_one(plan)

    return redirect(url_for("admin"))

@app.route("/admin/add-staff", methods=["POST"])
def add_staff():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if db.users.find_one({"email": email}):
        return redirect(url_for("admin"))

    if len(password) <= 8:
        return redirect(url_for("admin"))

    if (
        not re.search(r"[A-Z]", password)
        or not re.search(r"[a-z]", password)
        or not re.search(r"[^A-Za-z0-9]", password)
    ):
        return redirect(url_for("admin"))

    staff = {
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "role": "staff",
        "created_at": datetime.now()
    }

    db.users.insert_one(staff)

    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)