import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models import Category, Order, OrderItem, Product, ProductImage
from app.routes.auth import admin_required
from app.services.inventory import get_low_stock_products

admin_bp = Blueprint("admin", __name__)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def save_product_image(file):
    if not file or not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(path)
    return f"uploads/products/{filename}"


def slugify(text):
    import re

    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:220]


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    total_orders = Order.query.count()
    recent_orders = Order.query.filter(Order.placed_at >= thirty_days_ago).count()
    revenue = (
        db.session.query(db.func.coalesce(db.func.sum(Order.total), 0))
        .filter(Order.status != "cancelled")
        .scalar()
    )
    low_stock = get_low_stock_products(threshold=5)
    latest_orders = Order.query.order_by(Order.placed_at.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        total_orders=total_orders,
        recent_orders=recent_orders,
        revenue=revenue,
        low_stock=low_stock,
        latest_orders=latest_orders,
    )


@admin_bp.route("/products")
@login_required
@admin_required
def products():
    q = request.args.get("q", "").strip()
    show_inactive = request.args.get("show_inactive") == "1"
    query = Product.query
    if not show_inactive:
        query = query.filter(Product.is_active.is_(True))
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Product.name.ilike(like), Product.sku.ilike(like)))
    products_list = query.order_by(Product.updated_at.desc()).all()
    return render_template(
        "admin/products.html", products=products_list, q=q, show_inactive=show_inactive
    )


@admin_bp.route("/products/new", methods=["GET", "POST"])
@login_required
@admin_required
def product_new():
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        return _save_product(None, categories)
    return render_template("admin/product_form.html", product=None, categories=categories)


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        return _save_product(product, categories)
    return render_template(
        "admin/product_form.html", product=product, categories=categories
    )


def _save_product(product, categories):
    name = request.form.get("name", "").strip()
    category_id = request.form.get("category_id", type=int)
    description = request.form.get("description", "").strip()
    price = request.form.get("price", type=float)
    compare_price = request.form.get("compare_price", type=float)
    stock = request.form.get("stock", 0, type=int)
    sku = request.form.get("sku", "").strip()
    is_active = request.form.get("is_active") == "on"

    if not all([name, description, sku]) or price is None or not category_id:
        flash("Please fill in all required fields.", "error")
        return render_template(
            "admin/product_form.html",
            product=product,
            categories=categories,
        )

    slug = slugify(name)
    existing = Product.query.filter(Product.slug == slug)
    if product:
        existing = existing.filter(Product.id != product.id)
    if existing.first():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    if product:
        product.name = name
        product.slug = slug
        product.category_id = category_id
        product.description = description
        product.price = Decimal(str(price))
        product.compare_price = Decimal(str(compare_price)) if compare_price else None
        product.stock = stock
        product.sku = sku
        product.is_active = is_active
        product.updated_at = datetime.utcnow()
    else:
        product = Product(
            name=name,
            slug=slug,
            category_id=category_id,
            description=description,
            price=Decimal(str(price)),
            compare_price=Decimal(str(compare_price)) if compare_price else None,
            stock=stock,
            sku=sku,
            is_active=is_active,
        )
        db.session.add(product)
        db.session.flush()

    images = request.files.getlist("images")
    for idx, image in enumerate(images):
        path = save_product_image(image)
        if path:
            db.session.add(
                ProductImage(
                    product_id=product.id,
                    image_path=path,
                    is_primary=(idx == 0 and not product.images),
                    sort_order=len(product.images) + idx,
                )
            )

    db.session.commit()
    flash("Product saved.", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:product_id>/deactivate", methods=["POST"])
@login_required
@admin_required
def product_deactivate(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = False
    product.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Product deactivated.", "info")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:product_id>/activate", methods=["POST"])
@login_required
@admin_required
def product_activate(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = True
    product.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Product activated.", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        parent_id = request.form.get("parent_id", type=int) or None
        if name:
            slug = slugify(name)
            if Category.query.filter_by(slug=slug).first():
                slug = f"{slug}-{uuid.uuid4().hex[:6]}"
            category = Category(name=name, slug=slug, parent_id=parent_id)
            db.session.add(category)
            db.session.commit()
            flash("Category created.", "success")
        else:
            flash("Category name is required.", "error")
        return redirect(url_for("admin.categories"))

    all_categories = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", categories=all_categories)


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
@admin_required
def category_delete(category_id):
    category = Category.query.get_or_404(category_id)
    if category.products:
        flash("Cannot delete category with products.", "error")
        return redirect(url_for("admin.categories"))
    if category.children:
        flash("Cannot delete category with subcategories.", "error")
        return redirect(url_for("admin.categories"))
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    status = request.args.get("status", "")
    query = Order.query
    if status and status in ["placed", "confirmed", "shipped", "delivered", "cancelled"]:
        query = query.filter_by(status=status)
    orders_list = query.order_by(Order.placed_at.desc()).all()
    return render_template("admin/orders.html", orders=orders_list, status=status)


@admin_bp.route("/orders/<order_number>", methods=["GET", "POST"])
@login_required
@admin_required
def order_detail(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()

    if request.method == "POST":
        new_status = request.form.get("status")
        if new_status in ["placed", "confirmed", "shipped", "delivered", "cancelled"]:
            order.status = new_status
            order.updated_at = datetime.utcnow()
            if new_status == "delivered":
                order.payment_status = "paid"
            db.session.commit()
            flash("Order status updated.", "success")
        return redirect(url_for("admin.order_detail", order_number=order_number))

    return render_template("admin/order_detail.html", order=order)
