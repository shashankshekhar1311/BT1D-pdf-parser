import pymupdf  # PyMuPDF
import re
import json
import torch
from io import BytesIO
from PIL import Image
from typing import List, Tuple, Dict, Any
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
from qwen_vl_utils import process_vision_info
from schemas import (
   DocumentExtractionResponse, BatchTray, MailerPackage, CheckDetail, CashDetail, LetterDetail, ReportDetail, ReportLineItem, CarrierEnum
)

class PDFBatchExtractor:
    def __init__(self):
        print("Loading 4-Bit Quantized Qwen2.5-VL-7B Vision Model onto GPU...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2.5-VL-7B-Instruct",
            quantization_config=bnb_config,
            device_map="auto"
        )
        min_pixels = 256 * 28 * 28
        max_pixels = 1024 * 28 * 28
        self.processor = AutoProcessor.from_pretrained(
            "Qwen/Qwen2.5-VL-7B-Instruct",
            min_pixels=min_pixels,
            max_pixels=max_pixels
        )
        print("Vision-LLM loaded successfully (~5 GB VRAM used)!\n")
        self.re_tray_id = re.compile(r'Tray\s*ID[:\s]*(\d+)', re.IGNORECASE)
        self.re_client_id = re.compile(r'Client\s*ID[:\s]*(\d+)', re.IGNORECASE)
        self.re_project = re.compile(r'Project[:\s]*(\d+)\s*(.*)', re.IGNORECASE)
        self.re_ups_tracking = re.compile(r'1Z[A-Z0-9]{16}', re.IGNORECASE)
        self.re_usps_tracking = re.compile(r'9\d{21}', re.IGNORECASE)
    def page_to_image(self, page, dpi: int = 150) -> Image.Image:
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        return Image.open(BytesIO(img_bytes))
    def _parse_float(self, val: Any) -> float:
        """Safely parses float numeric values from raw or string JSON inputs."""
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        s_val = str(val).strip().lower()
        if s_val in ["null", "none", "", "nan", "undefined"]:
            return 0.0
        s_clean = re.sub(r"[^\d.-]", "", s_val)
        try:
            return float(s_clean) if s_clean else 0.0
        except ValueError:
            return 0.0
    def _parse_bool(self, val: Any) -> bool:
        """Safely parses boolean flags from raw or string JSON inputs."""
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        s_val = str(val).strip().lower()
        return s_val in ["true", "1", "yes"]
    def _clean_str(self, val: Any, default: Any = None) -> Any:
        """Cleans literal 'null' strings returned by LLM into Python None or defaults."""
        if val is None:
            return default
        s_val = str(val).strip()
        if s_val.lower() in ["null", "none", "undefined", ""]:
            return default
        return s_val
    def analyze_page_with_vision(self, pil_image: Image.Image, page_num: int) -> Dict[str, Any]:
        prompt = """
        Analyze this document page in detail and respond in valid JSON.
        --- CHECK NUMBER EXTRACTION RULES ---
        1. Look at the top-right corner or MICR line at the bottom for the check serial number.
        2. On personal checks (e.g. Navy Federal, Moody Bank), check number is a short integer like '200', '1049', '1371', '1121'.
        3. On DAF or Bill-Pay checks (DAFgiving360, PNC, TopLine), check number is a 7-10 digit serial like '0005708913', '0005706426', '0000007825'.
        4. CRITICAL DISAMBIGUATION: NEVER extract fractional numbers containing slashes or dashes like '68-7497/2560', '760/312', '7469/2910', or '70-2328/0719'. These are ABA routing fractions, NOT check numbers. If both exist in top-right, ALWAYS pick the integer (e.g., '200').
        --- PAGE CONTENTS RULES ---
        A page can contain BOTH a letter/grant text at top AND a negotiable check at the bottom (e.g., DAFgiving360 pages 53, 58, 63, 73, 78).
        Return JSON format:
        {
            "has_check": boolean (true if ANY bank check or check voucher is visible),
            "check_data": {
                "check_number": "STRING (e.g. '200' or '0005708913'. NO FRACTIONS)",
                "check_date": "MM/DD/YYYY or null",
                "payer_name": "Full name of payer or donor",
                "payee_name": "Entity check is written to e.g. Breakthrough T1D",
                "amount_numeric": float (e.g. 25.0 or 500.0),
                "bank_name": "Bank institution name e.g. Navy Federal Credit Union, Bank of America",
                "memo": "Memo line text or null",
                "is_void": boolean
            },
            "has_letter_or_note": boolean (true if letter text, grant transmittal, or handwritten notes exist),
            "letter_data": {
                "donor_acknowledgment": "Donor name(s) or null",
                "grant_designation": "Grant purpose or null",
                "full_text_markdown": "Full text transcript of letter or note"
            }
        }
        Return ONLY raw JSON, with no markdown formatting.
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        text_prompt = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, _ = process_vision_info(messages)
        inputs = self.processor(
            text=[text_prompt],
            images=image_inputs,
            padding=True,
            return_tensors="pt"
        ).to("cuda")
        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=512)
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            response_text = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
        torch.cuda.empty_cache()
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except Exception as e:
                print(f" [JSON Parse Error P{page_num}: {e}]", end="")
        return {"has_check": False, "has_letter_or_note": False}
   
    def process_pdf(self, pdf_path: str) -> DocumentExtractionResponse:
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        batches: List[BatchTray] = []
        current_tray: BatchTray = None
        current_mailer: MailerPackage = None
        total_checks = 0
        grand_check_sum = 0.0
        print(f"Starting Extraction for {total_pages} Pages...\n")
        for page_num in range(1, total_pages + 1):
            page = doc[page_num - 1]
            text = page.get_text("text").strip()
            text_upper = text.upper()
            # 1. Batch Tray Separator
            if "SEPARATING PAGE" in text_upper or "TRAY ID:" in text_upper:
                print(f"[Page {page_num}/{total_pages}] Found Batch Separator Page.")
                tray_metadata = self._parse_tray_page(text)
                current_tray = BatchTray(
                    tray_id=tray_metadata.get("tray_id", f"TRAY-{page_num}"),
                    cage_date=tray_metadata.get("cage_date"),
                    sys_date=tray_metadata.get("sys_date"),
                    client_name="JDRF - Juvenile Diabetes Research Foundation",
                    client_id=tray_metadata.get("client_id", "0688"),
                    project_code=tray_metadata.get("project_code", ""),
                    project_name=tray_metadata.get("project_name", ""),
                    mailers=[]
                )
                batches.append(current_tray)
                current_mailer = None
                continue
            if current_tray is None:
                current_tray = BatchTray(
                    tray_id="TRAY-DEFAULT-001",
                    client_name="JDRF",
                    client_id="0688",
                    project_code="GENERAL",
                    project_name="General Batch",
                    mailers=[]
                )
                batches.append(current_tray)
            # 2. Package / Shipping Label Boundary
            ups_match = self.re_ups_tracking.search(text)
            usps_match = self.re_usps_tracking.search(text)
            if ups_match or usps_match or "SHIP TO:" in text_upper:
                print(f"[Page {page_num}/{total_pages}] Found Courier/Package Boundary.")
                current_mailer = MailerPackage(
                    carrier=CarrierEnum.UPS if ups_match else CarrierEnum.USPS,
                    tracking_number=ups_match.group(0) if ups_match else (usps_match.group(0) if usps_match else None),
                    page_range=[page_num]
                )
                current_tray.mailers.append(current_mailer)
                continue
            if current_mailer is None:
                current_mailer = MailerPackage(carrier=CarrierEnum.UNKNOWN, page_range=[page_num])
                current_tray.mailers.append(current_mailer)
            else:
                current_mailer.page_range.append(page_num)
            # 3. Vision-LLM Evaluation
            if self._should_evaluate_page(page, text_upper):
                print(f"[Page {page_num}/{total_pages}] Running Vision-LLM Analysis...", end="", flush=True)
                page_img = self.page_to_image(page)
                vision_data = self.analyze_page_with_vision(page_img, page_num)
                # Process Check portion if present
                if vision_data.get("has_check") is True and vision_data.get("check_data"):
                    c_data = vision_data["check_data"]
                    raw_chk_num = self._clean_str(c_data.get("check_number"))
                    if raw_chk_num and "/" in raw_chk_num:
                        raw_chk_num = raw_chk_num.split("/")[0].split("-")[0].strip()
                    parsed_amt = self._parse_float(c_data.get("amount_numeric"))
                    check_detail = CheckDetail(
                        check_number=raw_chk_num,
                        check_date=self._clean_str(c_data.get("check_date")),
                        payer_name=self._clean_str(c_data.get("payer_name"), "Unknown Payer"),
                        payee_name=self._clean_str(c_data.get("payee_name"), "Breakthrough T1D"),
                        amount_numeric=parsed_amt,
                        bank_name=self._clean_str(c_data.get("bank_name"), "Unknown Bank"),
                        memo=self._clean_str(c_data.get("memo")),
                        is_void=self._parse_bool(c_data.get("is_void")),
                        page_number=page_num
                    )
                    current_mailer.checks.append(check_detail)
                    total_checks += 1
                    grand_check_sum += parsed_amt
                    print(f" -> Check Captured (${parsed_amt:,.2f}, Check #{check_detail.check_number})", end="")
                # Process Letter/Note portion if present
                if vision_data.get("has_letter_or_note") is True and vision_data.get("letter_data"):
                    l_data = vision_data["letter_data"]
                    text_content = self._clean_str(l_data.get("full_text_markdown"), "")
                    donor_ack = self._clean_str(l_data.get("donor_acknowledgment"))
                    grant_des = self._clean_str(l_data.get("grant_designation"))
                    if donor_ack:
                        text_content = f"Donor: {donor_ack}\nDesignation: {grant_des or ''}\n\n" + text_content
                    if text_content:
                        current_mailer.donor_notes.append(text_content)
                    if current_mailer.cover_letter is None and (text_content or donor_ack):
                        current_mailer.cover_letter = LetterDetail(
                            author_name=donor_ack,
                            full_text_markdown=text_content
                        )
                    print(f" -> Letter/Grant Details Captured", end="")
                print()
        return DocumentExtractionResponse(
            filename=pdf_path.split("\\")[-1],
            total_pages_processed=total_pages,
            total_batch_count=len(batches),
            total_check_count=total_checks,
            grand_total_check_amount=round(grand_check_sum, 2),
            batches=batches
        )
    def _should_evaluate_page(self, page, text_upper: str) -> bool:
        is_known_non_check = "SEPARATING PAGE" in text_upper or "SHIP TO:" in text_upper or "PAY-01:" in text_upper
        if is_known_non_check:
            return False
        has_images = len(page.get_images()) > 0
        has_text = len(text_upper) > 10
        return has_images or has_text
    def _parse_tray_page(self, text: str) -> Dict[str, Any]:
        data = {}
        t_match = self.re_tray_id.search(text)
        if t_match:
            data["tray_id"] = t_match.group(1)
        c_match = self.re_client_id.search(text)
        if c_match:
            data["client_id"] = c_match.group(1)
        p_match = self.re_project.search(text)
        if p_match:
            data["project_code"] = p_match.group(1)
            data["project_name"] = p_match.group(2).strip()
        return data