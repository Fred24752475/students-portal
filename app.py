import json
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

# Lumen Student Portal
# Pages: landing, portal form, students index, student details.

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "students.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
OPTIONS_FILE = BASE_DIR / "static" / "data" / "options.json"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
STATUS_OPTIONS = ("Pending", "Admitted", "Declined")
FORM_FIELDS = (
    "first_name",
    "last_name",
    "email",
    "phone",
    "address",
    "date_of_birth",
    "gender",
    "faculty",
    "department",
    "entry_score",
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


def get_connection():
    """Open the SQLite database and return rows as dictionaries."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the students table the first time the app runs."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                gender TEXT NOT NULL,
                faculty TEXT NOT NULL,
                department TEXT NOT NULL,
                entry_score INTEGER NOT NULL,
                image_name TEXT NOT NULL,
                admission_status TEXT NOT NULL DEFAULT 'Pending'
            )
            """
        )


def load_options():
    """Read the faculty and department list used to check form choices."""
    with OPTIONS_FILE.open(encoding="utf-8") as options_file:
        return json.load(options_file)


def blank_form():
    return {field: "" for field in FORM_FIELDS}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_submission(form, image):
    """Return an error message when any required value is missing or invalid."""
    for field in FORM_FIELDS:
        if not str(form.get(field, "")).strip():
            return "Fill in every field before submitting."

    if "@" not in form["email"] or "." not in form["email"].split("@")[-1]:
        return "Enter a valid email address."

    try:
        score = int(form["entry_score"])
    except ValueError:
        return "Entry score must be a number."

    if score < 0 or score > 100:
        return "Entry score must be between 0 and 100."

    options = load_options()
    faculty = next(
        (item for item in options["faculties"] if item["name"] == form["faculty"]),
        None,
    )
    if faculty is None or form["department"] not in faculty["departments"]:
        return "Choose a faculty and one of its departments."

    if form["gender"] not in ("Female", "Male"):
        return "Choose a gender."

    if image is None or not image.filename:
        return "Upload a student photo."

    if not allowed_file(image.filename):
        return "The photo must be a PNG, JPG, WEBP, or GIF image."

    return ""


def save_image(image):
    """Store the photo in the project folder and return only its file name."""
    extension = secure_filename(image.filename).rsplit(".", 1)[1].lower()
    image_name = uuid4().hex + "." + extension
    image.save(UPLOAD_DIR / image_name)
    return image_name


def create_student(form, image_name):
    """Save the student's details. The photo itself stays in the uploads folder."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO students (
                first_name, last_name, email, phone, address, date_of_birth,
                gender, faculty, department, entry_score, image_name, admission_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
            """,
            (
                form["first_name"],
                form["last_name"],
                form["email"],
                form["phone"],
                form["address"],
                form["date_of_birth"],
                form["gender"],
                form["faculty"],
                form["department"],
                int(form["entry_score"]),
                image_name,
            ),
        )
        return cursor.lastrowid


def get_students():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM students ORDER BY id ASC"
        ).fetchall()
    return rows


def get_student(student_id):
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()


def update_admission_status(student_id, status):
    with get_connection() as connection:
        connection.execute(
            "UPDATE students SET admission_status = ? WHERE id = ?",
            (status, student_id),
        )


@app.context_processor
def inject_year():
    return {"year": datetime.now().year}


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/form", methods=["GET", "POST"])
def portal_form():
    """Validate the portal form, save the record, then open the students list."""
    if request.method == "GET":
        return render_template("form.html", form=blank_form(), error="")

    form = {field: request.form.get(field, "").strip() for field in FORM_FIELDS}
    image = request.files.get("image")
    error = validate_submission(form, image)

    if error:
        return render_template("form.html", form=form, error=error)

    image_name = save_image(image)
    create_student(form, image_name)
    return redirect(url_for("students_index"))


@app.route("/students")
def students_index():
    return render_template("students.html", students=get_students())


@app.route("/students/<int:student_id>")
def student_details(student_id):
    student = get_student(student_id)
    if student is None:
        return redirect(url_for("students_index"))
    return render_template(
        "details.html",
        student=student,
        status_options=STATUS_OPTIONS,
    )


@app.route("/students/<int:student_id>/status", methods=["POST"])
def student_status(student_id):
    """Change admission status from the details page without a full reload."""
    student = get_student(student_id)
    if student is None:
        return jsonify(ok=False, message="Student not found."), 404

    payload = request.get_json(silent=True) or {}
    status = payload.get("admission_status", "")

    if status not in STATUS_OPTIONS:
        return jsonify(ok=False, message="Choose a valid admission status."), 400

    update_admission_status(student_id, status)
    return jsonify(ok=True, admission_status=status)


init_db()


if __name__ == "__main__":
    app.run(debug=True)
