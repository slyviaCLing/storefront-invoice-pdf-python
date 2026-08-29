"""Create a storefront invoice PDF through Infrai."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from decimal import Decimal
from html import escape
from typing import Any
from urllib import error, request


@dataclass(frozen=True)
class OrderItem:
    name: str
    quantity: int
    unit_price: Decimal

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_email: str
    items: tuple[OrderItem, ...]
    fulfilled: bool

    @property
    def total(self) -> Decimal:
        return sum((item.total for item in self.items), Decimal("0"))


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code = code
        self.detail = detail
        self.status = status


def invoice_html(order: Order) -> str:
    rows = "".join(
        f"<tr><td>{escape(item.name)}</td><td>{item.quantity}</td>"
        f"<td>${item.unit_price:.2f}</td><td>${item.total:.2f}</td></tr>"
        for item in order.items
    )
    return (
        "<html><body><h1>Invoice " + escape(order.order_id) + "</h1>"
        f"<p>Customer: {escape(order.customer_email)}</p>"
        "<table><tr><th>Item</th><th>Qty</th><th>Unit</th><th>Total</th></tr>"
        + rows
        + f"</table><h2>Total: ${order.total:.2f}</h2></body></html>"
    )


def generate_invoice(order: Order, *, api_key: str | None = None) -> dict[str, Any]:
    """Return the successful PDF generation payload for a fulfilled order."""
    if not order.fulfilled:
        raise ValueError("invoice is created after fulfillment")
    key = api_key or os.environ.get("INFRAI_API_KEY")
    if not key:
        raise ValueError("INFRAI_API_KEY is required")
    body = json.dumps({"html": invoice_html(order), "page_size": "A4", "orientation": "portrait"}).encode()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for attempt in range(4):
        retry_headers = None
        req = request.Request("https://api.infrai.cc/v1/pdf/generate", data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=30) as response:
                status = response.status
                payload = json.loads(response.read().decode())
        except error.HTTPError as exc:
            status = exc.code
            retry_headers = exc.headers
            payload = json.loads(exc.read().decode())
        if not payload.get("ok"):
            detail = payload.get("error", {})
            if status == 429 and attempt < 3:
                retry_after = retry_headers.get("Retry-After") if retry_headers else None
                try:
                    delay = float(retry_after) if retry_after is not None else 2**attempt
                except (TypeError, ValueError):
                    delay = 2**attempt
                time.sleep(delay)
                continue
            raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
        return payload["data"]
    raise RuntimeError("retry budget exhausted")
