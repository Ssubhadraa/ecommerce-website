# ShopHub — App Folder Workflow

Yeh document `app/` folder ke andar sab kuch kaise connect hota hai, step-by-step explain karta hai.

---

## 1. Folder Structure

```
app/
├── __init__.py          # App factory — sab kuch yahan jodta hai
├── models/              # Database tables (SQLAlchemy)
├── routes/              # URLs handle karta hai (Blueprints)
├── services/            # Business logic (tax, stock, recommendations)
├── templates/           # HTML pages (Jinja2)
└── static/              # CSS, JS, placeholder images
```

| Folder / File | Role |
|---------------|------|
| `__init__.py` | Flask app create, config, DB, login, blueprints register |
| `models/` | Data structure — User, Product, Order, Cart, etc. |
| `routes/` | HTTP request aaya → logic chala → response bheja |
| `services/` | Reusable logic jo routes se alag rakhi gayi hai |
| `templates/` | User ko dikhne wala HTML |
| `static/` | Browser directly load karta hai (CSS, JS, images) |

---

## 2. App Startup Flow

Server start hone par yeh sequence chalta hai:

```mermaid
flowchart TD
    A["run.py / flask run"] --> B["create_app()"]
    B --> C["Config load"]
    C --> D["db + migrate + login_manager init"]
    D --> E["Blueprints register"]
    E --> F["Context processors + error handlers"]
    F --> G["Flask app ready"]
    G --> H["User requests accept"]
```

**Steps:**

1. Root se `create_app()` call hota hai (`app/__init__.py`).
2. Config set hoti hai — DB URL, secret key, shipping, tax, upload path.
3. Extensions initialize hote hain — `SQLAlchemy`, `Migrate`, `LoginManager`.
4. Saare blueprints register hote hain — auth, products, cart, orders, wishlist, admin.
5. Har template ko global data milta hai — `cart_count`, `wishlist_count`, `nav_categories`.
6. App requests sunne ke liye ready ho jati hai.

---

## 3. Request Lifecycle (Har page ka common flow)

User jab bhi koi URL open karta hai, yeh flow chalta hai:

```mermaid
sequenceDiagram
    participant Browser
    participant Routes as routes
    participant Services as services
    participant Models as models
    participant DB as Database
    participant Templates as templates
    participant Static as static

    Browser->>Routes: HTTP Request
    Routes->>Routes: login_required check if needed
    Routes->>Services: Business logic optional
    Services->>Models: Query or update data
    Models->>DB: SQL
    DB-->>Models: Rows
    Models-->>Routes: Python objects
    Routes->>Templates: render_template(data)
    Templates-->>Browser: HTML response
    Browser->>Static: Load CSS and JS
    Static-->>Browser: Assets
```

**Example:** User `/products` kholta hai

1. `routes/products.py` → `product_list()` run hota hai
2. `Product` model se DB query hoti hai (filter, sort, pagination)
3. `templates/products/list.html` render hota hai
4. Browser `static/css/main.css` aur `static/js/main.js` load karta hai

---

## 4. Architecture Layers

```mermaid
flowchart TB
    subgraph presentation ["Presentation Layer"]
        T["templates"]
        S["static"]
    end

    subgraph controller ["Controller Layer"]
        R["routes"]
    end

    subgraph business ["Business Layer"]
        SV["services"]
    end

    subgraph data ["Data Layer"]
        M["models"]
        DB[("Database")]
    end

    subgraph core ["App Core"]
        I["__init__.py"]
    end

    I --> R
    R --> SV
    R --> M
    SV --> M
    M --> DB
    R --> T
    T --> S
```

| Layer | Responsibility |
|-------|----------------|
| Presentation | UI dikhana — HTML, CSS, JS |
| Controller | URL → action map karna |
| Business | Calculations, recommendations, stock rules |
| Data | DB tables aur relationships |
| App Core | Sab layers ko ek saath jodna |

---

## 5. Blueprint Map (Kaun sa route kahan hai)

```mermaid
flowchart LR
    subgraph auth_bp ["auth blueprint"]
        A1["register"]
        A2["login"]
        A3["account"]
        A4["addresses"]
    end

    subgraph products_bp ["products blueprint"]
        P1["home"]
        P2["product list"]
        P3["product detail"]
        P4["search"]
    end

    subgraph cart_bp ["cart blueprint"]
        C1["view cart"]
        C2["add to cart"]
    end

    subgraph orders_bp ["orders blueprint"]
        O1["checkout"]
        O2["order history"]
        O3["confirmation"]
    end

    subgraph wishlist_bp ["wishlist blueprint"]
        W1["view wishlist"]
        W2["toggle wishlist"]
    end

    subgraph admin_bp ["admin blueprint"]
        AD1["dashboard"]
        AD2["manage products"]
        AD3["manage orders"]
        AD4["manage categories"]
    end
```

---

## 6. Feature Workflows

### 6.1 User Registration and Login

```mermaid
sequenceDiagram
    participant User
    participant Auth as auth route
    participant UserModel as user model
    participant DB as Database

    User->>Auth: POST register
    Auth->>Auth: Validate email password name
    Auth->>UserModel: Create user and hash password
    UserModel->>DB: INSERT into users
    DB-->>User: Redirect to login

    User->>Auth: POST login
    Auth->>UserModel: Find user by email
    UserModel->>UserModel: check_password
    Auth->>Auth: login_user via Flask-Login
    Auth-->>User: Redirect to home
```

**Files involved:** `routes/auth.py`, `models/user.py`, `templates/auth/register.html`, `templates/auth/login.html`

---

### 6.2 Browse and Search Products

```mermaid
flowchart TD
    Start["User opens site"] --> Home["products home route"]
    Home --> Rec["recommendations service"]
    Rec --> Trend["get_trending_products"]
    Rec --> Personal["get_recommended_for_user"]
    Trend --> RenderHome["home template"]
    Personal --> RenderHome

    Start --> List["product list route"]
    List --> Filter["Filter by category price stock sort"]
    Filter --> RenderList["list template"]

    Start --> Detail["product detail route"]
    Detail --> View["Log ProductView in analytics"]
    Detail --> FBT["get_frequently_bought_together"]
    FBT --> RenderDetail["detail template"]
```

---

### 6.3 Add to Cart (AJAX)

```mermaid
sequenceDiagram
    participant User
    participant JS as main.js
    participant Cart as cart route
    participant Inv as inventory service
    participant DB as Database

    User->>JS: Click Add to Cart
    JS->>Cart: POST cart add via AJAX
    Cart->>Cart: login_required check
    Cart->>Inv: check_stock
    Inv-->>Cart: OK or error
    Cart->>DB: Insert or update CartItem
    Cart-->>JS: JSON success and cart_count
    JS->>User: Toast message and badge update
```

**Files involved:** `routes/cart.py`, `models/cart.py`, `services/inventory.py`, `static/js/main.js`

---

### 6.4 Checkout and Place Order

```mermaid
flowchart TD
    A["User goes to checkout"] --> B{"Cart empty?"}
    B -->|Yes| C["Redirect to cart"]
    B -->|No| D["calculate_order_totals"]
    D --> E["checkout service"]
    E --> F["Subtotal Shipping Tax"]
    F --> G["checkout template"]

    G --> H["User selects address and submits"]
    H --> I["Create Order record"]
    I --> J["For each cart item"]
    J --> K["decrement_stock"]
    K --> L["Create OrderItem"]
    L --> M["Delete CartItem"]
    M --> N["db session commit"]
    N --> O["Redirect to confirmation page"]
```

**Checkout totals logic** (`services/checkout.py`):

| Component | Rule |
|-----------|------|
| Subtotal | Saare cart items ka sum |
| Shipping | Flat rate; free agar subtotal >= threshold |
| Tax | Subtotal × TAX_RATE (default 18%) |
| Total | Subtotal + Shipping + Tax |

---

### 6.5 Wishlist Toggle

```mermaid
sequenceDiagram
    participant User
    participant JS as main.js
    participant WL as wishlist route
    participant DB as Database

    User->>JS: Click heart icon
    JS->>WL: POST wishlist toggle
    WL->>DB: Check WishlistItem exists
    alt Already in wishlist
        WL->>DB: DELETE WishlistItem
    else Not in wishlist
        WL->>DB: INSERT WishlistItem
    end
    WL-->>JS: JSON and wishlist_count
    JS->>User: Update badge and toast
```

---

### 6.6 Admin Panel

```mermaid
flowchart TD
    A["Admin visits admin panel"] --> B{"Logged in as admin?"}
    B -->|No| C["Redirect to login"]
    B -->|Yes| D["admin route"]
    D --> E["Dashboard stats and low stock"]
    D --> F["Products CRUD and image upload"]
    D --> G["Categories manage"]
    D --> H["Orders view and status update"]

    F --> I["Save to uploads folder"]
    I --> J["Serve via uploads route in init"]
```

**Admin guard:** `routes/auth.py` mein `admin_required` decorator — sirf `role == "admin"` wale user ko access.

---

### 6.7 Recommendations Engine

```mermaid
flowchart TD
    Input{"User ID available?"} -->|Yes| Collab["Collaborative filtering"]
    Collab -->|Results found| Output["Return products"]
    Collab -->|Empty| Affinity["Category affinity"]
    Affinity -->|Results found| Output
    Affinity -->|Empty| Trend["Trending last 30 days"]
    Input -->|No| Trend
    Trend --> Output
```

**Data sources:**
- `models/analytics.py` → `ProductView` (kya dekha)
- `models/order.py` → `OrderItem` (kya khareeda)
- `services/recommendations.py` → sab logic yahan

---

## 7. Models Relationship (Database)

```mermaid
erDiagram
    User ||--o{ Address : has
    User ||--o{ CartItem : has
    User ||--o{ WishlistItem : has
    User ||--o{ Order : places
    User ||--o{ ProductView : views

    Category ||--o{ Product : contains
    Product ||--o{ ProductImage : has
    Product ||--o{ CartItem : in
    Product ||--o{ WishlistItem : in
    Product ||--o{ OrderItem : in
    Product ||--o{ ProductView : tracked

    Order ||--|{ OrderItem : contains
```

---

## 8. Global Context (Har page pe automatically)

`__init__.py` ka `inject_globals()` har template ko yeh data deta hai:

| Variable | Source | Use |
|----------|--------|-----|
| `current_user` | Flask-Login | Login state, nav links |
| `cart_count` | `CartItem` sum | Header badge |
| `wishlist_count` | `WishlistItem` count | Header badge |
| `wishlist_product_ids` | Wishlist query | Heart icon filled/empty |
| `nav_categories` | Top-level `Category` | Navigation menu |
| `current_year` | `datetime.utcnow()` | Footer copyright |

---

## 9. Static Assets Flow

```mermaid
flowchart LR
    A["base template"] --> B["main.css"]
    A --> C["main.js"]
    D["Product has no image"] --> E["placeholder svg"]
    F["Admin uploads image"] --> G["uploads folder"]
    G --> H["uploads route in init"]
```

**Template filter:** `product_image_url` — image path ko sahi URL mein convert karta hai (upload ya placeholder).

---

## 10. Error Handling

```mermaid
flowchart TD
    A["Request received"] --> B{"Route found?"}
    B -->|No| C["404 error page"]
    B -->|Yes| D{"Server error?"}
    D -->|Yes| E["500 error page"]
    D -->|No| F["Normal response"]
```

Handlers `app/__init__.py` mein registered hain.

---

## 11. Quick Reference — File to Feature

| Feature | Primary files |
|---------|---------------|
| App bootstrap | `app/__init__.py` |
| User auth | `routes/auth.py`, `models/user.py` |
| Product catalog | `routes/products.py`, `models/product.py`, `models/category.py` |
| Shopping cart | `routes/cart.py`, `models/cart.py` |
| Checkout | `routes/orders.py`, `services/checkout.py`, `services/inventory.py` |
| Wishlist | `routes/wishlist.py`, `models/wishlist.py` |
| Recommendations | `services/recommendations.py`, `models/analytics.py` |
| Admin | `routes/admin.py`, `templates/admin/*` |
| UI layout | `templates/base.html`, `static/css/main.css` |
| AJAX interactions | `static/js/main.js` |

---

## 12. End-to-End User Journey

```mermaid
flowchart TD
    S1["Visit home page"] --> S2["Browse or search products"]
    S2 --> S3["View product detail"]
    S3 --> S4{"Logged in?"}
    S4 -->|No| S5["Register or Login"]
    S5 --> S6["Add to cart or wishlist"]
    S4 -->|Yes| S6
    S6 --> S7["Go to cart"]
    S7 --> S8["Checkout select address"]
    S8 --> S9["Order placed stock reduced"]
    S9 --> S10["Confirmation and order history"]
```

Yeh poora flow `app/` folder ke andar ke routes, services, models, templates aur static files mil kar complete karte hain.
