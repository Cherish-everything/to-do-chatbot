import os
from cs50 import SQL
from flask import Flask, render_template, request, session, redirect, make_response, jsonify
import random

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "clastr_agency_todo_secret_key_99_flex"

# Connect to database
if os.path.exists("/tmp"):
    db_path = "/tmp/todo.db"
    if not os.path.exists(db_path):
        open(db_path, "w").close()
    db = SQL("sqlite:////tmp/todo.db")
else:
    db = SQL("sqlite:///todo.db")

# Create a single table for everyone
try:
    db.execute("""
        CREATE TABLE IF NOT EXISTS list (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            task TEXT NOT NULL
        );
    """)
except Exception as e:
    print(f"Database error: {e}")

@app.route("/")
@app.route("/main")
def index():
    todo_rows = db.execute("SELECT id, task FROM list")
    completed = session.get("completed_count", 0)

    rendered = render_template("index.html", todo=todo_rows, completed_today=completed)
    response = make_response(rendered)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route("/get-system-message")
def get_system_message():
    todo_rows = db.execute("SELECT id, task FROM list")
    total_tasks = len(todo_rows)
    
    if total_tasks > 0:
        starter = ["Yo", "Dude", "Bro", "Hey", "Hello,", "Helloooooo", "Hey dude"]
        middle = [f"You got {total_tasks} due left!", "Clock's ticking!", "You need to lock in bruh"]
        motivational_msg = f"{random.choice(starter)}, {random.choice(middle)}"
    else:
        motivational_msg = "All systems clear. No active sequences pending."

    return jsonify({"message": motivational_msg})

@app.route("/add-task", methods=["POST"])
def add_task():
    new_task = request.form.get("task_name", "").strip()
    if new_task:
        db.execute("INSERT INTO list (task) VALUES (?)", new_task)
    return redirect("/main")

@app.route("/complete-task/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    db.execute("DELETE FROM list WHERE id = ?", task_id)
    session["completed_count"] = session.get("completed_count", 0) + 1
    return redirect("/main")

if __name__ == "__main__":
    app.run(debug=False)
