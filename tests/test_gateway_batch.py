import importlib
import unittest
from unittest.mock import patch

gateway_module = importlib.import_module("152.app.api.gateway")
_process_single_pdf = gateway_module._process_single_pdf


class GatewayBatchProcessingTests(unittest.IsolatedAsyncioTestCase):
    async def test_process_single_pdf_reports_empty_model_error_body(self):
        class FakeFile:
            filename = "sample.pdf"

            async def read(self):
                return b"%PDF-1.4"

        class FakeResponse:
            status_code = 500
            text = ""

        class FakeAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

            async def post(self, *args, **kwargs):
                return FakeResponse()

        with patch.object(gateway_module.httpx, "AsyncClient", return_value=FakeAsyncClient()):
            result, error = await _process_single_pdf(FakeFile())

        self.assertIsNone(result)
        self.assertIn("sample.pdf", error)
        self.assertIn("HTTP 500", error)
        self.assertNotEqual(error, "sample.pdf: ")


if __name__ == "__main__":
    unittest.main()
