from decimal import Decimal

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import CartItem, Category, Product, ProductView
from app.services.recommendations import (
    get_frequently_bought_together,
    get_recommended_for_user,
    get_trending_products,
)

products_bp = Blueprint("products", __name__)


@products_bp.route("/")
def home():
    categories = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
    user_id = current_user.id if current_user.is_authenticated else None
    recommended = get_recommended_for_user(user_id, limit=8)
    trending = get_trending_products(limit=8)
    return render_template(
        "products/home.html",
        categories=categories,
        recommended=recommended,
        trending=trending,
    )


@products_bp.route("/products")
def product_list():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    category_slug = request.args.get("category", "")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    availability = request.args.get("availability", "")
    sort = request.args.get("sort", "newest")

    query = Product.query.filter(Product.is_active.is_(True))

    current_category = None
    if category_slug:
        current_category = Category.query.filter_by(slug=category_slug).first()
        if current_category:
            cat_ids = current_category.all_descendant_ids
            query = query.filter(Product.category_id.in_(cat_ids))

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Product.name.ilike(like), Product.description.ilike(like))
        )

    if min_price is not None:
        query = query.filter(Product.price >= Decimal(str(min_price)))
    if max_price is not None:
        query = query.filter(Product.price <= Decimal(str(max_price)))

    if availability == "in_stock":
        query = query.filter(Product.stock > 0)
    elif availability == "out_of_stock":
        query = query.filter(Product.stock <= 0)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "popularity":
        query = query.order_by(Product.stock.desc(), Product.created_at.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(parent_id=None).order_by(Category.name).all()

    breadcrumbs = []
    if current_category:
        breadcrumbs = current_category.breadcrumb()

    return render_template(
        "products/list.html",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        current_category=current_category,
        breadcrumbs=breadcrumbs,
        q=q,
        filters={
            "category": category_slug,
            "min_price": min_price,
            "max_price": max_price,
            "availability": availability,
            "sort": sort,
        },
    )


@products_bp.route("/products/<slug>")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()

    view = ProductView(
        user_id=current_user.id if current_user.is_authenticated else None,
        product_id=product.id,
    )
    db.session.add(view)
    db.session.commit()

    bought_together = get_frequently_bought_together(product.id, limit=4)
    breadcrumbs = product.category.breadcrumb() if product.category else []

    return render_template(
        "products/detail.html",
        product=product,
        bought_together=bought_together,
        breadcrumbs=breadcrumbs,
    )


@products_bp.route("/category/<slug>")
def category_page(slug):
    return redirect(url_for("products.product_list", category=slug))


@products_bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    return redirect(url_for("products.product_list", q=q))
