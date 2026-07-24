from __future__ import annotations

from copy import deepcopy
from typing import Any


DOCUMENT_META_FIELDS = [
    "document_type",
    "invoice_number",
    "invoice_date",
    "invoice_date_raw",
    "due_date",
    "issue_date",
    "period_start",
    "period_end",
    "purchase_order_number",
    "sales_order_number",
    "delivery_note_number",
    "contract_reference",
    "project_code",
    "cost_center",
    "language",
    "page_count",
    "is_credit_note",
    "original_invoice_ref",
]

SUPPLIER_FIELDS = [
    "name",
    "legal_entity_name",
    "address_line1",
    "address_line2",
    "city",
    "state",
    "postal_code",
    "country",
    "phone",
    "fax",
    "email",
    "website",
    "tax_id",
    "vat_number",
    "gstin",
    "pan",
    "cin",
    "registration_number",
    "contact_person",
    "logo_present",
]

CUSTOMER_FIELDS = [
    "name",
    "account_number",
    "customer_id",
    "billing_address_line1",
    "billing_address_line2",
    "billing_city",
    "billing_state",
    "billing_postal_code",
    "billing_country",
    "shipping_name",
    "shipping_address_line1",
    "shipping_address_line2",
    "shipping_city",
    "shipping_state",
    "shipping_postal_code",
    "shipping_country",
    "phone",
    "email",
    "tax_id",
    "vat_number",
    "gstin",
    "contact_person",
    "attention_to",
]

LINE_ITEM_FIELDS = [
    "line_number",
    "item_code",
    "sku",
    "hsn_sac_code",
    "description",
    "additional_description",
    "quantity",
    "unit_of_measure",
    "unit_price",
    "list_price",
    "discount_percent",
    "discount_amount",
    "tax_rate_percent",
    "tax_amount",
    "tax_code",
    "line_subtotal",
    "line_total",
    "serial_numbers",
    "batch_number",
    "delivery_date",
    "gl_account",
    "cost_center",
    "notes",
]

TOTAL_FIELDS = [
    "currency_code",
    "currency_symbol",
    "subtotal",
    "total_discount",
    "discount_description",
    "shipping_charge",
    "handling_fee",
    "insurance",
    "packaging_charge",
    "taxable_amount",
    "cgst",
    "sgst",
    "igst",
    "cess",
    "vat_total",
    "total_tax",
    "withholding_tax",
    "tds_amount",
    "round_off",
    "grand_total",
    "amount_paid",
    "credit_applied",
    "advance_adjusted",
    "balance_due",
    "amount_in_words",
    "exchange_rate",
    "base_currency_total",
]

PAYMENT_FIELDS = [
    "payment_terms",
    "payment_terms_days",
    "early_payment_discount",
    "late_fee_terms",
    "payment_method",
    "payment_status",
    "bank_name",
    "bank_branch",
    "account_name",
    "account_number",
    "iban",
    "swift_bic",
    "ifsc",
    "routing_number",
    "sort_code",
    "upi_id",
    "payment_link",
    "payment_reference_instruction",
    "remittance_email",
]

SHIPPING_FIELDS = [
    "shipping_method",
    "carrier",
    "tracking_number",
    "incoterms",
    "ship_date",
    "expected_delivery_date",
    "weight",
    "weight_unit",
    "number_of_packages",
    "vehicle_number",
    "eway_bill_number",
    "port_of_loading",
    "port_of_discharge",
    "country_of_origin",
]

ADDITIONAL_FIELDS = [
    "notes",
    "terms_and_conditions",
    "declaration",
    "footer_text",
    "signature_present",
    "signatory_name",
    "signatory_designation",
    "stamp_present",
    "qr_code_present",
    "qr_code_content",
    "barcode_present",
    "barcode_value",
    "irn",
    "acknowledgement_number",
    "acknowledgement_date",
    "digital_signature_status",
    "watermark_text",
]

VALIDATION_FIELDS = [
    "line_items_sum",
    "line_items_sum_matches_subtotal",
    "computed_grand_total",
    "grand_total_matches",
]

CONFIDENCE_FIELDS = [
    "overall",
    "supplier",
    "customer",
    "line_items",
    "totals",
    "notes_on_low_confidence",
]


def blank_section(fields: list[str]) -> dict[str, Any]:
    return {field: None for field in fields}



def blank_line_item() -> dict[str, Any]:
    item = blank_section(LINE_ITEM_FIELDS)
    item["serial_numbers"] = []
    return item



def blank_other_charge() -> dict[str, Any]:
    return {"label": None, "amount": None}



def blank_tax_breakdown() -> dict[str, Any]:
    return {
        "tax_name": None,
        "tax_rate_percent": None,
        "taxable_base": None,
        "tax_amount": None,
        "jurisdiction": None,
    }



def empty_invoice_output() -> dict[str, Any]:
    return {
        "document_meta": {
            **blank_section(DOCUMENT_META_FIELDS),
            "reference_numbers": [],
        },
        "supplier": blank_section(SUPPLIER_FIELDS),
        "customer": blank_section(CUSTOMER_FIELDS),
        "line_items": [blank_line_item()],
        "totals": {
            **blank_section(TOTAL_FIELDS),
            "other_charges": [blank_other_charge()],
            "tax_breakdown": [blank_tax_breakdown()],
        },
        "payment": blank_section(PAYMENT_FIELDS),
        "shipping": blank_section(SHIPPING_FIELDS),
        "additional": {
            **blank_section(ADDITIONAL_FIELDS),
            "attachments_referenced": [],
        },
        "validation": {
            **blank_section(VALIDATION_FIELDS),
            "arithmetic_discrepancies": [],
            "missing_critical_fields": [],
            "anomalies_detected": [],
        },
        "extraction_confidence": blank_section(CONFIDENCE_FIELDS),
    }


DEFAULT_OUTPUT = empty_invoice_output()



def clone_template() -> dict[str, Any]:
    return deepcopy(DEFAULT_OUTPUT)
