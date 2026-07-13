from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, quests_dao, users_dao
from flask_login import LoginManager, login_user, logout_user, login_required
from models import User
from datetime import date, datetime

from werkzeug.security import generate_password_hash, check_password_hash

from PIL import Image

app = Flask(__name__)
app.config["SECRET_KEY"] = "Key for Valley of the Wind Fantasy Adventure Guild"

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_user = users_dao.get_user_by_id(p_id=user_id)

    if db_user is None:
        return None

    return User(db_user["id"], db_user["username"], db_user["password"], db_user["role"])


@app.route('/')
def home():
    db_quests = quests_dao.get_quests()
    return render_template('home.html', quests=db_quests)

@app.route('/quests')
def quest_page():
    db_quests = quests_dao.get_quests()
    return render_template('quest_page.html', quests=db_quests)

@app.route('/quests/<int:quest_id>')
def quest_detail(quest_id):
    db_quest = quests_dao.get_quest_by_id(p_quest_id=quest_id)

    if db_quest is None:
        return redirect(url_for("error"))

    db_sessions = quests_dao.get_sessions_by_quest_id(p_quest_id=quest_id)
    day_names = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
        7: "Sunday",
    }

    return render_template('quest_page.html', quest=db_quest, sessions=db_sessions, day_names=day_names)

@app.route('/adventurer_profile')
def adventurer_profile():
    return render_template('adventurer_profile.html')

@app.route('/guild_master_profile')
def guild_master_profile():
    return render_template('guild_master_profile.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    return render_template('login.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template('register.html')

    username = request.form.get("txt_username")
    password = generate_password_hash(request.form.get("txt_password"))
    role = request.form.get("txt_role")

    if users_dao.username_exists(p_username=username):
        flash("username already exists")
        return redirect(url_for("register"))

    users_dao.new_user(p_username=username, p_password=password, p_role=role)

    return redirect(url_for("home"))

@app.route("/authenticate", methods=["POST"])
def authenticate():
    form_user = request.form.to_dict()

    db_user = users_dao.get_user_by_username(form_user["txt_username"])

    if not db_user:
        # print("The user does not exist")
        flash("The user does not exist", "danger")
        return redirect(url_for("login"))
    
    if not check_password_hash(db_user[2], form_user["txt_password"]):
        # print("The password is wrong")
        flash("The password is wrong", "danger")
        return redirect(url_for("login"))

    new = User(
        id=db_user["id"],
        username=db_user["username"],
        password=db_user["password"],
        role=db_user["role"]
    )

    result = login_user(new)
    flash("Welcome back! " + db_user["username"] + "!", "success")
    # print(result)

    return redirect(url_for("home"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))
