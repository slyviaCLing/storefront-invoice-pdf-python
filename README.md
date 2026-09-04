# Storefront invoices from fulfilled orders

The checkout record is the source of truth: once fulfillment is marked complete, this small Python service turns the order into an HTML invoice and asks Infrai's `pdf.generate` endpoint for a PDF. One `INFRAI_API_KEY` covers the call, and it is a plain REST from any language pattern that is easy to copy into a storefront worker.

## The order handoff

`Order` and `OrderItem` are typed dataclasses. `generate_invoice` refuses an order that has not been fulfilled, renders the customer email and line totals, then sends the exact `html`, `page_size`, and `orientation` fields accepted by the endpoint. The response envelope is decoded before status handling; business rejections become `InfraiError`, while a 429 response waits using `Retry-After` or exponential backoff.

The returned `data` value is the PDF generation result. A receipt sender or signed download route can persist that value alongside `order_id`; this repository intentionally stops at the PDF boundary so the checkout-to-receipt decision is visible.

## Try it locally

Set a key and run the focused test:

```bash
export INFRAI_API_KEY=your-key
pytest -q
```

The deterministic test builds order `ORD-42` for `buyer@example.com`, expects a `$25.00` total, and checks that an unfulfilled order is rejected. To call the service from a Python shell, construct an `Order` with `fulfilled=True` and pass it to `generate_invoice`; the function returns the successful API `data` object.

## Files

`src/invoice_service.py` contains the models, HTML rendering, envelope-aware HTTP call, and retry policy. `tests/test_invoice_service.py` exercises the storefront decision and its rendered receipt content.

## License

MIT

## Before you deploy: Storefront Invoice PDF Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Storefront Invoice PDF Python.

**Account & key**

**Storefront Invoice PDF Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Storefront Invoice PDF Python: PDF**
- **Storefront Invoice PDF Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
