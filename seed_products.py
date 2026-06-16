import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app, db
from app.models import (
    Address,
    CartItem,
    Category,
    Order,
    OrderItem,
    Product,
    ProductImage,
    ProductView,
    User,
)

COLORS = ["#FF9900", "#007185", "#232F3E", "#067D62", "#B12704", "#37475A", "#131921", "#C45500"]

CATEGORIES = [
    {"name": "Electronics", "children": ["Smartphones", "Laptops", "Audio"]},
    {"name": "Clothing", "children": ["Men", "Women"]},
    {"name": "Books", "children": []},
    {"name": "Home & Kitchen", "children": []},
    {"name": "Sports", "children": []},
    {"name": "Beauty", "children": []},
    {"name": "Toys", "children": []},
    {"name": "Groceries", "children": []},
]

PRODUCT_NAMES = {
    "Electronics": [
        "Wireless Earbuds Pro", "USB-C Hub Adapter", "Portable Power Bank 20000mAh",
        "Bluetooth Speaker Mini", "Smart Watch Series X", "4K Action Camera",
        "Mechanical Keyboard RGB", "Wireless Mouse Ergo", "Tablet Stand Adjustable",
        "HD Webcam 1080p", "Noise Cancelling Headphones", "Smart Home Plug",
    ],
    "Clothing": [
        "Classic Cotton T-Shirt", "Slim Fit Denim Jeans", "Running Sneakers",
        "Winter Fleece Jacket", "Linen Casual Shirt", "Athletic Shorts",
        "Wool Blend Sweater", "Leather Belt", "Canvas Backpack",
    ],
    "Books": [
        "Python Programming Guide", "The Art of Product Design", "Mindful Living",
        "Business Strategy 101", "Fantasy Epic Vol. 1", "Cookbook: Indian Flavors",
    ],
    "Home & Kitchen": [
        "Stainless Steel Cookware Set", "Non-Stick Frying Pan", "Electric Kettle 1.7L",
        "Memory Foam Pillow", "LED Desk Lamp", "Storage Container Set",
    ],
    "Sports": [
        "Yoga Mat Premium", "Adjustable Dumbbells", "Resistance Bands Set",
        "Sports Water Bottle", "Tennis Racket Pro", "Cycling Helmet",
    ],
    "Beauty": [
        "Hydrating Face Serum", "SPF 50 Sunscreen", "Argan Oil Shampoo",
        "Vitamin C Moisturizer", "Lip Balm Set", "Charcoal Face Mask",
    ],
    "Toys": [
        "Building Blocks 500pc", "Remote Control Car", "Plush Teddy Bear",
        "Board Game Family Pack", "Art Supply Kit", "Puzzle 1000 Pieces",
    ],
    "Groceries": [
        "Organic Green Tea 100g", "Extra Virgin Olive Oil", "Mixed Nuts 500g",
        "Whole Grain Pasta", "Dark Chocolate Bar", "Granola Breakfast Mix",
        "Honey Raw Organic", "Instant Coffee Premium",
    ],
}


def slugify(text):
    import re

    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text)[:120]


def create_placeholder_svg(path, label, color):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
  <rect width="400" height="400" fill="#f7fafa"/>
  <rect x="40" y="40" width="320" height="320" rx="16" fill="{color}" opacity="0.15"/>
  <circle cx="200" cy="180" r="60" fill="{color}" opacity="0.35"/>
  <text x="200" y="300" text-anchor="middle" fill="#565959" font-family="Inter, sans-serif" font-size="16">{label[:28]}</text>
</svg>"""
    with open(path, "w") as f:
        f.write(svg)


def seed():
    app = create_app()
    with app.app_context():
        upload_dir = app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)

        if User.query.filter_by(email="admin@shop.com").first():
            print("Database already seeded. Skipping.")
            return

        admin = User(
            email="admin@shop.com",
            full_name="Shop Admin",
            phone="9999999999",
            role="admin",
        )
        admin.set_password("admin123")
        db.session.add(admin)

        customers = []
        for i in range(1, 6):
            user = User(
                email=f"customer{i}@example.com",
                full_name=f"Customer {i}",
                phone=f"987654321{i}",
            )
            user.set_password("password123")
            db.session.add(user)
            customers.append(user)
        db.session.flush()

        for user in customers:
            db.session.add(
                Address(
                    user_id=user.id,
                    label="Home",
                    line1=f"{100 + user.id} Main Street",
                    city="Mumbai",
                    state="Maharashtra",
                    pincode="400001",
                    is_default=True,
                )
            )

        category_map = {}
        for idx, cat_data in enumerate(CATEGORIES):
            parent = Category(
                name=cat_data["name"],
                slug=slugify(cat_data["name"]),
            )
            db.session.add(parent)
            db.session.flush()
            category_map[cat_data["name"]] = parent

            for child_name in cat_data["children"]:
                child = Category(
                    name=child_name,
                    slug=slugify(f"{cat_data['name']}-{child_name}"),
                    parent_id=parent.id,
                )
                db.session.add(child)
                db.session.flush()
                category_map[child_name] = child

        all_products = []
        sku_counter = 1000
        color_idx = 0
        product_count = 0

        for cat_name, names in PRODUCT_NAMES.items():
            if product_count >= 50:
                break
            parent_cat = category_map[cat_name]
            assign_cats = [parent_cat] + list(parent_cat.children)
            for name in names:
                if product_count >= 50:
                    break
                sku_counter += 1
                cat = random.choice(assign_cats)
                price = Decimal(str(random.randint(199, 9999)))
                compare = price + Decimal(str(random.randint(50, 500))) if random.random() > 0.5 else None
                stock = random.randint(3, 50)

                filename = f"product-{sku_counter}.svg"
                filepath = os.path.join(upload_dir, filename)
                create_placeholder_svg(
                    filepath, name, COLORS[color_idx % len(COLORS)]
                )
                color_idx += 1

                product = Product(
                    category_id=cat.id,
                    name=name,
                    slug=f"{slugify(name)}-{sku_counter}",
                    description=(
                        f"{name} — premium quality product from our {cat.name} collection. "
                        f"Great value, fast delivery, and trusted by thousands of shoppers."
                    ),
                    price=price,
                    compare_price=compare,
                    stock=stock,
                    sku=f"SKU-{sku_counter}",
                    is_active=True,
                )
                db.session.add(product)
                db.session.flush()

                db.session.add(
                    ProductImage(
                        product_id=product.id,
                        image_path=f"uploads/products/{filename}",
                        is_primary=True,
                        sort_order=0,
                    )
                )
                all_products.append(product)
                product_count += 1

        db.session.flush()

        order_counter = 0
        for day_offset in range(0, 25, 3):
            for customer in customers[:4]:
                order_counter += 1
                items = random.sample(all_products, k=random.randint(2, 4))
                subtotal = Decimal("0")
                order_items_data = []

                for product in items:
                    qty = random.randint(1, 2)
                    unit = product.price
                    line = unit * qty
                    subtotal += line
                    order_items_data.append((product, qty, unit, line))

                shipping = Decimal("0") if subtotal >= 999 else Decimal("50")
                tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
                total = subtotal + shipping + tax
                addr = customer.addresses[0]

                order = Order(
                    user_id=customer.id,
                    order_number=f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{order_counter:03d}",
                    status=random.choice(["placed", "confirmed", "shipped", "delivered"]),
                    subtotal=subtotal,
                    shipping_cost=shipping,
                    tax=tax,
                    total=total,
                    shipping_address=addr.to_dict(),
                    payment_method="cod",
                    payment_status="pending",
                    placed_at=datetime.utcnow() - timedelta(days=day_offset),
                )
                db.session.add(order)
                db.session.flush()

                for product, qty, unit, line in order_items_data:
                    db.session.add(
                        OrderItem(
                            order_id=order.id,
                            product_id=product.id,
                            product_name=product.name,
                            unit_price=unit,
                            quantity=qty,
                            line_total=line,
                        )
                    )

        for customer in customers:
            viewed = random.sample(all_products, k=8)
            for product in viewed:
                db.session.add(
                    ProductView(
                        user_id=customer.id,
                        product_id=product.id,
                        viewed_at=datetime.utcnow() - timedelta(days=random.randint(1, 20)),
                    )
                )

        db.session.commit()
        print(f"Seeded {Category.query.count()} categories")
        print(f"Seeded {Product.query.count()} products")
        print(f"Seeded {User.query.count()} users")
        print(f"Seeded {Order.query.count()} orders")
        print("Admin login: admin@shop.com / admin123")
        print("Sample customer: customer1@example.com / password123")


if __name__ == "__main__":
    seed()
