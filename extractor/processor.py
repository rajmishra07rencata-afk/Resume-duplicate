import os
import io
import time

from extractor.pdf_extractor import PDFExtractor
from extractor.docx_extractor import DOCXExtractor
from extractor.validator import TextValidator
from extractor.pdf_to_image import PDFToImage


class ResumeProcessor:

    def __init__(self, doc_extractor, azure_ocr, ocr_worker):

        self.doc_extractor = doc_extractor
        self.azure_ocr = azure_ocr
        self.ocr_worker = ocr_worker

    def process(self, file_path):

        ext = os.path.splitext(file_path)[1].lower()

        extracted_text = ""

        # =========================
        # NATIVE EXTRACTION
        # =========================

        if ext == ".pdf":
            extracted_text = PDFExtractor.extract_text(file_path)

        elif ext == ".docx":
            extracted_text = DOCXExtractor.extract_text(file_path)

        elif ext == ".doc":
            extracted_text = self.doc_extractor.extract_text(file_path)

        else:
            return {
                "status": "unsupported",
                "text": ""
            }

        # =========================
        # VALIDATION
        # =========================

        if TextValidator.is_text_good(extracted_text):

            return {
                "status": "native_text",
                "text": extracted_text
            }

        # =========================
        # OCR FALLBACK (CONTROLLED QUEUE)
        # =========================

        print("Running Azure OCR fallback...")

        ocr_text = ""

        if ext == ".pdf":

            images = PDFToImage.convert(file_path)

            for img in images:

                image_stream = io.BytesIO(img)

                # 🔥 QUEUE BASED OCR (NO DIRECT AZURE CALL)
                result_holder = []

                self.ocr_worker.submit(image_stream, result_holder)

                while not result_holder:
                    time.sleep(0.05)

                ocr_text += result_holder[0] + "\n\n"

            return {
                "status": "ocr_text",
                "text": ocr_text.strip()
            }

        return {
            "status": "ocr_required",
            "text": extracted_text
        }