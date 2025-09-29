import os
import datetime
from PIL import Image
import sqlite3

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///daily.db")

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    if request.method == "POST":
        user_id = session['user_id']

        cash = request.form.get("cash")
        if not cash:
            return apology("must provide the amount of cash", 400)

        user_cash = db.execute("SELECT cash from users WHERE id = ?", user_id)
        update_cash = float(user_cash[0]["cash"]) + float(cash)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", update_cash, user_id)

        flash("Updated the amount of cash!")
        return redirect("/expenditure")

    else:
        return render_template("cash.html")

@app.route("/debit", methods=["GET", "POST"])
@login_required
def debit():
    if request.method == "POST":
        user_id = session['user_id']

        debit = request.form.get("debit")
        if not debit:
            return apology("must provide the amount of debit account", 400)

        user_debit = db.execute("SELECT debit from users WHERE id = ?", user_id)
        update_debit = float(user_debit[0]["debit"]) + float(debit)
        db.execute("UPDATE users SET debit = ? WHERE id = ?", update_debit, user_id)

        flash("Updated debit account!")
        return redirect("/expenditure")

    else:
        return render_template("debit.html")

@app.route("/credit", methods=["GET", "POST"])
@login_required
def credit():
    if request.method == "POST":
        user_id = session['user_id']

        credit = request.form.get("credit")
        if not credit:
            return apology("must provide the amount of credit account", 400)

        user_credit = db.execute("SELECT credit from users WHERE id = ?", user_id)
        update_credit = float(user_credit[0]["credit"]) + float(credit)
        db.execute("UPDATE users SET credit = ? WHERE id = ?", update_credit, user_id)

        flash("Updated credit account!")
        return redirect("/expenditure")

    else:
        return render_template("credit.html")

@app.route("/loan", methods=["GET", "POST"])
@login_required
def loan():
    if request.method == "POST":
        user_id = session['user_id']

        loan = request.form.get("loan")
        if not loan:
            return apology("must provide the amount of loan", 400)

        user_loan = db.execute("SELECT loan from users WHERE id = ?", user_id)
        update_loan = float(user_loan[0]["loan"]) + float(loan)
        db.execute("UPDATE users SET loan = ? WHERE id = ?", update_loan, user_id)

        flash("Updated the amount of loan!")
        return redirect("/expenditure")

    else:
        return render_template("loan.html")

@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
    # Remember user_id
    user_id = session['user_id']

    if request.method == "POST":
        name = request.form.get("outcome")
        if not name:
            return apology("must provide description", 400)

        value = request.form.get("value")
        if not value:
            return apology("must provide the amount of expenditure", 400)

        money = float(value)
        if float(money) < 0:
            return apology("must a positive number", 400)

        count_activities = db.execute("SELECT MAX(id) FROM outcome WHERE user_id = ?", user_id)

        if count_activities[0]["MAX(id)"] == None:
            db.execute("INSERT INTO outcome (name, money, user_id, date) VALUES (?, ?, ?, ?)", name, money, user_id, datetime.datetime.now().date())

        elif count_activities[0]["MAX(id)"] != None:
            activities = db.execute("SELECT name FROM outcome WHERE user_id = ? AND date = ?", user_id, datetime.datetime.now().date())

            if name in activities:
                db.execute("UPDATE outcome SET money = money + :money WHERE user_id = :user_id AND name = :name AND date = :date", money=money, user_id=user_id, name=name, date=datetime.datetime.now().date())

            if name not in activities:
                db.execute("INSERT INTO outcome (name, money, user_id, date) VALUES (?, ?, ?, ?)", name, money, user_id, datetime.datetime.now().date())

        flash("Added an expenditure!")
        return redirect("/expenditure")

    else:
        return render_template("expense.html")

@app.route("/expenditure", methods=["GET"])
@login_required
def expenditure():

    # Remember user_id
    user_id = session['user_id']

    user_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    cash = float(user_cash[0]["cash"])
    user_debit = db.execute("SELECT debit FROM users WHERE id = ?", user_id)
    debit = float(user_debit[0]["debit"])
    user_credit = db.execute("SELECT credit FROM users WHERE id = ?", user_id)
    credit = float(user_credit[0]["credit"])
    user_loan = db.execute("SELECT loan FROM users WHERE id = ?", user_id)
    loan = float(user_loan[0]["loan"])

    outcomes = db.execute("SELECT name, money, date FROM outcome WHERE user_id = ?", user_id)
    total = 0
    for outcome in outcomes:
        money = outcome["money"]
        total = total + money

    total = total
    balance = cash + debit + credit - loan - total

    return render_template("expenditure.html", cash=cash, debit=debit, credit=credit, loan=loan, outcomes=outcomes, total = total, balance = balance)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():

    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password was reepeated
        elif not request.form.get("confirmation"):
            return apology("must repeat password", 400)

        # Password confirmation
        password = request.form.get("password")
        generate_password_hash(password)
        confirmation = request.form.get("confirmation")
        generate_password_hash(confirmation)
        if password != confirmation:
            return apology("password does not match", 400)

        # Query database for username
        username = request.form.get("username")
        select_usernames = db.execute("SELECT username FROM users")

        # Ensure the username is unique
        if username in select_usernames:
            return apology("the username already exists", 400)

        # Query database for insert new users
        if not select_usernames or username not in select_usernames:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))
            db.execute("INSERT INTO infor (user_id) VALUES ((SELECT id FROM users WHERE username = ?))", username)
            # Redirect user to login page
            return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def infor():
    # Remember user_id
    user_id = session['user_id']

    if request.method == "POST":

        name = request.form.get("name")
        if not name:
            return apology("must provide name", 400)

        birth = request.form.get("birth")
        if not birth:
            return apology("must provide birth", 400)

        gender = request.form.get("gender")
        if not gender:
            return apology("must provide gender", 400)

        phone = request.form.get("phone")
        if not phone:
            return apology("must provide name", 400)

        email = request.form.get("email")
        if not email:
            return apology("must provide name", 400)

        url = request.form.get("url")

        # Check for the available users
        available = db.execute("SELECT user_id FROM infor WHERE user_id = ?", user_id) #should make a list
        user = []
        for i in range (1):
            user.append(available[0]["user_id"])
        if user_id in user:
            db.execute("UPDATE infor SET name = ?, birth = ?, gender = ?, phone = ?, email = ?, url = ? WHERE user_id = ?", name, birth, gender, phone, email, url, user_id)
        if user_id not in user:
            db.execute("INSERT INTO infor (user_id, name, birth, gender, phone, email, url) VALUES (?, ?, ?, ?, ?, ?, ?)", user_id, name, birth, gender, phone, email, url)
        return redirect("/profile")
    else:
        image = db.execute("SELECT url FROM infor WHERE user_id = ?", user_id)
        url = image[0]["url"]

        user_info = db.execute("SELECT name, birth, gender, phone, email FROM infor WHERE user_id = ?", user_id)
        name = user_info[0]["name"]
        birth = user_info[0]["birth"]
        gender = user_info[0]["gender"]
        phone = user_info[0]["phone"]
        email = user_info[0]["email"]

        return render_template("profile.html", url=url, name=name, birth=birth, gender=gender, phone=phone, email=email)

@app.route("/change_password", methods=["GET", "POST"])
def change():
    # Remember user_id
    user_id = session['user_id']

    if request.method == "POST":
        new = request.form.get("new")
        if not new:
            return apology("must provide new passwoord", 400)

        confirmation = request.form.get("confirmation")
        if not confirmation:
            return apology("must confirm new password", 400)

        if new != confirmation:
            return apology("password does not match")
        if new == confirmation:
            db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(new), user_id)
            return redirect("/login")

    else:
        return render_template("change_password.html")

@app.route("/cook", methods=["GET", "POST"])
def cook():
    # Remember user_id
    user_id = session['user_id']
    if request.method == "POST":
        # Delete
        delete = request.form.get("delete")
        if delete != None:
            count = db.execute("SELECT MAX(id) FROM cook WHERE user_id = ?", user_id)
            if count[0]["MAX(id)"] == None:
                flash("There is nothing to delete")
                return render_template("cook.html", cooks = cooks)
            elif count[0]["MAX(id)"] != None:
                deletes = db.execute("DELETE FROM cook WHERE name = ? AND user_id = ?", delete, user_id)

                if not deletes:
                    return apology("Invalid name of dish", 400)
                else:
                    return redirect("/cook")

        # Add
        name = request.form.get("name")
        if not name:
            return apology ("must provide name", 400)

        description = request.form.get("description")

        ingredient = request.form.get("ingredient")
        if not ingredient:
            return apology ("must provide ingredient", 400)

        pre_time = float(request.form.get("pre_time"))
        if not pre_time or pre_time <= 0:
            return apology ("must have a positive preparation time", 400)

        cook_time = float(request.form.get("cook_time"))
        if not cook_time or cook_time <= 0:
            return apology ("must have a positive cook time", 400)

        url = request.form.get("url")

        how = request.form.get("how")

        count_dishes = db.execute("SELECT MAX(id) FROM cook WHERE user_id = ?", user_id)
        if count_dishes[0]["MAX(id)"] == None:
            db.execute("INSERT INTO cook (user_id, name, description, ingredient, pre_time, cook_time, url, how) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", user_id, name, description, ingredient, pre_time, cook_time, url, how)

        elif count_dishes[0]["MAX(id)"] != None:
            count = count_dishes[0]["MAX(id)"]
            list_dishes = db.execute("SELECT name FROM cook WHERE user_id = ?", user_id)

            if name in list_dishes:
                db.execute("UPDATE cook SET description = ?, ingredient = ?, pre_time = ?, cook_time = ?, url = ?, how =? WHERE user_id = ? AND name = ?", description, ingredient, pre_time, cook_time, url, how, user_id, name)

            if name not in list_dishes:
                db.execute("INSERT INTO cook (user_id, name, description, ingredient, pre_time, cook_time, url, how) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", user_id, name, description, ingredient, pre_time, cook_time, url, how)
        return redirect("/cook")
    else:
        cooks = db.execute("SELECT name, description, ingredient, pre_time, cook_time, url, how FROM cook WHERE user_id = ?", user_id)
        for cook in cooks:
            url = cook["url"]

        return render_template("cook.html", cooks = cooks)

@app.route("/new_recipe", methods=["GET"])
def recipe():
    # Remember user_id
    user_id = session['user_id']

    count_dishes = db.execute("SELECT MAX(id) FROM cook")
    if count_dishes[0]["MAX(id)"] == None:
        return render_template("nothing.html")
    elif count_dishes[0]["MAX(id)"] != None:
        count = count_dishes[0]["MAX(id)"]
        list_dishes = db.execute("SELECT users.username, cook.name, cook.description, cook.ingredient, cook.pre_time, cook.cook_time, cook.url, cook.how FROM cook, users WHERE cook.user_id = users.id AND users.id = (SELECT user_id FROM cook EXCEPT SELECT user_id FROM cook WHERE user_id = ?)", user_id)
        return render_template("dishes.html", list_dishes = list_dishes)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
