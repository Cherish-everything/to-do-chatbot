import os
from cs50 import SQL
from flask import Flask, render_template, request, session, redirect, make_response, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import random

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "clastr_agency_todo_secret_key_99_flex"

# 2. Connect to the pristine environment path (with the Vercel pre-create file trick)
if os.path.exists("/tmp"):
    db_path = "/tmp/todo.db"
    # Create an empty file first so the CS50 library doesn't panic and crash
    if not os.path.exists(db_path):
        open(db_path, "w").close()
    db = SQL("sqlite:////tmp/todo.db")
else:
    db = SQL("sqlite:///todo.db")

# 3. Create tables using independent, single-query executions
try:
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS list (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            user_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)
except Exception as e:
    print(f"Database initialization tracking log notice: {e}")
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/main")
@login_required
def index():
    user_id = session.get('user_id')
    
    # Fetch live tasks for this specific logged-in user
    todo_rows = db.execute("SELECT id, task FROM list WHERE user_id = ?", user_id)
    completed = session.get("completed_count", 0)

    # Force a fresh response package to bypass any annoying engine layout caching
    rendered = render_template("index.html", 
                               todo=todo_rows,
                               completed_today=completed)
    
    response = make_response(rendered)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route("/get-system-message")
@login_required
def get_system_message():
    user_id = session.get('user_id')
    
    # Fetch live tasks just like your index route does
    todo_rows = db.execute("SELECT id, task FROM list WHERE user_id = ?", user_id)
    total_tasks = len(todo_rows)
    task_due = total_tasks
    
    # Generate the message using your exact arrays!
    if total_tasks > 0:
        starter = ["Yo", "Dude", "Bro", "Hey", "Hello,", "Have a moment?", "Helloooooo", "Hey dude"]
        middle = [f"You got {task_due} due left!", f"Clock's ticking! {task_due} tasks are waiting!", f"You need to lock in bruh"]
        motivational_msg = f"{random.choice(starter)}, {random.choice(middle)}"
    else:
        motivational_msg = "All systems clear. No active sequences pending."

    return jsonify({"message": motivational_msg})

@app.route("/add-task", methods=["POST"])
@login_required
def add_task():
    user_id = session.get('user_id')
    new_task = request.form.get("task_name", "").strip()
    
    # Prevent task additions completely if the system state is locked
    if new_task and not session.get("locked", False):
        db.execute("INSERT INTO list (user_id, task) VALUES (?, ?)", user_id, new_task)
        
    return redirect("/main")

@app.route("/complete-task/<int:task_id>", methods=["POST"])
@login_required
def complete_task(task_id):
    user_id = session.get('user_id')
    
    db.execute("DELETE FROM list WHERE id = ? AND user_id = ?", task_id, user_id)
    session["completed_count"] = session.get("completed_count", 0) + 1
    
    # --- CHANGE THIS LINE FROM REDIRECT TO JSON ---
    return redirect("/main")

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_input = request.form.get("username")
        password_input = request.form.get("password")
        if not username_input or not password_input:
            return "Error: Missing data", 400
        rows = db.execute("SELECT * FROM users WHERE username = ?", username_input)
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], password_input):
            return "Access Denied", 403
        
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        session["completed_count"] = 0
        session["locked"] = False
        return redirect("/main")
    else:
        session.clear()
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("new_username")
        password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")
        
        # 1. Validation check for blank entries or password mismatches
        if not username or not password or confirmation != password:
            return "Invalid registration details. Ensure passwords match.", 400
            
        # 2. Strict check to ensure username doesn't already exist in the database
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) > 0:
            return "Username taken. Please choose a different identity.", 400
        
        # 3. Clean insert execution block
        try:
            db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                       username, generate_password_hash(password))
            return redirect("/login")
        except Exception as e:
            print(f"Registration insert exception: {e}")
            return "An internal database entry error occurred.", 500
            
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=False)
