import pymupdf  # PyMuPDF
import re
import json
import torch
from io import BytesIO
from PIL import Image
from typing import List, Tuple, Dict, Any, Optional

from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
from qwen_vl_utils import process_vision_info

from schemas import (
    DocumentExtractionResponse, BatchTray, MailerPackage,
    CheckDetail, CashDetail, LetterDetail, ReportDetail,
    ReportLineItem, CarrierEnum
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
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        s_val = str(val).strip().lower()
        return s_val in ["true", "1", "yes"]

    def _clean_str(self, val: Any, default: Any = None) -> Any:
        if val is None:
            return default
        s_val = str(val).strip()
        if s_val.lower() in ["null", "none", "undefined", "", "x", "1234567890", "n/a", "unknown"]:
            return default
        return s_val

    def _clean_check_number(self, val: Any) -> Optional[str]:
        """
        Safely extracts check numbers while filtering out ABA transit fractions 
        (e.g., '68-7497/2560' or '70-2328/0719').
        """
        if val is None:
            return None
        s_val = str(val).strip()
        if s_val.lower() in ["null", "none", "undefined", "", "x", "1234567890", "n/a", "unknown"]:
            return None

        # 1. Remove standard ABA transit fractions (XX-XXXX/XXXX)
        s_clean = re.sub(r'\b\d{1,4}-\d{1,5}/\d{1,5}\b', '', s_val).strip()
        
        # 2. Remove simple fractional patterns (XXXX/XXXX)
        s_clean = re.sub(r'\b\d{1,4}/\d{1,5}\b', '', s_clean).strip()

        # 3. Discard placeholder blacklist values
        if not s_clean or s_clean.lower() in ["null", "none", "x"] or s_clean in ["21741-502121", "903683424", "903683425", "903621306"]:
            return None

        # 4. Extract remaining valid alphanumeric token if multiple items exist
        tokens = [t for t in s_clean.split() if t.isalnum()]
        if tokens:
            return tokens[0]
        return s_clean

    def _repair_and_parse_json(self, response_text: str) -> Dict[str, Any]:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            return {"has_check": False, "has_letter": False}

        raw_str = json_match.group(0)

        try:
            return json.loads(raw_str)
        except Exception:
            pass

        try:
            cleaned = re.sub(r'(?<=: ")(.*?)(?=",\n|"\n|\"\s*\})', lambda m: m.group(1).replace('\n', '\\n').replace('"', '\\"'), raw_str, flags=re.DOTALL)
            return json.loads(cleaned)
        except Exception:
            pass

        result = {}
        result["has_check"] = "true" in raw_str.lower().split("has_check")[1][:15] if "has_check" in raw_str else False
        result["has_letter"] = "true" in raw_str.lower().split("has_letter")[1][:15] if "has_letter" in raw_str else False

        chk_num = re.search(r'"check_number"\s*:\s*"([^"]+)"', raw_str)
        amt = re.search(r'"amount_numeric"\s*:\s*([\d.]+)', raw_str)
        payer = re.search(r'"payer_name"\s*:\s*"([^"]+)"', raw_str)
        bank = re.search(r'"bank_name"\s*:\s*"([^"]+)"', raw_str)
        dt = re.search(r'"check_date"\s*:\s*"([^"]+)"', raw_str)

        result["check_number"] = chk_num.group(1) if chk_num else None
        result["amount_numeric"] = float(amt.group(1)) if amt else 0.0
        result["payer_name"] = payer.group(1) if payer else None
        result["bank_name"] = bank.group(1) if bank else None
        result["check_date"] = dt.group(1) if dt else None

        return result

    def analyze_page_with_vision(self, pil_image: Image.Image, page_num: int) -> Dict[str, Any]:
        prompt = """
        Analyze this document page and return a JSON object.

        --- CHECK EXTRACTION RULES ---
        A page contains a check if a physical check, check voucher, or check stub is present with dollar amounts ($), 'Pay to the Order of', or MICR line.
        1. "has_check": true IF AND ONLY IF a negotiable check or check voucher is visible.
        2. "amount_numeric": Extract the exact numerical dollar amount (e.g., 25000.00, 1000.00, 500.00). NEVER set 0.0 if a positive dollar check amount is visible.
        3. "check_number": Extract the serial check number (usually top-right corner or MICR line). CRITICAL: Do NOT extract ABA transit fractions (numbers formatted with slashes or dashes like XX-XXXX/XXXX). Return only the true check number string or null.

        --- LETTER EXTRACTION RULES ---
        1. "has_letter": true ONLY if actual donor letter text, grant transmittal message, or handwritten note is present. Set false for blank forms, simple envelopes, or pure check stubs.
        2. "donor_name": Donor/author name or null.
        3. "grant_designation": Designation or null.
        4. "letter_summary": Concise 1-2 sentence summary of letter text or null.

        Return ONLY raw JSON in this exact structure:
        {
            "has_check": boolean,
            "check_number": "string or null",
            "check_date": "MM/DD/YYYY or null",
            "payer_name": "string or null",
            "payee_name": "string or null",
            "amount_numeric": float,
            "bank_name": "string or null",
            "memo": "string or null",
            "is_void": boolean,
            "has_letter": boolean,
            "donor_name": "string or null",
            "grant_designation": "string or null",
            "letter_summary": "string or null"
        }
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
            generated_ids = self.model.generate(
                **inputs, 
                max_new_tokens=384,
                do_sample=False  # Deterministic decoding
            )
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            response_text = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]

        torch.cuda.empty_cache()
        return self._repair_and_parse_json(response_text)

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

                has_chk = self._parse_bool(vision_data.get("has_check"))
                parsed_amt = self._parse_float(vision_data.get("amount_numeric"))
                is_void = self._parse_bool(vision_data.get("is_void"))
                
                # Apply robust check number cleaner
                clean_chk_num = self._clean_check_number(vision_data.get("check_number"))

                # CHECK CAPTURE RULE: Valid positive amount OR void check
                if has_chk and (parsed_amt > 0.0 or is_void):
                    check_detail = CheckDetail(
                        check_number=clean_chk_num,
                        check_date=self._clean_str(vision_data.get("check_date")),
                        payer_name=self._clean_str(vision_data.get("payer_name"), "Unknown Payer"),
                        payee_name=self._clean_str(vision_data.get("payee_name"), "Breakthrough T1D"),
                        amount_numeric=parsed_amt,
                        bank_name=self._clean_str(vision_data.get("bank_name"), "Unknown Bank"),
                        memo=self._clean_str(vision_data.get("memo")),
                        is_void=is_void,
                        page_number=page_num
                    )
                    current_mailer.checks.append(check_detail)
                    total_checks += 1
                    grand_check_sum += parsed_amt
                    print(f" -> Check Captured (${parsed_amt:,.2f}, Check #{check_detail.check_number})", end="")

                # LETTER CAPTURE RULE: Requires explicit flag AND non-empty content
                has_ltr = self._parse_bool(vision_data.get("has_letter"))
                donor_name = self._clean_str(vision_data.get("donor_name"))
                grant_des = self._clean_str(vision_data.get("grant_designation"))
                ltr_summary = self._clean_str(vision_data.get("letter_summary"))

                if has_ltr and (ltr_summary or donor_name or grant_des):
                    note_parts = []
                    if donor_name:
                        note_parts.append(f"Donor: {donor_name}")
                    if grant_des:
                        note_parts.append(f"Designation: {grant_des}")
                    if ltr_summary:
                        note_parts.append(f"Summary: {ltr_summary}")

                    if note_parts:
                        full_note = "\n".join(note_parts)
                        current_mailer.donor_notes.append(full_note)

                        if current_mailer.cover_letter is None:
                            current_mailer.cover_letter = LetterDetail(
                                author_name=donor_name,
                                full_text_markdown=full_note
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