import re
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.models import Address, User

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("products.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()

        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not EMAIL_RE.match(email):
            errors.append("Valid email is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("auth/register.html")

        user = User(email=email, full_name=full_name, phone=phone or None)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome! Your account has been created.", "success")
        return redirect(url_for("products.home"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("products.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(email=email).first()
        if user and user.is_active and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            flash("Logged in successfully.", "success")
            if next_page:
                return redirect(next_page)
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("products.home"))

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("products.home"))


@auth_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        if not full_name:
            flash("Full name is required.", "error")
        else:
            current_user.full_name = full_name
            current_user.phone = phone or None
            db.session.commit()
            flash("Profile updated.", "success")
        return redirect(url_for("auth.account"))

    return render_template("auth/account.html")


@auth_bp.route("/addresses")
@login_required
def addresses():
    user_addresses = (
        Address.query.filter_by(user_id=current_user.id)
        .order_by(Address.is_default.desc(), Address.id.desc())
        .all()
    )
    return render_template("auth/addresses.html", addresses=user_addresses)


@auth_bp.route("/addresses/add", methods=["POST"])
@login_required
def add_address():
    label = request.form.get("label", "Home").strip()
    line1 = request.form.get("line1", "").strip()
    line2 = request.form.get("line2", "").strip()
    city = request.form.get("city", "").strip()
    state = request.form.get("state", "").strip()
    pincode = request.form.get("pincode", "").strip()
    is_default = request.form.get("is_default") == "on"

    if not all([line1, city, state, pincode]):
        flash("Please fill in all required address fields.", "error")
        return redirect(url_for("auth.addresses"))

    if is_default:
        Address.query.filter_by(user_id=current_user.id, is_default=True).update(
            {"is_default": False}
        )

    address = Address(
        user_id=current_user.id,
        label=label or "Home",
        line1=line1,
        line2=line2 or None,
        city=city,
        state=state,
        pincode=pincode,
        is_default=is_default or not current_user.addresses,
    )
    db.session.add(address)
    db.session.commit()
    flash("Address added.", "success")
    return redirect(url_for("auth.addresses"))


@auth_bp.route("/addresses/<int:address_id>/edit", methods=["POST"])
@login_required
def edit_address(address_id):
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    address.label = request.form.get("label", address.label).strip()
    address.line1 = request.form.get("line1", address.line1).strip()
    address.line2 = request.form.get("line2", "").strip() or None
    address.city = request.form.get("city", address.city).strip()
    address.state = request.form.get("state", address.state).strip()
    address.pincode = request.form.get("pincode", address.pincode).strip()

    if request.form.get("is_default") == "on":
        Address.query.filter_by(user_id=current_user.id, is_default=True).update(
            {"is_default": False}
        )
        address.is_default = True

    db.session.commit()
    flash("Address updated.", "success")
    return redirect(url_for("auth.addresses"))


@auth_bp.route("/addresses/<int:address_id>/delete", methods=["POST"])
@login_required
def delete_address(address_id):
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    was_default = address.is_default
    db.session.delete(address)
    db.session.commit()

    if was_default:
        next_addr = Address.query.filter_by(user_id=current_user.id).first()
        if next_addr:
            next_addr.is_default = True
            db.session.commit()

    flash("Address deleted.", "info")
    return redirect(url_for("auth.addresses"))


@auth_bp.route("/addresses/<int:address_id>/default", methods=["POST"])
@login_required
def set_default_address(address_id):
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    Address.query.filter_by(user_id=current_user.id, is_default=True).update(
        {"is_default": False}
    )
    address.is_default = True
    db.session.commit()
    flash("Default address updated.", "success")
    return redirect(url_for("auth.addresses"))
