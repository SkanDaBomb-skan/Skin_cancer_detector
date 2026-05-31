

import json
import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
    session,
)
from functools import wraps

from config import Config
from database.db import init_db, get_connection
from engine.predictor import predict, save_upload
from engine.report import generate_report


app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

init_db()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function



def _allowed(filename: str) -> bool:
    """Check whether *filename* has a permitted extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )




@app.route("/")
def home():
    """Landing page — explains what the platform does."""
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == app.config.get("ADMIN_USERNAME") and password == app.config.get("ADMIN_PASSWORD"):
            session["logged_in"] = True
            flash("Logged in successfully.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard"))
        else:
            flash("Invalid credentials.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard page — aggregates patient data and highlights risk metrics."""
    try:
        with get_connection() as conn:
            # Aggregate stats
            total = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
            malignant = conn.execute("SELECT COUNT(*) FROM predictions WHERE risk_level = 'Malignant'").fetchone()[0]
            benign = conn.execute("SELECT COUNT(*) FROM predictions WHERE risk_level = 'Benign'").fetchone()[0]
            
            # Recent predictions for the recap table
            rows = conn.execute("SELECT * FROM predictions ORDER BY created_at DESC LIMIT 10").fetchall()
            recent_predictions = [dict(r) for r in rows]
            
    except Exception as exc:
        flash(f"Error loading dashboard: {exc}", "error")
        total = malignant = benign = 0
        recent_predictions = []

    return render_template(
        "dashboard.html",
        total=total,
        malignant=malignant,
        benign=benign,
        recent_predictions=recent_predictions
    )


@app.route("/analyze", methods=["GET", "POST"])
@login_required
def analyze():
    """
    GET  → render upload form with image preview
    POST → run prediction and redirect to result page
    """
    if request.method == "POST":
        file = request.files.get("image")

        if not file or file.filename == "":
            flash("Please select an image to analyze.", "warning")
            return redirect(url_for("analyze"))

        if not _allowed(file.filename):
            flash(
                "Unsupported file type. Please upload a PNG, JPG, JPEG, or WebP image.",
                "warning",
            )
            return redirect(url_for("analyze"))

        try:
            # Save uploaded image
            original_name = file.filename
            saved_path = save_upload(file, Config.UPLOAD_FOLDER)

            # Run ML prediction
            result = predict(saved_path)

            # Persist to database
            with get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO predictions
                        (image_path, original_name, diagnosis, short_code,
                         risk_level, confidence, description, recommendation,
                         top_3_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        saved_path,
                        original_name,
                        result["diagnosis"],
                        result["short_code"],
                        result["risk_level"],
                        result["confidence"],
                        result["description"],
                        result["recommendation"],
                        result["top_3_json"],
                    ),
                )
                prediction_id = cursor.lastrowid

            return redirect(url_for("result", prediction_id=prediction_id))

        except Exception as exc:
            flash(f"Analysis failed: {exc}", "error")
            return redirect(url_for("analyze"))

    return render_template("analyze.html")


@app.route("/result/<int:prediction_id>")
@login_required
def result(prediction_id):
    """Display detailed prediction results."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM predictions WHERE id = ?", (prediction_id,)
            ).fetchone()

        if not row:
            flash("Prediction not found.", "error")
            return redirect(url_for("history"))

        pred = dict(row)
        # Parse the JSON for top-3 predictions
        pred["top_3"] = json.loads(pred.get("top_3_json", "[]"))

        # Build a web-servable URL for the image
        img_path = pred.get("image_path", "")
        if img_path:
            # Convert absolute path to relative URL
            static_idx = img_path.replace("\\", "/").find("static/")
            if static_idx != -1:
                pred["image_url"] = "/" + img_path.replace("\\", "/")[static_idx:]
            else:
                pred["image_url"] = ""
        else:
            pred["image_url"] = ""

        # Get risk color config
        risk_colors = Config.RISK_COLORS.get(
            pred["risk_level"],
            {"bg": "#f3f4f6", "text": "#374151", "accent": "#6b7280"},
        )

        return render_template(
            "result.html", prediction=pred, risk_colors=risk_colors
        )

    except Exception as exc:
        flash(f"Error loading result: {exc}", "error")
        return redirect(url_for("history"))


@app.route("/history")
@login_required
def history():
    """Show all past predictions, most recent first."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM predictions ORDER BY created_at DESC"
            ).fetchall()
        predictions = [dict(r) for r in rows]
    except Exception as exc:
        flash(f"Error loading history: {exc}", "error")
        predictions = []

    return render_template("history.html", predictions=predictions)


@app.route("/history/<int:prediction_id>/pdf")
@login_required
def download_pdf(prediction_id):
    """Generate and stream a PDF report for a prediction."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM predictions WHERE id = ?", (prediction_id,)
            ).fetchone()

        if not row:
            flash("Prediction not found.", "error")
            return redirect(url_for("history"))

        pred = dict(row)
        buffer = generate_report(pred)
        safe = pred["diagnosis"].replace(" ", "_")
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"DermaVision_Report_{safe}_{prediction_id}.pdf",
            mimetype="application/pdf",
        )

    except Exception as exc:
        flash(f"PDF generation failed: {exc}", "error")
        return redirect(url_for("history"))




@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Accept an image via multipart POST and return JSON results.
    Used by the frontend for the async loading animation.
    """
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    file = request.files.get("image")
    if not file or file.filename == "":
        return jsonify({"error": "No image provided"}), 400

    if not _allowed(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    try:
        original_name = file.filename
        saved_path = save_upload(file, Config.UPLOAD_FOLDER)
        result = predict(saved_path)

        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO predictions
                    (image_path, original_name, diagnosis, short_code,
                     risk_level, confidence, description, recommendation,
                     top_3_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    saved_path,
                    original_name,
                    result["diagnosis"],
                    result["short_code"],
                    result["risk_level"],
                    result["confidence"],
                    result["description"],
                    result["recommendation"],
                    result["top_3_json"],
                ),
            )
            prediction_id = cursor.lastrowid

        result["id"] = prediction_id
        result["redirect"] = url_for("result", prediction_id=prediction_id)
        return jsonify(result)

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500




@app.errorhandler(404)
def page_not_found(_):
    return render_template("404.html"), 404


@app.errorhandler(413)
def file_too_large(_):
    flash("File is too large. Maximum size is 16 MB.", "error")
    return redirect(url_for("analyze"))


@app.errorhandler(500)
def internal_error(_):
    return render_template("500.html"), 500



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
