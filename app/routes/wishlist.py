from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Product, WishlistItem

wishlist_bp = Blueprint("wishlist", __name__)


@wishlist_bp.route("/wishlist")
@login_required
def view_wishlist():
    items = (
        WishlistItem.query.filter_by(user_id=current_user.id)
        .join(Product)
        .filter(Product.is_active.is_(True))
        .order_by(WishlistItem.added_at.desc())
        .all()
    )
    return render_template("wishlist/wishlist.html", items=items)


@wishlist_bp.route("/wishlist/toggle", methods=["POST"])
@login_required
def toggle_wishlist():
    if request.is_json:
        product_id = request.json.get("product_id")
    else:
        product_id = request.form.get("product_id", type=int)

    try:
        product_id = int(product_id) if product_id is not None else None
    except (TypeError, ValueError):
        product_id = None

    product = Product.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        message = "Product not found."
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": message}), 404
        flash(message, "error")
        return redirect(request.referrer or url_for("products.home"))

    item = WishlistItem.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first()

    if item:
        db.session.delete(item)
        db.session.commit()
        in_wishlist = False
        message = f"{product.name} removed from wishlist"
    else:
        db.session.add(WishlistItem(user_id=current_user.id, product_id=product_id))
        db.session.commit()
        in_wishlist = True
        message = f"{product.name} added to wishlist"

    wishlist_count = WishlistItem.query.filter_by(user_id=current_user.id).count()

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "success": True,
                "message": message,
                "in_wishlist": in_wishlist,
                "wishlist_count": wishlist_count,
            }
        )

    flash(message, "success")
    return redirect(request.referrer or url_for("wishlist.view_wishlist"))
