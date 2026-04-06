import time
from collections import defaultdict

from flask import flash, redirect, render_template, request, url_for, session
from flask_login import current_user, login_required, login_user, logout_user

from blueprints.auth import auth_bp
from models.user import User

# ── Rate limiting (in-memory, per-IP) ───────────────────────────
_login_attempts = defaultdict(list)   # ip -> [timestamps]
RATE_LIMIT_WINDOW = 30   # seconds
RATE_LIMIT_MAX = 5        # attempts


def _is_rate_limited(ip):
    """Return True if *ip* has exceeded the login attempt limit."""
    now = time.time()
    attempts = _login_attempts[ip]
    # Prune old entries outside the window
    _login_attempts[ip] = [t for t in attempts if now - t < RATE_LIMIT_WINDOW]
    return len(_login_attempts[ip]) >= RATE_LIMIT_MAX


def _record_attempt(ip):
    _login_attempts[ip].append(time.time())


# ── Routes ──────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        ip = request.remote_addr or "unknown"

        if _is_rate_limited(ip):
            flash("Too many login attempts. Please wait and try again.", "danger")
            return render_template("auth/login.html"), 429

        _record_attempt(ip)

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(username=username).first()

        if user and user.is_active and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.display_name}!", "success")

            # Honour ?next= redirect, but only relative URLs
            next_url = request.args.get("next", "")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("dashboard.index"))

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        if not current_user.check_password(current_pw):
            flash("Current password is incorrect.", "danger")
        elif len(new_pw) < 8:
            flash("New password must be at least 8 characters.", "danger")
        elif new_pw != confirm_pw:
            flash("New passwords do not match.", "danger")
        else:
            from extensions import db
            current_user.set_password(new_pw)
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for("dashboard.index"))

    return render_template("auth/change_password.html")
