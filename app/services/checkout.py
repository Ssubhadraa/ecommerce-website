from decimal import Decimal

from flask import current_app


def calculate_shipping(subtotal):
    subtotal = Decimal(str(subtotal))
    threshold = Decimal(str(current_app.config["FREE_SHIPPING_THRESHOLD"]))
    flat_rate = Decimal(str(current_app.config["SHIPPING_FLAT_RATE"]))
    if subtotal >= threshold:
        return Decimal("0.00")
    return flat_rate


def calculate_tax(subtotal):
    subtotal = Decimal(str(subtotal))
    rate = Decimal(str(current_app.config["TAX_RATE"]))
    return (subtotal * rate).quantize(Decimal("0.01"))


def calculate_order_totals(cart_items):
    subtotal = sum(Decimal(str(item.line_total)) for item in cart_items)
    shipping = calculate_shipping(subtotal)
    tax = calculate_tax(subtotal)
    total = subtotal + shipping + tax
    return {
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "shipping": shipping.quantize(Decimal("0.01")),
        "tax": tax.quantize(Decimal("0.01")),
        "total": total.quantize(Decimal("0.01")),
    }
