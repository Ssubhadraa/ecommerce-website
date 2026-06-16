from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func

from app import db
from app.models import Order, OrderItem, Product


def check_stock(product_id, quantity):
    product = db.session.get(Product, product_id)
    if not product or not product.is_active:
        return False, "Product is unavailable"
    if product.stock < quantity:
        return False, f"Only {product.stock} units available"
    return True, None


def decrement_stock(product_id, quantity):
    product = (
        db.session.query(Product)
        .filter(Product.id == product_id)
        .with_for_update()
        .first()
    )
    if not product or product.stock < quantity:
        raise ValueError(f"Insufficient stock for {product.name if product else product_id}")
    product.stock -= quantity
    product.updated_at = datetime.utcnow()


def get_low_stock_products(threshold=5):
    return (
        Product.query.filter(Product.is_active.is_(True), Product.stock < threshold)
        .order_by(Product.stock.asc())
        .all()
    )
