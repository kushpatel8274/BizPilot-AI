"""Retail CSV inventory parsing and low-stock reports."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO


REQUIRED_COLUMNS = {"sku", "name", "quantity", "reorder_level"}


@dataclass(frozen=True)
class InventoryItem:
    sku: str
    name: str
    quantity: int
    reorder_level: int


def parse_inventory_csv(csv_text: str) -> list[InventoryItem]:
    if not csv_text.strip():
        raise ValueError("Upload a CSV file with inventory rows.")

    reader = csv.DictReader(StringIO(csv_text))
    headers = {header.strip().lower() for header in (reader.fieldnames or [])}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise ValueError(
            "Inventory CSV is missing required columns: " + ", ".join(sorted(missing)) + "."
        )

    items: list[InventoryItem] = []
    for line_number, raw in enumerate(reader, start=2):
        row = {str(key).strip().lower(): str(value).strip() for key, value in raw.items()}
        try:
            quantity = int(row["quantity"])
            reorder_level = int(row["reorder_level"])
        except ValueError as exc:
            raise ValueError(
                f"Line {line_number}: quantity and reorder_level must be whole numbers."
            ) from exc

        if quantity < 0 or reorder_level < 0:
            raise ValueError(f"Line {line_number}: stock numbers cannot be negative.")
        if not row["sku"] or not row["name"]:
            raise ValueError(f"Line {line_number}: sku and name are required.")

        items.append(
            InventoryItem(
                sku=row["sku"],
                name=row["name"],
                quantity=quantity,
                reorder_level=reorder_level,
            )
        )

    if not items:
        raise ValueError("Inventory CSV does not contain any inventory rows.")
    return items


def low_stock_items(items: list[InventoryItem]) -> list[InventoryItem]:
    return [item for item in items if item.quantity <= item.reorder_level]


def low_stock_report(items: list[InventoryItem]) -> str:
    low_stock = low_stock_items(items)
    if not low_stock:
        return "No low-stock items found."
    lines = ["Low-stock items:"]
    for item in low_stock:
        lines.append(
            f"- {item.sku} | {item.name}: {item.quantity} on hand, reorder at {item.reorder_level}"
        )
    return "\n".join(lines)
