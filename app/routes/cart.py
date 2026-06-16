from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import CartItem, Product
from app.services.inventory import check_stock
from app.services.recommendations import get_cart_recommendations

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/cart")
@login_required
def view_cart():
    items = (
        CartItem.query.filter_by(user_id=current_user.id)
        .join(Product)
        .filter(Product.is_active.is_(True))
        .all()
    )
    subtotal = sum(item.line_total for item in items)
    cart_product_ids = [item.product_id for item in items]
    recommendations = get_cart_recommendations(
        current_user.id, cart_product_ids, limit=8
    )
    return render_template(
        "cart/cart.html",
        items=items,
        subtotal=subtotal,
        recommendations=recommendations,
    )


@cart_bp.route("/cart/add", methods=["POST"])
@login_required
def add_to_cart():
    if request.is_json:
        product_id = request.json.get("product_id")
        quantity = request.json.get("quantity", 1)
    else:
        product_id = request.form.get("product_id", type=int)
        quantity = request.form.get("quantity", 1, type=int)

    try:
        product_id = int(product_id) if product_id is not None else None
    except (TypeError, ValueError):
        product_id = None

    product = Product.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": "Product not found"}), 404
        flash("Product not found.", "error")
        return redirect(request.referrer or url_for("products.home"))

    ok, message = check_stock(product_id, quantity)
    if not ok:
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": message}), 400
        flash(message, "error")
        return redirect(request.referrer or url_for("products.product_detail", slug=product.slug))

    cart_item = CartItem.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first()

    new_qty = quantity
    if cart_item:
        new_qty = cart_item.quantity + quantity
        ok, message = check_stock(product_id, new_qty)
        if not ok:
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": False, "message": message}), 400
            flash(message, "error")
            return redirect(request.referrer or url_for("cart.view_cart"))
        cart_item.quantity = new_qty
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)

    db.session.commit()

    cart_count = (
        db.session.query(db.func.coalesce(db.func.sum(CartItem.quantity), 0))
        .filter(CartItem.user_id == current_user.id)
        .scalar()
        or 0
    )

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "success": True,
                "message": f"{product.name} added to cart",
                "cart_count": int(cart_count),
            }
        )

    flash(f"{product.name} added to cart.", "success")
    return redirect(request.referrer or url_for("cart.view_cart"))


@cart_bp.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def update_cart_item(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    quantity = request.form.get("quantity", 1, type=int)

    if quantity <= 0:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed from cart.", "info")
        return redirect(url_for("cart.view_cart"))

    ok, message = check_stock(item.product_id, quantity)
    if not ok:
        flash(message, "error")
        return redirect(url_for("cart.view_cart"))

    item.quantity = quantity
    db.session.commit()
    flash("Cart updated.", "success")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_cart_item(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/cart/count")
@login_required
def cart_count():
    count = (
        db.session.query(db.func.coalesce(db.func.sum(CartItem.quantity), 0))
        .filter(CartItem.user_id == current_user.id)
        .scalar()
        or 0
    )
    return jsonify({"count": int(count)})
