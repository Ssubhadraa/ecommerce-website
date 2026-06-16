import os
from datetime import datetime

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config=None):
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///ecommerce.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "uploads", "products"
    )
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    app.config["SHIPPING_FLAT_RATE"] = float(os.getenv("SHIPPING_FLAT_RATE", 50))
    app.config["FREE_SHIPPING_THRESHOLD"] = float(
        os.getenv("FREE_SHIPPING_THRESHOLD", 999)
    )
    app.config["TAX_RATE"] = float(os.getenv("TAX_RATE", 0.18))
    app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif", "webp"}

    if config:
        app.config.update(config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.products import products_bp
    from app.routes.cart import cart_bp
    from app.routes.orders import orders_bp
    from app.routes.admin import admin_bp
    from app.routes.wishlist import wishlist_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from app.models import CartItem, Category, WishlistItem

        cart_count = 0
        wishlist_count = 0
        wishlist_product_ids = set()
        if current_user.is_authenticated:
            cart_count = (
                db.session.query(db.func.coalesce(db.func.sum(CartItem.quantity), 0))
                .filter(CartItem.user_id == current_user.id)
                .scalar()
                or 0
            )
            wishlist_count = WishlistItem.query.filter_by(user_id=current_user.id).count()
            wishlist_product_ids = {
                item.product_id
                for item in WishlistItem.query.filter_by(user_id=current_user.id).all()
            }
        nav_categories = Category.query.filter_by(parent_id=None).order_by(Category.name).limit(8).all()
        return {
            "current_user": current_user,
            "cart_count": int(cart_count),
            "wishlist_count": int(wishlist_count),
            "wishlist_product_ids": wishlist_product_ids,
            "current_year": datetime.utcnow().year,
            "nav_categories": nav_categories,
        }

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        from flask import send_from_directory

        upload_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        return send_from_directory(upload_root, filename)

    @app.template_filter("product_image_url")
    def product_image_url(path):
        if not path:
            from flask import url_for

            return url_for("static", filename="img/placeholders/product.svg")
        if path.startswith("uploads/"):
            return f"/{path}"
        from flask import url_for

        return url_for("static", filename=path)

    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template

        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        from flask import render_template

        return render_template("errors/500.html"), 500

    return app
