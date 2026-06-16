from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Address, CartItem, Order, OrderItem, Product
from app.services.checkout import calculate_order_totals
from app.services.inventory import decrement_stock

orders_bp = Blueprint("orders", __name__)

VALID_STATUSES = ["placed", "confirmed", "shipped", "delivered", "cancelled"]


def generate_order_number():
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"ORD-{today}-"
    last = (
        Order.query.filter(Order.order_number.like(f"{prefix}%"))
        .order_by(Order.id.desc())
        .first()
    )
    if last:
        seq = int(last.order_number.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


@orders_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items = (
        CartItem.query.filter_by(user_id=current_user.id)
        .join(Product)
        .filter(Product.is_active.is_(True))
        .all()
    )

    if not cart_items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("cart.view_cart"))

    addresses = (
        Address.query.filter_by(user_id=current_user.id)
        .order_by(Address.is_default.desc())
        .all()
    )
    totals = calculate_order_totals(cart_items)

    if request.method == "POST":
        address_id = request.form.get("address_id", type=int)
        address = Address.query.filter_by(
            id=address_id, user_id=current_user.id
        ).first()

        if not address:
            flash("Please select a valid shipping address.", "error")
            return render_template(
                "orders/checkout.html",
                cart_items=cart_items,
                addresses=addresses,
                totals=totals,
            )

        try:
            totals = calculate_order_totals(cart_items)
            order = Order(
                user_id=current_user.id,
                order_number=generate_order_number(),
                status="placed",
                subtotal=totals["subtotal"],
                shipping_cost=totals["shipping"],
                tax=totals["tax"],
                total=totals["total"],
                shipping_address=address.to_dict(),
                payment_method="cod",
                payment_status="pending",
            )
            db.session.add(order)
            db.session.flush()

            for item in cart_items:
                decrement_stock(item.product_id, item.quantity)
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=item.product.name,
                    unit_price=item.product.price,
                    quantity=item.quantity,
                    line_total=item.line_total,
                )
                db.session.add(order_item)
                db.session.delete(item)

            db.session.commit()
            flash("Order placed successfully!", "success")
            return redirect(url_for("orders.confirmation", order_number=order.order_number))

        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        except Exception:
            db.session.rollback()
            flash("Unable to place order. Please try again.", "error")

        totals = calculate_order_totals(cart_items)

    return render_template(
        "orders/checkout.html",
        cart_items=cart_items,
        addresses=addresses,
        totals=totals,
    )


@orders_bp.route("/orders/confirmation/<order_number>")
@login_required
def confirmation(order_number):
    order = Order.query.filter_by(
        order_number=order_number, user_id=current_user.id
    ).first_or_404()
    return render_template("orders/confirmation.html", order=order)


@orders_bp.route("/orders")
@login_required
def order_history():
    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.placed_at.desc())
        .all()
    )
    return render_template("orders/history.html", orders=orders)


@orders_bp.route("/orders/<order_number>")
@login_required
def order_detail(order_number):
    order = Order.query.filter_by(
        order_number=order_number, user_id=current_user.id
    ).first_or_404()
    return render_template("orders/detail.html", order=order)
