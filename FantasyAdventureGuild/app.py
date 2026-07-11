from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/quests')
def quest_page():
    return render_template('quest_page.html')

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

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')
