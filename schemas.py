from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class PaymentTypeEnum(str, Enum):
   CHECK = "Check"
   CASH = "Cash"
   CREDIT_CARD = "Credit Card"
   DONOR_ADVISED_FUND = "Donor Advised Fund"
   NATIONAL_PAYMENTS = "National Payments"
   OTHER = "Other"

class CarrierEnum(str, Enum):
   USPS = "USPS"
   UPS = "UPS"
   FEDEX = "FedEx"
   HAND_DELIVERY = "Hand Delivery"
   UNKNOWN = "Unknown"

class ReportLineItem(BaseModel):
   reference_id: Optional[str] = Field(None, description="Bidder or donor reference ID (e.g., P-00JT-TKC)")
   bidder_name: Optional[str] = Field(None, description="Name of the donor or bidder")
   transaction_date: Optional[str] = Field(None, description="Date of payment entry")
   payment_type: Optional[PaymentTypeEnum] = Field(None, description="Payment classification")
   check_or_card_info: Optional[str] = Field(None, description="Check number or card details")
   amount: float = Field(0.0, description="Line item amount")
   
class ReportDetail(BaseModel):
   report_title: str = Field(..., description="Title of report")
   report_date: Optional[str] = Field(None, description="Date printed on report")
   total_amount_reported: Optional[float] = Field(None, description="Total dollar amount printed on report")
   line_items: List[ReportLineItem] = Field(default_factory=list)

class CheckDetail(BaseModel):
   check_number: Optional[str] = Field(None, description="Check serial number")
   check_date: Optional[str] = Field(None, description="Date on check")
   payer_name: Optional[str] = Field(None, description="Payer/Account holder name")
   payee_name: Optional[str] = Field(None, description="Payee name")
   amount_numeric: float = Field(0.0, description="Numerical check amount")
   amount_in_words: Optional[str] = Field(None, description="Written dollar line")
   bank_name: Optional[str] = Field(None, description="Bank institution name")
   memo: Optional[str] = Field(None, description="Check memo field")
   is_void: bool = Field(False, description="Flagged true if check is void")
   page_number: int = Field(..., description="PDF page number containing check")

class CashDetail(BaseModel):
   cash_total_amount: float = Field(0.0, description="Total cash collected")
   handwritten_transcript: Optional[str] = Field(None, description="Transcript of handwritten notes")
   event_name: Optional[str] = Field(None, description="Associated event name")
   page_number: int = Field(..., description="PDF page number containing cash record")

class LetterDetail(BaseModel):
   letter_date: Optional[str] = Field(None, description="Date on cover letter")
   sender_organization: Optional[str] = Field(None, description="Sender organization")
   author_name: Optional[str] = Field(None, description="Signer name")
   subject_line: Optional[str] = Field(None, description="Subject/Re header")
   stated_total_amount: Optional[float] = Field(None, description="Stated total amount in letter")
   receipt_email: Optional[str] = Field(None, description="Email for receipting")
   full_text_markdown: Optional[str] = Field(None, description="Extracted letter text")

class MailerPackage(BaseModel):
   carrier: CarrierEnum = Field(CarrierEnum.UNKNOWN, description="Carrier name")
   tracking_number: Optional[str] = Field(None, description="Carrier tracking number")
   sender_name: Optional[str] = Field(None, description="Sender or staff name")
   recipient_attention: Optional[str] = Field(None, description="ATTN recipient field")
   stated_item_count: Optional[int] = Field(None, description="Declared piece count")
   cover_letter: Optional[LetterDetail] = Field(None, description="Cover letter details")
   donor_notes: List[str] = Field(default_factory=list, description="Transcripts of handwritten notes, letters, or memos")
   cash_records: List[CashDetail] = Field(default_factory=list)
   checks: List[CheckDetail] = Field(default_factory=list)
   supporting_reports: List[ReportDetail] = Field(default_factory=list)
   page_range: List[int] = Field(default_factory=list, description="Pages covered by package")     

class BatchTray(BaseModel):
   tray_id: str = Field(..., description="Tray ID barcode number")
   tray_count: int = Field(1, description="Tray sequence count")
   cage_date: Optional[str] = Field(None, description="Cage date")
   sys_date: Optional[str] = Field(None, description="System date")
   client_name: Optional[str] = Field(None, description="Client name")
   client_id: Optional[str] = Field(None, description="Client ID")
   project_code: Optional[str] = Field(None, description="Project code")
   project_name: Optional[str] = Field(None, description="Project name")
   mailers: List[MailerPackage] = Field(default_factory=list)

class DocumentExtractionResponse(BaseModel):
   filename: str = Field(..., description="Original input PDF file name")
   total_pages_processed: int = Field(..., description="Total PDF page count")
   total_batch_count: int = Field(0, description="Total trays identified")
   total_check_count: int = Field(0, description="Total checks extracted")
   grand_total_check_amount: float = Field(0.0, description="Sum of all checks")
   grand_total_cash_amount: float = Field(0.0, description="Sum of all cash entries")
   has_reconciliation_mismatch: bool = Field(False, description="Flagged if letter total != check sum")
   needs_human_review: bool = Field(False, description="Flagged if low confidence or missing data")
   batches: List[BatchTray] = Field(default_factory=list)

  
 