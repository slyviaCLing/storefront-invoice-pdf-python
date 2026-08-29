from decimal import Decimal

import pytest

from src.invoice_service import Order, OrderItem, invoice_html


def test_fulfilled_order_html_contains_totals_and_customer():
    order = Order("ORD-42", "buyer@example.com", (OrderItem("Coffee beans", 2, Decimal("12.50")),), True)
    html = invoice_html(order)
    assert "ORD-42" in html
    assert "buyer@example.com" in html
    assert "Total: $25.00" in html


def test_unfulfilled_order_is_not_invoiceable():
    order = Order("ORD-43", "buyer@example.com", (), False)
    with pytest.raises(ValueError, match="fulfillment"):
        from src.invoice_service import generate_invoice
        generate_invoice(order, api_key="test")
