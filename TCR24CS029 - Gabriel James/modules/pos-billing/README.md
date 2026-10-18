# Point of Sale Billing module

Standalone hospital module of the CareWeave system. Python and Flask only: the module, its user
interface, its tests and its SQLite database are entirely Python, exactly as the assignment
requires for the Flask part of the system.

## Run

```
python3 run.py
```

Install the dependencies first when the interpreter does not already provide them:

```
python3 -m pip install -r requirements.txt
```

The module listens on `http://127.0.0.1:5005` and stores its data in `data/pos_billing.db`
(SQLite, WAL mode). `CAREWEAVE_DB` and `CAREWEAVE_PORT` override the database file and the port.

The module installs its demonstration data at startup; `python3 seed.py` reruns the same
idempotent installation. No dependency of this module reaches the
internet at run time: the pages use only local CSS and JavaScript and the module makes no
outbound calls.

## Capability endpoints

| Capability | Method and path | Purpose |
| --- | --- | --- |
| BILL-GenerateInvoice | POST /api/generate_invoice | Generate an invoice with amount and description |
| BILL-ProcessPayment | POST /api/process_payment | Pay an invoice; cash below the amount is rejected |
| BILL-GetReceipt | POST /api/get_receipt | Read receipt text and payment status |
| BILL-SendReceiptNotice | POST /api/send_receipt_notice | Send a receipt notice for a paid invoice |
| BILL-Form | POST /ui/payments/new | GUI payment form (same code path as BILL-ProcessPayment) |

Every API call accepts a JSON object of the inputs named in `spec.json` and answers with

```json
{"status": "ok", "capability": "BILL-ProcessPayment", "outputs": {...}, "effects": [...],
 "state": {...}, "trace": ["BILL-ProcessPayment executed"]}
```

or, on rejection, `{"status": "error", "capability": "...", "error": "..."}` with status 400
(bad input or a cash tender below the invoice amount), 404 (unknown invoice) or 409 (the invoice
is already paid, or a receipt notice is requested before payment). Read-only endpoints:
`GET /health`, `GET /spec`, `GET /state`.

The state variable `Invoice.amount` reports the outstanding amount: the sum of the amounts of
the invoices that are not yet paid.

## Screens

| Page | Path | Fields and stable element ids |
| --- | --- | --- |
| Home | /ui/ | Summary counts, capability table, `id="module_title"` |
| Invoices | /ui/invoices | Search `id="search_input"`, table `id="invoice_table"` |
| New invoice | /ui/invoices/new | `id="invoice_form"` with `id="patient_mrn_input"`, `id="amount_input"`, `id="description_input"`, submit `id="submit_button"`, result `id="result_output"` |
| Invoice detail | /ui/invoices/<invoice_id> | Payment form `id="payment_form"` (`id="method_select"`, `id="tendered_input"`), notice form `id="notice_form"` once paid, notice table `id="notice_table"` |
| Take payment | /ui/payments/new | `id="payment_form"` with `id="invoice_select"`, `id="method_select"`, `id="tendered_input"`, submit `id="submit_button"`, result `id="result_output"` |
| Capabilities | /ui/capabilities | Formal tuple of every capability from `spec.json` |

Sample values: MRN `MRN-1001`, amount `42.50`, tender `50.00`, method `CASH`, channel `EMAIL`.
A cash tender below the invoice amount is rejected with status 400; paying an invoice twice is
rejected with status 409.

## Tests

```
python3 -m pytest tests -q --cov=. --cov-report=term
```

The suite creates a temporary database per test and exercises every capability, the tender and
payment rules, the UI forms with their stable ids and the offline asset check.
