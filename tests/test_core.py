import sqlite3
import unittest

from bizpilot.approvals import ApprovalAction, create_approval
from bizpilot.database import Draft, initialize, list_drafts, save_draft
from bizpilot.freelance import FreelanceRequest, validate_request
from bizpilot.retail import low_stock_items, low_stock_report, parse_inventory_csv


class CoreTests(unittest.TestCase):
    def test_freelance_validation_requires_real_business_details(self):
        request = FreelanceRequest(business_name="", client_name="Acme", service="")

        with self.assertRaisesRegex(ValueError, "business name, service"):
            validate_request(request)

    def test_retail_low_stock_report_from_csv(self):
        items = parse_inventory_csv(
            "sku,name,quantity,reorder_level\nA1,Notebook,3,5\nB2,Pen,12,5\n"
        )

        self.assertEqual([item.sku for item in low_stock_items(items)], ["A1"])
        self.assertIn("A1 | Notebook", low_stock_report(items))

    def test_retail_csv_rejects_missing_columns(self):
        with self.assertRaisesRegex(ValueError, "reorder_level"):
            parse_inventory_csv("sku,name,quantity\nA1,Notebook,3\n")

    def test_approval_requires_payload(self):
        approval = create_approval(
            ApprovalAction.SAVE_DRAFT,
            "Save proposal draft",
            {"kind": "proposal", "title": "Acme proposal", "content": "Hello"},
        )

        self.assertEqual(approval.action, ApprovalAction.SAVE_DRAFT)
        self.assertTrue(approval.request_id)

    def test_database_saves_only_valid_drafts(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        initialize(conn)

        draft_id = save_draft(conn, Draft(kind="email", title="Acme email", content="Hi"))

        self.assertEqual(draft_id, 1)
        self.assertEqual(list_drafts(conn)[0]["title"], "Acme email")
        with self.assertRaises(ValueError):
            save_draft(conn, Draft(kind="", title="", content=""))


if __name__ == "__main__":
    unittest.main()