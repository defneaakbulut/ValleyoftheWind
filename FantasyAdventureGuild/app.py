from flask import Flask, render_template, request, redirect, url_for, flash
import quests_dao, users_dao
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User
from datetime import date, datetime
from pathlib import Path

from werkzeug.security import generate_password_hash, check_password_hash

from PIL import Image

QUEST_IMG_HEIGHT = 600
BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["SECRET_KEY"] = "Key for Valley of the Wind Fantasy Adventure Guild"
SIMULATED_DAY_OF_WEEK = 1
SIMULATED_CURRENT_TIME = "09:00"
PARTY_ROLES = {
    "warrior": 4,
    "mage": 3,
    "healer": 2,
}
QUEST_TYPES = ["combat", "exploration", "puzzle", "stealth", "magic", "survival"]
DIFFICULTIES = ["easy", "medium", "hard", "legendary"]
DAYS = [
    (1, "Monday"),
    (2, "Tuesday"),
    (3, "Wednesday"),
    (4, "Thursday"),
    (5, "Friday"),
    (6, "Saturday"),
    (7, "Sunday"),
]
LOCATIONS = ["Valley of the Wind", "Sea of Corruption", "Ancient Crypt"]

login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/')
def home():
    db_sessions = quests_dao.get_quest_sessions()
    day_names = dict(DAYS)

    return render_template('home.html', sessions=db_sessions, day_names=day_names, quest_types=QUEST_TYPES, difficulties=DIFFICULTIES, roles=PARTY_ROLES)
    
@login_manager.user_loader
def load_user(user_id):
    db_user = users_dao.get_user_by_id(p_id=user_id)

    if db_user is None:
        return None

    return User(db_user["id"], db_user["username"], db_user["password"], db_user["role"])

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
    day_names = dict(DAYS)

    user_participations = {}

    if current_user.is_authenticated:
        for participation in quests_dao.get_participations_by_user(current_user.id):
            user_participations[participation["session_id"]] = participation

    return render_template(
        'quest_page.html',
        quest=db_quest,
        sessions=db_sessions,
        day_names=day_names,
        roles=PARTY_ROLES,
        user_participations=user_participations,
        simulated_day=SIMULATED_DAY_OF_WEEK,
        simulated_time=SIMULATED_CURRENT_TIME,
    )

@app.route('/adventurer_profile')
@login_required
def adventurer_profile():
    day_names = dict(DAYS)
    db_participations = quests_dao.get_participations_by_user(current_user.id)

    return render_template('adventurer_profile.html', participations=db_participations,day_names=day_names)

@app.route('/guild_master_profile')
@login_required
def guild_master_profile():
    db_quests = quests_dao.get_quests_by_guild_master(current_user.id)

    return render_template('guild_master_profile.html', quests=db_quests, days=DAYS, day_names=dict(DAYS), locations=LOCATIONS)


@app.route('/sessions/<int:session_id>/update', methods=["POST"])
@login_required
def update_quest_session(session_id):
    db_session = quests_dao.get_session_by_id(session_id)

    if db_session is None:
        return redirect(url_for("error"))

    if len(quests_dao.get_participations_by_session(session_id)) > 0:
        flash("This quest session cant be modified because adventurers have already joined.")
        return redirect(url_for("guild_master_profile"))

    session_day = request.form.get("txt_session_day")
    session_start_time = request.form.get("txt_session_start_time")
    session_location = request.form.get("txt_session_location")

    if quest_session_overlaps(session_day, session_start_time, session_location, db_session["duration_minutes"], session_id):
        flash("A location can only host one quest session at a time.")
        return redirect(url_for("guild_master_profile"))

    updated = quests_dao.update_quest_session(session_id, session_day, session_start_time,session_location)

    if not updated:
        flash("A location can only host one quest session at a time.")
        return redirect(url_for("guild_master_profile"))

    flash("Quest session updated successfully.")
    return redirect(url_for("guild_master_profile"))


@app.route('/sessions/<int:session_id>/cancel', methods=["POST"])
@login_required
def cancel_quest_session(session_id):
    quests_dao.delete_quest_session(p_session_id=session_id)

    flash("Quest session cancelled successfully.")
    return redirect(url_for("guild_master_profile"))

@app.route('/add_quest', methods=["GET", "POST"])
@login_required
def add_quest():
    if request.method == "GET":
        return render_template(
            "add_quest.html",
            quest_types=QUEST_TYPES,
            difficulties=DIFFICULTIES,
            days=DAYS,
            locations=LOCATIONS,
        )

    title = request.form.get("txt_title")
    description = request.form.get("txt_description")
    duration = request.form.get("txt_duration")
    quest_type = request.form.get("txt_quest_type")
    difficulty = request.form.get("txt_difficulty")
    session_days = request.form.getlist("txt_session_day")
    session_start_times = request.form.getlist("txt_session_start_time")
    session_locations = request.form.getlist("txt_session_location")
    image = request.files["file_image"]
    requested_sessions = []

    for i in range(len(session_days)):
        requested_sessions.append((
            session_days[i],
            session_start_times[i],
            session_locations[i],
        ))

    requested_session_objects = []

    for session_day, session_start_time, session_location in requested_sessions:
        requested_session = {"day_of_week": session_day, "start_time": session_start_time,"duration_minutes": duration, "location": session_location }

        for saved_session in requested_session_objects:
            if session_location == saved_session["location"] and sessions_overlap(requested_session, saved_session):
                flash("A location can only host one quest session at a time.")
                return render_template("add_quest.html", quest_types=QUEST_TYPES,difficulties=DIFFICULTIES, days=DAYS, locations=LOCATIONS)

        requested_session_objects.append(requested_session)

        if quest_session_overlaps(p_day_of_week=session_day, p_start_time=session_start_time, p_location=session_location,p_duration=duration):
            flash("A location can only host one quest session at a time.")
            return render_template("add_quest.html", quest_types=QUEST_TYPES, difficulties=DIFFICULTIES, days=DAYS, locations=LOCATIONS)
    image_filename = "logo.png"

    if image and image.filename:
        img = Image.open(image)
        width, height = img.size
        new_width = QUEST_IMG_HEIGHT * width / height
        size = new_width, QUEST_IMG_HEIGHT
        img.thumbnail(size, Image.Resampling.LANCZOS)

        left = new_width / 2 - QUEST_IMG_HEIGHT / 2
        top = 0
        right = new_width / 2 + QUEST_IMG_HEIGHT / 2
        bottom = QUEST_IMG_HEIGHT

        img = img.crop((left, top, right, bottom))

        seconds = int(datetime.now().timestamp())
        ext = image.filename.split(".")[-1]
        image_filename = current_user.username.lower() + "-" + str(seconds) + "." + ext

        img.save(BASE_DIR / "static" / "images" / image_filename)

    quest_id = quests_dao.new_quest(
        p_title=title,
        p_duration=duration,
        p_difficulty=difficulty,
        p_description=description,
        p_quest_type=quest_type,
        p_image_filename=image_filename,
        p_created_by=current_user.id,
    )

    for session_day, session_start_time, session_location in requested_sessions:
        quests_dao.new_quest_session( p_quest_id=quest_id, p_day_of_week=session_day,p_start_time=session_start_time, p_location=session_location )

    flash("Quest added successfully.")
    return redirect(url_for("quest_detail", quest_id=quest_id))


@app.route('/sessions/<int:session_id>/join', methods=["POST"])
@login_required
def join_quest_session(session_id):
    if current_user.role != "adventurer":
        return redirect(url_for("error"))

    db_session = quests_dao.get_session_by_id(p_session_id=session_id)

    if db_session is None:
        return redirect(url_for("error"))
    
    selected_role = request.form.get("selected_role")
    reserved_places = request.form.get("reserved_places")

    if quests_dao.get_participation(current_user.id, session_id) is not None:
        flash("You already joined this quest session.")
        return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))

    user_participations = quests_dao.get_participations_by_user(current_user.id)

    if len(user_participations) >= 3:
        flash("You can join at most 3 quest sessions during the week.")
        return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))

    if user_session_overlaps(current_user.id, session_id):
        flash("You cannot join two quest sessions that overlap in time.")
        return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))

    if not role_has_capacity(session_id, selected_role, reserved_places):
        flash("There are not enough places left for that role.")
        return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))

    quests_dao.new_participation(p_session_id=session_id, p_user_id=current_user.id,p_selected_role=selected_role, p_reserved_places=reserved_places)

    flash("Quest session joined successfully.")
    return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))


def update_quest_participation(participation_id):
    db_participation = quests_dao.get_participation_by_id(p_participation_id=participation_id)

    if db_participation is None or int(db_participation["user_id"]) != int(current_user.id):
        return redirect(url_for("error"))

    db_session = quests_dao.get_session_by_id(p_session_id=db_participation["session_id"])

    if not participation_can_be_changed(db_session):
        flash("This participation can no longer be modified or cancelled.")
        return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))

    selected_role = request.form.get("selected_role")
    reserved_places = request.form.get("reserved_places")

    if selected_role not in PARTY_ROLES or reserved_places not in ["1", "2"]:
        flash("Choose a valid role and number of places.")
        return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))

    if not role_has_capacity(db_participation["session_id"], selected_role, reserved_places, participation_id):
        flash("There are not enough places left for that role.")
        return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))

    quests_dao.update_participation(
        p_participation_id=participation_id,
        p_selected_role=selected_role,
        p_reserved_places=reserved_places,
    )

    flash("Participation updated successfully.")
    return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))


@app.route('/participations/<int:participation_id>', methods=["POST"])
@login_required
def cancel_quest_participation(participation_id):
    if request.form.get("participation_action") == "update":
        return update_quest_participation(participation_id)

    db_participation = quests_dao.get_participation_by_id(p_participation_id=participation_id)

    if db_participation is None or int(db_participation["user_id"]) != int(current_user.id):
        return redirect(url_for("error"))

    db_session = quests_dao.get_session_by_id(p_session_id=db_participation["session_id"])

    if not participation_can_be_changed(db_session):
        flash("This participation can no longer be modified or cancelled.")
        return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))

    quests_dao.delete_participation(p_participation_id=participation_id)

    flash("Participation cancelled successfully.")
    return redirect(url_for("quest_detail", quest_id=db_session["quest_id"]))

@app.route('/admin')
@login_required
def admin():
    if current_user.role != "admin":
        return redirect(url_for("error"))

    day_names = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
        7: "Sunday",
    }

    return render_template(
        'admin.html',
        adventurers=users_dao.get_adventurers_with_participation_counts(),
        quests=quests_dao.get_quests(),
        sessions=quests_dao.get_quest_sessions(),
        stats=quests_dao.get_platform_statistics(),
        day_names=day_names,
        roles=PARTY_ROLES,
    )

@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')

    form_user = request.form.to_dict()

    db_user = users_dao.get_user_by_username(form_user["txt_username"])

    if not db_user:
        flash("The user does not exist", "danger")
        return redirect(url_for("login"))
    
    if not check_password_hash(db_user[2], form_user["txt_password"]):
        flash("The password is wrong", "danger")
        return redirect(url_for("login"))

    new = User(
        id=db_user["id"],
        username=db_user["username"],
        password=db_user["password"],
        role=db_user["role"]
    )

    login_user(new)
    flash("Welcome back! " + db_user["username"] + "!", "success")

    return redirect(url_for("home"))

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

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

def participation_can_be_changed(p_session):
    current_minutes = session_start_min_week(
        SIMULATED_DAY_OF_WEEK,
        SIMULATED_CURRENT_TIME,
    )
    session_minutes = session_start_min_week(
        p_session["day_of_week"],
        p_session["start_time"],
    )

    if session_minutes < current_minutes:
        session_minutes += 7 * 24 * 60

    return session_minutes - current_minutes > 8 * 60


def time_to_minutes(p_start_time):
    hours, minutes = p_start_time.split(":")

    return int(hours) * 60 + int(minutes)


def session_start_min_week(p_day_of_week, p_start_time):
    return (int(p_day_of_week) - 1) * 24 * 60 + time_to_minutes(p_start_time)


def sessions_overlap(p_first_session, p_second_session):
    first_start = session_start_min_week(p_first_session["day_of_week"], p_first_session["start_time"])
    first_end = first_start + int(p_first_session["duration_minutes"])
    second_start = session_start_min_week(p_second_session["day_of_week"], p_second_session["start_time"])
    second_end = second_start + int(p_second_session["duration_minutes"])

    return first_start < second_end and second_start < first_end


def quest_session_overlaps(p_day_of_week, p_start_time, p_location, p_duration, p_same_session_id=None):
    new_start = time_to_minutes(p_start_time)
    new_end = new_start + int(p_duration)

    for db_session in quests_dao.get_quest_sessions():
        if p_same_session_id is not None and int(db_session["session_id"]) == int(p_same_session_id):
            continue

        if int(db_session["day_of_week"]) != int(p_day_of_week):
            continue

        if db_session["location"] != p_location:
            continue

        existing_start = time_to_minutes(db_session["start_time"])
        existing_end = existing_start + int(db_session["duration_minutes"])

        if new_start < existing_end and existing_start < new_end:
            return True

    return False


def user_session_overlaps(p_user_id, p_session_id):
    new_session = quests_dao.get_session_by_id(p_session_id)

    for participation in quests_dao.get_participations_by_user(p_user_id):
        if int(participation["session_id"]) == int(p_session_id):
            continue

        if sessions_overlap(new_session, participation):
            return True

    return False


def role_has_capacity(p_session_id, p_selected_role, p_reserved_places, p_existing_participation_id=None):
    capacity = PARTY_ROLES[p_selected_role]
    reserved_places = 0

    for participation in quests_dao.get_participations_by_session(p_session_id):
        if participation["selected_role"] == p_selected_role:
            reserved_places += int(participation["reserved_places"])

    if p_existing_participation_id is not None:
        existing = quests_dao.get_participation_by_id(p_existing_participation_id)

        if existing is not None and existing["selected_role"] == p_selected_role:
            reserved_places -= int(existing["reserved_places"])

    return reserved_places + int(p_reserved_places) <= capacity
