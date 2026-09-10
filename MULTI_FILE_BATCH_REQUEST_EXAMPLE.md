# Example HTTP Request Payload for Multi-File Batch Extraction

Use this against the 152 gateway endpoint:

```http
POST http://127.0.0.1:8000/api/v1/extract-batch
Content-Type: multipart/form-data
```

Form-data fields:
- `files` : one or more PDF files

Example with cURL:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/extract-batch" \
  -F "files=@D:\pdf_parser\input\BT1D_010226_B001.pdf" \
  -F "files=@D:\pdf_parser\input\BT1D_010226_C001.pdf" \
  -F "files=@D:\pdf_parser\input\BT1D_031626_B001.pdf"
```

Example JSON response shape:
```json
{
  "filename": "combined_batch_output",
  "total_pages_processed": 520,
  "total_batch_count": 3,
  "total_check_count": 18,
  "grand_total_check_amount": 12500.0,
  "grand_total_cash_amount": 0.0,
  "results": [
    {
      "filename": "BT1D_010226_B001.pdf",
      "total_pages_processed": 120,
      "total_batch_count": 1,
      "total_check_count": 4,
      "grand_total_check_amount": 5000.0,
      "batches": []
    }
  ],
  "errors": []
}
```

Notes:
- The gateway loops through each uploaded PDF and calls the internal 148 inference service.
- Each PDF result is retained in the `results` list.
- The final payload is a combined summary plus per-file output objects.
