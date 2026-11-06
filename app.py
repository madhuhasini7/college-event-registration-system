
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "college_event_secret_key"


# Database Connection
def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


# Create Database Tables
def create_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_venue TEXT NOT NULL,
            event_description TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            student_email TEXT NOT NULL,
            event_id INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)

    connection.commit()
    connection.close()


# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# Admin Login
@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        else:
            return render_template(
                "admin_login.html",
                error="Invalid username or password"
            )

    return render_template("admin_login.html")


# Admin Dashboard
@app.route("/admin-dashboard")
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    total_events = connection.execute(
        "SELECT COUNT(*) FROM events"
    ).fetchone()[0]

    total_registrations = connection.execute(
        "SELECT COUNT(*) FROM registrations"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "admin_dashboard.html",
        total_events=total_events,
        total_registrations=total_registrations
    )


# Admin Logout
@app.route("/admin-logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("admin_login"))


# View Events (Available to Students and Admin)
@app.route("/events")
def events():

    connection = get_db_connection()

    all_events = connection.execute(
        "SELECT * FROM events ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template(
        "events.html",
        events=all_events,
        is_admin=session.get("admin_logged_in", False)
    )


# Add Event (Admin Only)
@app.route("/add-event", methods=["GET", "POST"])
def add_event():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        event_name = request.form["event_name"]
        event_date = request.form["event_date"]
        event_venue = request.form["event_venue"]
        event_description = request.form["event_description"]

        connection = get_db_connection()

        connection.execute(
            """INSERT INTO events
            (event_name, event_date, event_venue, event_description)
            VALUES (?, ?, ?, ?)""",
            (event_name, event_date, event_venue, event_description)
        )

        connection.commit()
        connection.close()

        return redirect(url_for("events"))

    return render_template("add_event.html")


# Edit Event (Admin Only)
@app.route("/edit-event/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    event = connection.execute(
        "SELECT * FROM events WHERE id = ?", (event_id,)
    ).fetchone()

    if event is None:
        connection.close()
        return "Event not found", 404

    if request.method == "POST":
        event_name = request.form["event_name"]
        event_date = request.form["event_date"]
        event_venue = request.form["event_venue"]
        event_description = request.form["event_description"]

        connection.execute(
            """UPDATE events
            SET event_name = ?, event_date = ?,
                event_venue = ?, event_description = ?
            WHERE id = ?""",
            (event_name, event_date, event_venue,
             event_description, event_id)
        )

        connection.commit()
        connection.close()

        return redirect(url_for("events"))

    connection.close()

    return render_template("edit_event.html", event=event)


# Delete Event (Admin Only)
@app.route("/delete-event/<int:event_id>", methods=["POST"])
def delete_event(event_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM events WHERE id = ?",
        (event_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("events"))


# Student Registration (Available to Everyone)
@app.route("/registrations", methods=["GET", "POST"])
def registrations():

    connection = get_db_connection()

    if request.method == "POST":
        student_name = request.form["student_name"].strip()
        student_email = request.form["student_email"].strip()
        event_id = request.form["event_id"]

        event = connection.execute(
            "SELECT id FROM events WHERE id = ?", (event_id,)
        ).fetchone()

        if student_name and student_email and event:
            connection.execute(
                """INSERT INTO registrations
                (student_name, student_email, event_id)
                VALUES (?, ?, ?)""",
                (student_name, student_email, event_id)
            )

            connection.commit()

        connection.close()

        return redirect(url_for("registrations"))

    all_events = connection.execute(
        "SELECT * FROM events ORDER BY event_date"
    ).fetchall()

    is_admin = session.get("admin_logged_in", False)

    if is_admin:
        all_registrations = connection.execute("""
            SELECT registrations.id,
                   registrations.student_name,
                   registrations.student_email,
                   events.event_name,
                   events.event_date
            FROM registrations
            JOIN events ON registrations.event_id = events.id
            ORDER BY registrations.id DESC
        """).fetchall()
    else:
        all_registrations = []

    connection.close()

    return render_template(
        "registrations.html",
        events=all_events,
        registrations=all_registrations,
        is_admin=is_admin
    )


# Delete Registration (Admin Only)
@app.route("/delete-registration/<int:registration_id>", methods=["POST"])
def delete_registration(registration_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM registrations WHERE id = ?",
        (registration_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("registrations"))


if __name__ == "__main__":
    create_table()
    app.run(debug=True)
