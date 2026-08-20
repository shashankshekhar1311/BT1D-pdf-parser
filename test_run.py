import json
from extractor import PDFBatchExtractor

if __name__ == "__main__":
    pdf_file_path = "D:\\\pdf_parser\input\\BT1D_010226_A001.pdf"  # Place sample PDF here
    extractor = PDFBatchExtractor()
    print(f"Processing PDF: {pdf_file_path}...")
    result = extractor.process_pdf(pdf_file_path)

    # Save formatted JSON output to disk
    output_json_path = "D:\\pdf_parser\\output\\output_extraction.json"

    with open(output_json_path, "w") as f:
        f.write(json.dumps(result.model_dump(), indent=2))

    print(f"\nExtraction completed successfully!")
    print(f"Total Trays Found: {result.total_batch_count}")
    print(f"Total Checks Extracted: {result.total_check_count}")
    print(f"Grand Check Total Amount: ${result.grand_total_check_amount:,.2f}")
    print(f"JSON Output Saved To: {output_json_path}")
 