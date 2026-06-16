from datetime import datetime, timedelta

from sqlalchemy import func

from app import db
from app.models import Order, OrderItem, Product, ProductView


def _active_in_stock_query():
    return Product.query.filter(Product.is_active.is_(True), Product.stock > 0)


def get_trending_products(limit=12, days=30):
    since = datetime.utcnow() - timedelta(days=days)
    results = (
        db.session.query(Product, func.count(OrderItem.id).label("order_count"))
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.placed_at >= since,
            Product.is_active.is_(True),
            Product.stock > 0,
        )
        .group_by(Product.id)
        .order_by(func.count(OrderItem.id).desc())
        .limit(limit)
        .all()
    )
    return [row[0] for row in results]


def get_frequently_bought_together(product_id, limit=4):
    results = (
        db.session.query(Product, func.count().label("freq"))
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(
            OrderItem,
            OrderItem.order_id == OrderItem.order_id,
            isouter=False,
        )
    )
    # Correct query using alias
    oi1 = db.aliased(OrderItem)
    oi2 = db.aliased(OrderItem)
    results = (
        db.session.query(Product, func.count().label("freq"))
        .join(oi2, Product.id == oi2.product_id)
        .join(oi1, oi1.order_id == oi2.order_id)
        .filter(
            oi1.product_id == product_id,
            oi2.product_id != product_id,
            Product.is_active.is_(True),
            Product.stock > 0,
        )
        .group_by(Product.id)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )
    return [row[0] for row in results]


def get_collaborative_recommendations(user_id, limit=12):
    purchased_ids = (
        db.session.query(OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.user_id == user_id)
        .distinct()
        .all()
    )
    purchased_ids = [pid for (pid,) in purchased_ids]
    if not purchased_ids:
        return []

    oi_target = db.aliased(OrderItem)
    oi_other = db.aliased(OrderItem)

    results = (
        db.session.query(Product, func.count().label("score"))
        .join(oi_other, Product.id == oi_other.product_id)
        .join(oi_target, oi_target.order_id == oi_other.order_id)
        .filter(
            oi_target.product_id.in_(purchased_ids),
            ~oi_other.product_id.in_(purchased_ids),
            Product.is_active.is_(True),
            Product.stock > 0,
        )
        .group_by(Product.id)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )
    return [row[0] for row in results]


def get_category_affinity_recommendations(user_id, limit=12):
    viewed = (
        db.session.query(ProductView.product_id)
        .filter(ProductView.user_id == user_id)
        .order_by(ProductView.viewed_at.desc())
        .limit(20)
        .all()
    )
    viewed_ids = [pid for (pid,) in viewed]
    if not viewed_ids:
        return []

    category_ids = (
        db.session.query(Product.category_id)
        .filter(Product.id.in_(viewed_ids))
        .distinct()
        .all()
    )
    category_ids = [cid for (cid,) in category_ids]

    purchased_ids = (
        db.session.query(OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.user_id == user_id)
        .distinct()
        .all()
    )
    purchased_ids = [pid for (pid,) in purchased_ids]

    query = _active_in_stock_query().filter(Product.category_id.in_(category_ids))
    if purchased_ids:
        query = query.filter(~Product.id.in_(purchased_ids))
    if viewed_ids:
        query = query.filter(~Product.id.in_(viewed_ids))

    return query.order_by(Product.created_at.desc()).limit(limit).all()


def get_recommended_for_user(user_id, limit=12):
    if user_id:
        collab = get_collaborative_recommendations(user_id, limit)
        if collab:
            return collab
        affinity = get_category_affinity_recommendations(user_id, limit)
        if affinity:
            return affinity
    return get_trending_products(limit)


def get_cart_recommendations(user_id, cart_product_ids, limit=8):
    exclude = set(cart_product_ids or [])
    recommendations = []

    if user_id:
        recommendations = get_collaborative_recommendations(user_id, limit + len(exclude))
        recommendations = [p for p in recommendations if p.id not in exclude][:limit]

    if len(recommendations) < limit:
        trending = get_trending_products(limit + len(exclude))
        for product in trending:
            if product.id not in exclude and product not in recommendations:
                recommendations.append(product)
            if len(recommendations) >= limit:
                break

    return recommendations[:limit]
