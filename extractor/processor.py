import os
import io
import time
import tempfile

from extractor.pdf_extractor import PDFExtractor
from extractor.docx_extractor import DOCXExtractor
from extractor.validator import TextValidator
from extractor.pdf_to_image import PDFToImage


class ResumeProcessor:

    def __init__(self, doc_extractor, azure_ocr, ocr_worker):

        self.doc_extractor = doc_extractor
        self.azure_ocr = azure_ocr
        self.ocr_worker = ocr_worker

    # =========================================
    # COM RETRY HELPER
    #
    # Word COM can reject calls if it is busy
    # or not fully released from previous use.
    # Retry with delay solves RPC_E_CALL_REJECTED
    # =========================================

    def _com_retry(self, fn, retries=3, delay=3):

        last_error = None

        for attempt in range(1, retries + 1):

            try:

                return fn()

            except Exception as e:

                last_error = e

                print(
                    f"[COM RETRY] Attempt {attempt}/{retries} "
                    f"failed: {e}"
                )

                if attempt < retries:

                    print(f"[COM RETRY] Waiting {delay}s...")
                    time.sleep(delay)

        raise last_error

    # =========================================
    # KILL LEFTOVER WORD PROCESSES
    #
    # Zombie Word.exe blocks new COM instances.
    # Kill them before retrying.
    # =========================================

    def _kill_word_processes(self):

        try:

            os.system(
                "taskkill /f /im WINWORD.EXE >nul 2>&1"
            )

            time.sleep(2)

            print("[COM] Killed leftover Word processes")

        except Exception as e:

            print(f"[COM] Could not kill Word: {e}")

    # =========================================
    # DOCX → PDF  (with retry)
    # =========================================

    def convert_docx_to_pdf(self, path):

        def _attempt():

            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()

            word = None
            doc = None

            try:

                word = win32com.client.DispatchEx(
                    "Word.Application"
                )

                word.Visible = False
                word.DisplayAlerts = 0

                abs_path = os.path.abspath(path)

                doc = word.Documents.Open(
                    abs_path,
                    ReadOnly=True,
                    ConfirmConversions=False
                )

                # Give Word time to fully load document
                time.sleep(1)

                pdf_path = tempfile.mktemp(suffix=".pdf")

                # 17 = wdFormatPDF
                doc.SaveAs(pdf_path, FileFormat=17)

                # Give Word time to finish writing
                time.sleep(1)

                return pdf_path

            except Exception as e:

                raise

            finally:

                try:
                    if doc:
                        doc.Close(False)
                except:
                    pass

                try:
                    if word:
                        word.Quit()
                except:
                    pass

                # Give Word time to fully release COM
                time.sleep(1)

                pythoncom.CoUninitialize()

        try:

            return self._com_retry(_attempt, retries=3, delay=3)

        except Exception as e:

            # Last resort: kill zombie Word and try once more
            print("[COM] All retries failed. Killing Word and retrying...")

            self._kill_word_processes()

            return _attempt()

    # =========================================
    # DOC → PDF  (with retry)
    # =========================================

    def convert_doc_to_pdf(self, path):

        def _attempt():

            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()

            word = None
            doc = None

            try:

                word = win32com.client.DispatchEx(
                    "Word.Application"
                )

                word.Visible = False
                word.DisplayAlerts = 0

                abs_path = os.path.abspath(path)

                doc = word.Documents.Open(
                    abs_path,
                    ReadOnly=True
                )

                # Give Word time to fully load document
                time.sleep(1)

                pdf_path = tempfile.mktemp(suffix=".pdf")

                # 17 = wdFormatPDF
                doc.SaveAs(pdf_path, FileFormat=17)

                # Give Word time to finish writing
                time.sleep(1)

                return pdf_path

            except Exception as e:

                raise

            finally:

                try:
                    if doc:
                        doc.Close(False)
                except:
                    pass

                try:
                    if word:
                        word.Quit()
                except:
                    pass

                # Give Word time to fully release COM
                time.sleep(1)

                pythoncom.CoUninitialize()

        try:

            return self._com_retry(_attempt, retries=3, delay=3)

        except Exception as e:

            print("[COM] All retries failed. Killing Word and retrying...")

            self._kill_word_processes()

            return _attempt()

    # =========================================
    # MAIN PROCESS
    # =========================================

    def process(self, file_path):

        ext = os.path.splitext(file_path)[1].lower()

        extracted_text = ""

        # =========================================
        # STEP 1 — NATIVE EXTRACTION
        # =========================================

        try:

            if ext == ".pdf":

                extracted_text = PDFExtractor.extract_text(
                    file_path
                )

            elif ext == ".docx":

                extracted_text = DOCXExtractor.extract_text(
                    file_path
                )

            elif ext == ".doc":

                extracted_text = self.doc_extractor.extract_text(
                    file_path
                )

            else:

                return {
                    "status": "failed",
                    "text": "",
                    "reason": f"Unsupported file type: {ext}",
                    "stage": "native_extraction"
                }

        except Exception as e:

            return {
                "status": "failed",
                "text": "",
                "reason": str(e),
                "stage": "native_extraction"
            }

        # =========================================
        # STEP 2 — VALIDATE NATIVE TEXT
        # =========================================

        if TextValidator.is_text_good(extracted_text):

            print(f"Native text OK: {file_path}")

            return {
                "status": "native_text",
                "text": extracted_text
            }

        # =========================================
        # STEP 3 — OCR FALLBACK
        # =========================================

        print(f"OCR fallback triggered: {file_path}")

        ocr_text = ""

        try:

            # =========================================
            # STEP 3a — CONVERT TO PDF
            # =========================================

            if ext == ".pdf":

                pdf_path = file_path

            elif ext == ".docx":

                pdf_path = self.convert_docx_to_pdf(
                    file_path
                )

            elif ext == ".doc":

                pdf_path = self.convert_doc_to_pdf(
                    file_path
                )

            else:

                return {
                    "status": "failed",
                    "text": extracted_text,
                    "reason": "Unsupported OCR file type",
                    "stage": "ocr_conversion"
                }

            # =========================================
            # STEP 3b — PDF → IMAGES
            # =========================================

            images = PDFToImage.convert(pdf_path)

            if not images:

                return {
                    "status": "failed",
                    "text": extracted_text,
                    "reason": "No images generated from PDF",
                    "stage": "pdf_to_image"
                }

            print(f"Pages to OCR: {len(images)}")

            # =========================================
            # STEP 3c — OCR EACH PAGE
            # =========================================

            for page_num, img in enumerate(images, start=1):

                print(f"  OCR page {page_num}/{len(images)}")

                image_stream = io.BytesIO(img)

                result_holder = []

                self.ocr_worker.submit(
                    image_stream,
                    result_holder
                )

                page_text = result_holder[0] if result_holder else ""

                ocr_text += page_text + "\n\n"

        except Exception as e:

            print(f"[ERROR] OCR fallback failed: {e}")

            return {
                "status": "failed",
                "text": extracted_text,
                "reason": str(e),
                "stage": "ocr_fallback"
            }

        # =========================================
        # STEP 4 — VALIDATE OCR TEXT
        # =========================================

        ocr_text = ocr_text.strip()

        if TextValidator.is_text_good(ocr_text):

            return {
                "status": "ocr_text",
                "text": ocr_text
            }

        # =========================================
        # STEP 5 — FINAL FAIL
        # =========================================

        return {
            "status": "failed",
            "text": ocr_text,
            "reason": "OCR text failed validation",
            "stage": "ocr_validation"
        }