from datetime import datetime

from app import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False, index=True)
    compare_price = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    category = db.relationship("Category", back_populates="products")
    images = db.relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order",
    )
    cart_items = db.relationship("CartItem", back_populates="product")
    wishlist_items = db.relationship("WishlistItem", back_populates="product")
    order_items = db.relationship("OrderItem", back_populates="product")
    views = db.relationship("ProductView", back_populates="product")

    @property
    def primary_image(self):
        primary = next((img for img in self.images if img.is_primary), None)
        if primary:
            return primary.image_path
        if self.images:
            return self.images[0].image_path
        return "img/placeholders/product.svg"

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def discount_percent(self):
        if self.compare_price and self.compare_price > self.price:
            return int(
                ((float(self.compare_price) - float(self.price)) / float(self.compare_price))
                * 100
            )
        return 0


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    image_path = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)

    product = db.relationship("Product", back_populates="images")
