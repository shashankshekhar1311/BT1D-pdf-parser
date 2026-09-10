import unittest

from extractor import PDFBatchExtractor
from lookup_service import resolve_lookup_workbook_path
from schemas import DocumentExtractionResponse, BatchTray, MailerPackage, CheckDetail


class LookupMatchingTests(unittest.TestCase):
    def setUp(self):
        self.extractor = PDFBatchExtractor.__new__(PDFBatchExtractor)
        self.extractor.lookup_workbook_path = str(resolve_lookup_workbook_path())
        self.extractor.lookup_tables = self.extractor._load_lookup_tables()

    def test_lookup_text_normalization_and_keyword_matching(self):
        text = "A DAFgiving 360 gift with Fund-a-Cure event support"

        normalized = self.extractor._normalize_lookup_text(text)
        self.assertIn("dafgiving", normalized)
        self.assertIn("fund a cure", normalized)

        self.assertEqual(
            self.extractor._match_lookup_by_keywords(
                text,
                [
                    {"PaymentMethod": "Donor Advised Fund", "PaymentMethodKeywords": "DAFgiving 360"},
                    {"Restrictions": "Fund-a-Cure", "Reasons": "Fund-a-Cure event/non-event gifts get a FAC retriction"},
                ],
                key_field="PaymentMethod",
                keyword_field="PaymentMethodKeywords",
            ),
            "Donor Advised Fund",
        )

    def test_dafgiving360_compact_alias_match(self):
        text = "Summary: This is an envelope from DAFgiving360 indicating a grant has been enclosed."
        match = self.extractor._match_lookup_by_keywords(
            text,
            [{"PaymentMethod": "Donor Advised Fund", "PaymentMethodKeywords": "DAFgiving 360"}],
            key_field="PaymentMethod",
            keyword_field="PaymentMethodKeywords",
        )
        self.assertEqual(match, "Donor Advised Fund")

    def test_first_relevant_note_wins_before_memo(self):
        response = DocumentExtractionResponse(
            filename="sample.pdf",
            total_pages_processed=1,
            batches=[
                BatchTray(
                    tray_id="TRAY-01",
                    mailers=[
                        MailerPackage(
                            donor_notes=[
                                "Fidelity Charitable gift support.",
                                "This is an envelope from DAFgiving360 indicating a grant has been enclosed.",
                            ],
                            checks=[
                                CheckDetail(
                                    check_number="123",
                                    memo="Donor Advised Funds (DAFs) Walk for the event.",
                                    amount_numeric=500.0,
                                    page_number=1,
                                )
                            ],
                        )
                    ],
                )
            ],
        )

        result = self.extractor._apply_lookup_rules_to_response(response)
        check = result.batches[0].mailers[0].checks[0]

        self.assertEqual(check.PaymentMethod, "Donor Advised Fund")

    def test_apply_lookup_rules_to_document(self):
        response = DocumentExtractionResponse(
            filename="sample.pdf",
            total_pages_processed=1,
            batches=[
                BatchTray(
                    tray_id="TRAY-01",
                    mailers=[
                        MailerPackage(
                            donor_notes=[
                                "This gift was made through DAFgiving 360.",
                                "Fund-a-Cure event support for this contribution.",
                            ],
                            checks=[
                                CheckDetail(
                                    check_number="123",
                                    memo="Donor Advised Funds (DAFs) Walk for the event.",
                                    amount_numeric=500.0,
                                    page_number=1,
                                )
                            ],
                        )
                    ],
                )
            ],
        )

        result = self.extractor._apply_lookup_rules_to_response(response)
        check = result.batches[0].mailers[0].checks[0]

        self.assertEqual(check.PaymentMethod, "Donor Advised Fund")
        self.assertEqual(check.restrictions, "Fund-a-Cure")
        self.assertEqual(check.entrysystem, "CRM")
        self.assertEqual(check.ReceiptType, "Do Not Receipt")

    def test_dictionary_payload_lookup_candidates_are_resolved(self):
        response = {
            "filename": "sample.pdf",
            "total_pages_processed": 1,
            "batches": [
                {
                    "tray_id": "TRAY-01",
                    "mailers": [
                        {
                            "donor_notes": [
                                "Summary: A grant envelope from DAFgiving360 addressed to an unspecified recipient.",
                                "Donor: Susan Street Whaley Charitable Fund\nDesignation: Pacific Northwest Chapter, Fund a Cure",
                            ],
                            "checks": [
                                {
                                    "check_number": "0005656097",
                                    "payer_name": "DAFgiving360",
                                    "payee_name": "BREAKTHROUGH T1D",
                                    "amount_numeric": 25000.0,
                                    "amount_in_words": "TWENTY-FIVE THOUSAND DOLLARS AND NO CENTS",
                                    "bank_name": "Bank of America",
                                    "memo": "10517633",
                                    "page_number": 89,
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        loaded = DocumentExtractionResponse.model_validate(response)
        result = self.extractor._apply_lookup_rules_to_response(loaded)
        check = result.batches[0].mailers[0].checks[0]

        self.assertEqual(check.PaymentMethod, "Donor Advised Fund")
        self.assertIsNotNone(check.lookup_debug)
        self.assertTrue(check.lookup_debug["candidate_texts"])

    def test_should_evaluate_page_keeps_donor_and_memo_signal_pages(self):
        class DummyPage:
            def get_images(self):
                return [1]

        self.assertTrue(self.extractor._should_evaluate_page(DummyPage(), "DONOR NOTE: FUND-A-CURE ENVELOPE"))
        self.assertTrue(self.extractor._should_evaluate_page(DummyPage(), "MEMO: DAFgiving360 purpose gift"))
        self.assertFalse(self.extractor._should_evaluate_page(DummyPage(), "SEPARATING PAGE"))
        self.assertFalse(self.extractor._should_evaluate_page(DummyPage(), "SHIP TO: ABC COMPANY"))


if __name__ == "__main__":
    unittest.main()
