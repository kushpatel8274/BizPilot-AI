
"""BizPilot AI: business calculations and retail inventory utilities."""

import csv
import io


def calculate_profit(income: float, expenses: float) -> float:
    """Calculate profit or loss."""
    if income < 0 or expenses < 0:
        raise ValueError("Income and expenses cannot be negative.")
    return round(income - expenses, 2)


def calculate_profit_margin(income: float, expenses: float) -> float:
    """Calculate profit margin as a percentage of income."""
    profit = calculate_profit(income, expenses)
    if income == 0:
        return 0.0
    return round((profit / income) * 100, 2)


def calculate_invoice_total(
    quantity: int,
    unit_price: float,
    tax_rate: float = 0.0,
    discount: float = 0.0,
) -> float:
    """Calculate an invoice total after discount and tax."""
    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")
    if unit_price < 0:
        raise ValueError("Unit price cannot be negative.")
    if not 0 <= tax_rate <= 100:
        raise ValueError("Tax rate must be between 0 and 100.")
    if not 0 <= discount <= 100:
        raise ValueError("Discount must be between 0 and 100.")

    subtotal = quantity * unit_price
    after_discount = subtotal * (1 - discount / 100)
    total = after_discount * (1 + tax_rate / 100)
    return round(total, 2)


def calculate_stock_value(quantity: int, unit_cost: float) -> float:
    """Calculate the total value of inventory stock."""
    if quantity < 0 or unit_cost < 0:
        raise ValueError("Quantity and unit cost cannot be negative.")
    return round(quantity * unit_cost, 2)


def check_stock(quantity: int, minimum_stock: int = 5) -> str:
    """Return the stock status for a product."""
    if quantity < 0 or minimum_stock < 0:
        raise ValueError("Stock quantities cannot be negative.")
    if quantity == 0:
        return "Out of stock"
    if quantity <= minimum_stock:
        return "Low stock"
    return "Stock available"


def calculate_total_expenses(expenses: list[float]) -> float:
    """Calculate the sum of expense amounts."""
    if any(amount < 0 for amount in expenses):
        raise ValueError("Expenses cannot be negative.")
    return round(sum(expenses), 2)



def parse_inventory_csv(csv_text: str) -> list[dict]:
    """
    Parse and validate inventory CSV data.

    Required fields: sku, name, quantity, reorder_level.
    Additional CSV columns are accepted but ignored.
    This function never saves to a database.
    """
    import csv
    import io
    import re

    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))

    if not reader.fieldnames:
        raise ValueError("The CSV file is empty or has no header row.")

    # Normalize headers: Product Name -> product_name
    def normalize_header(header):
        return re.sub(
            r"_+", "_",
            re.sub(r"[^a-z0-9]+", "_", (header or "").strip().lower())
        ).strip("_")

    aliases = {
        "sku": {
            "sku", "product_sku", "item_code", "product_code",
            "item_sku", "stock_code"
        },
        "name": {
            "name", "product_name", "item_name", "product",
            "item", "description"
        },
        "quantity": {
            "quantity", "qty", "stock", "stock_quantity",
            "available_quantity", "current_stock"
        },
        "reorder_level": {
            "reorder_level", "reorder_qty", "minimum_stock",
            "min_stock", "reorder_point", "minimum_quantity"
        },
    }

    # Map each required field to its actual CSV header.
    header_map = {}
    used_headers = set()

    for original_header in reader.fieldnames:
        normalized = normalize_header(original_header)

        for required_field, alternatives in aliases.items():
            if normalized in alternatives:
                if required_field in header_map:
                    raise ValueError(
                        f"Multiple CSV columns match '{required_field}'. "
                        "Keep only one matching column."
                    )

                header_map[required_field] = original_header
                used_headers.add(original_header)
                break

    missing = set(aliases) - set(header_map)

    if missing:
        raise ValueError(
            "Missing required CSV columns: "
            + ", ".join(sorted(missing))
            + ". Accepted alternatives include product_name for name, "
              "qty for quantity, item_code for sku, and min_stock "
              "for reorder_level."
        )

    inventory = []
    seen_skus = set()

    for line_number, original_row in enumerate(reader, start=2):
        # Extra values beyond the header count are malformed.
        if None in original_row:
            raise ValueError(
                f"Invalid data on CSV line {line_number}: "
                "too many columns."
            )

        # Read only the required fields; extra columns are ignored.
        row = {
            field: original_row.get(actual_header)
            for field, actual_header in header_map.items()
        }

        # Ignore completely blank rows.
        if not any(
            isinstance(value, str) and value.strip()
            for value in row.values()
        ):
            continue

        try:
            sku = (row.get("sku") or "").strip()
            name = (row.get("name") or "").strip()
            quantity_text = (row.get("quantity") or "").strip()
            reorder_text = (row.get("reorder_level") or "").strip()

            if not sku or not name:
                raise ValueError("SKU and product name are required.")

            if sku in seen_skus:
                raise ValueError(f"Duplicate SKU: {sku}")

            quantity = int(quantity_text)
            reorder_level = int(reorder_text)

            if quantity < 0 or reorder_level < 0:
                raise ValueError("Quantities cannot be negative.")

        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid data on CSV line {line_number}: {exc}"
            ) from exc

        seen_skus.add(sku)

        inventory.append({
            "sku": sku,
            "name": name,
            "quantity": quantity,
            "reorder_level": reorder_level,
        })

    if not inventory:
        raise ValueError("The CSV contains no inventory records.")

    return inventory



def low_stock_report(inventory: list[dict]) -> str:
    """Generate a report of products at or below their reorder level."""
    low_stock = [
        item for item in inventory
        if item["quantity"] <= item["reorder_level"]
    ]

    if not low_stock:
        return "All inventory items are above their reorder levels."

    lines = ["LOW-STOCK INVENTORY REPORT", ""]

    for item in low_stock:
        status = (
            "OUT OF STOCK"
            if item["quantity"] == 0
            else "LOW STOCK"
        )
        lines.append(
            f"{item['name']} (SKU: {item['sku']}) — "
            f"Quantity: {item['quantity']}, "
            f"Reorder level: {item['reorder_level']} [{status}]"
        )

    return "\n".join(lines)
