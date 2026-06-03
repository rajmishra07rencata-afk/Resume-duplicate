# import os
# import io
# import time
# import tempfile
# import re

# from extractor.pdf_extractor import PDFExtractor
# from extractor.docx_extractor import DOCXExtractor
# from extractor.validator import TextValidator
# from extractor.pdf_to_image import PDFToImage
# from extractor.text_cleaner import TextCleaner


# class ResumeProcessor:

#     def __init__(self, doc_extractor, azure_ocr, ocr_worker):
#         self.doc_extractor = doc_extractor
#         self.azure_ocr = azure_ocr
#         self.ocr_worker = ocr_worker

#     # =========================================
#     # COM HELPERS
#     # =========================================

#     def _com_retry(self, fn, retries=3, delay=3):
#         last_error = None
#         for attempt in range(1, retries + 1):
#             try:
#                 return fn()
#             except Exception as e:
#                 last_error = e
#                 print(f"[COM RETRY] Attempt {attempt}/{retries} failed: {e}")
#                 if attempt < retries:
#                     time.sleep(delay)
#         raise last_error

#     def _kill_word_processes(self):
#         try:
#             os.system("taskkill /f /im WINWORD.EXE >nul 2>&1")
#             time.sleep(2)
#         except:
#             pass

#     def convert_docx_to_pdf(self, path):
#         def _attempt():
#             import pythoncom
#             import win32com.client
#             pythoncom.CoInitialize()
#             word = None
#             doc = None
#             try:
#                 word = win32com.client.DispatchEx("Word.Application")
#                 word.Visible = False
#                 word.DisplayAlerts = 0
#                 abs_path = os.path.abspath(path)
#                 doc = word.Documents.Open(abs_path, ReadOnly=True, ConfirmConversions=False)
#                 time.sleep(1)
#                 pdf_path = tempfile.mktemp(suffix=".pdf")
#                 doc.SaveAs(pdf_path, FileFormat=17)
#                 time.sleep(1)
#                 return pdf_path
#             finally:
#                 try:
#                     if doc: doc.Close(False)
#                 except: pass
#                 try:
#                     if word: word.Quit()
#                 except: pass
#                 time.sleep(1)
#                 pythoncom.CoUninitialize()

#         try:
#             return self._com_retry(_attempt)
#         except:
#             self._kill_word_processes()
#             return _attempt()

#     def convert_doc_to_pdf(self, path):
#         def _attempt():
#             import pythoncom
#             import win32com.client
#             pythoncom.CoInitialize()
#             word = None
#             doc = None
#             try:
#                 word = win32com.client.DispatchEx("Word.Application")
#                 word.Visible = False
#                 word.DisplayAlerts = 0
#                 abs_path = os.path.abspath(path)
#                 doc = word.Documents.Open(abs_path, ReadOnly=True)
#                 time.sleep(1)
#                 pdf_path = tempfile.mktemp(suffix=".pdf")
#                 doc.SaveAs(pdf_path, FileFormat=17)
#                 time.sleep(1)
#                 return pdf_path
#             finally:
#                 try:
#                     if doc: doc.Close(False)
#                 except: pass
#                 try:
#                     if word: word.Quit()
#                 except: pass
#                 time.sleep(1)
#                 pythoncom.CoUninitialize()

#         try:
#             return self._com_retry(_attempt)
#         except:
#             self._kill_word_processes()
#             return _attempt()

#     # =========================================
#     # CONTACT CHECK
#     # =========================================

#     @staticmethod
#     def _has_contact_info(text):
#         if not text:
#             return False, False
#         email_re = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
#         phone_re = re.compile(r'(?:\+?\d[\s\-\.]*){10,15}')
#         has_email = bool(email_re.search(text))
#         has_phone = bool(phone_re.search(text))
#         return has_email, has_phone

#     # =========================================
#     # MAIN PROCESS
#     # =========================================

#     def process(self, file_path):
#         ext = os.path.splitext(file_path)[1].lower()

#         # STEP 1 — Scanned PDF check → skip native, go straight to OCR
#         if ext == ".pdf" and PDFExtractor.is_scanned(file_path):
#             print(f"Scanned PDF detected: {file_path}")
#             return self._run_ocr_pipeline(file_path, ext)

#         # STEP 2 — Native text extraction
#         extracted_text = ""
#         try:
#             if ext == ".pdf":
#                 extracted_text = PDFExtractor.extract_text(file_path)
#             elif ext == ".docx":
#                 extracted_text = DOCXExtractor.extract_text(file_path)
#             elif ext == ".doc":
#                 extracted_text = self.doc_extractor.extract_text(file_path)
#             else:
#                 return {
#                     "status": "failed",
#                     "text": "",
#                     "reason": f"Unsupported file type: {ext}",
#                     "stage": "native_extraction"
#                 }
#         except Exception as e:
#             return {
#                 "status": "failed",
#                 "text": "",
#                 "reason": str(e),
#                 "stage": "native_extraction"
#             }

#         # STEP 3 — Clean native text
#         clean_text = TextCleaner.clean(extracted_text)

#         # STEP 4 — Validate NATIVE text only
#         # If native is good → use it
#         if TextValidator.is_text_good(clean_text):
#             print(f"Native text OK: {file_path}")
#             return {"status": "native_text", "text": clean_text}

#         # STEP 5 — Native text failed validation → OCR fallback
#         print(f"Native text failed validation, trying OCR: {file_path}")
#         return self._run_ocr_pipeline(file_path, ext, extracted_text)

#     # =========================================
#     # OCR PIPELINE — NO VALIDATION, always use result
#     # =========================================

#     def _run_ocr_pipeline(self, file_path, ext, native_text=""):
#         print(f"OCR triggered: {file_path}")
#         ocr_text = ""

#         try:
#             if ext == ".pdf":
#                 pdf_path = file_path
#             elif ext == ".docx":
#                 pdf_path = self.convert_docx_to_pdf(file_path)
#             elif ext == ".doc":
#                 pdf_path = self.convert_doc_to_pdf(file_path)
#             else:
#                 return {
#                     "status": "failed",
#                     "text": native_text,
#                     "reason": "Unsupported OCR file type",
#                     "stage": "ocr_conversion"
#                 }

#             images = PDFToImage.convert(pdf_path)
#             if not images:
#                 return {
#                     "status": "failed",
#                     "text": native_text,
#                     "reason": "No images generated from PDF",
#                     "stage": "pdf_to_image"
#                 }

#             print(f"Pages to OCR: {len(images)}")
#             for page_num, img in enumerate(images, start=1):
#                 print(f"  OCR page {page_num}/{len(images)}")
#                 image_stream = io.BytesIO(img)
#                 result_holder = []
#                 self.ocr_worker.submit(image_stream, result_holder)
#                 page_text = result_holder[0] if result_holder else ""
#                 ocr_text += page_text + "\n\n"

#         except Exception as e:
#             print(f"[ERROR] OCR failed: {e}")
#             return {
#                 "status": "failed",
#                 "text": native_text,
#                 "reason": f"OCR error: {str(e)}",
#                 "stage": "ocr_error"
#             }

#         # STEP 6 — ALWAYS use OCR text, no validation
#         # Clean it and return
#         clean_ocr = TextCleaner.clean(ocr_text)

#         if clean_ocr.strip():
#             print(f"OCR text accepted: {len(clean_ocr)} chars")
#             return {"status": "ocr_text", "text": clean_ocr}
#         else:
#             # Only fail if OCR returned literally nothing
#             return {
#                 "status": "failed",
#                 "text": native_text,
#                 "reason": "OCR returned empty text",
#                 "stage": "ocr_empty"
#             }


import os
import io
import time
import tempfile
import re

from extractor.pdf_extractor import PDFExtractor
from extractor.docx_extractor import DOCXExtractor
from extractor.validator import TextValidator
from extractor.pdf_to_image import PDFToImage
from extractor.text_cleaner import TextCleaner


class ResumeProcessor:

    def __init__(self, doc_extractor, azure_ocr, ocr_worker):
        self.doc_extractor = doc_extractor
        self.azure_ocr = azure_ocr
        self.ocr_worker = ocr_worker

    # =========================================
    # COM HELPERS
    # =========================================

    def _com_retry(self, fn, retries=3, delay=3):
        last_error = None
        for attempt in range(1, retries + 1):
            try:
                return fn()
            except Exception as e:
                last_error = e
                print(f"[COM RETRY] Attempt {attempt}/{retries} failed: {e}")
                if attempt < retries:
                    time.sleep(delay)
        raise last_error

    def _kill_word_processes(self):
        try:
            os.system("taskkill /f /im WINWORD.EXE >nul 2>&1")
            time.sleep(2)
        except:
            pass

    def convert_docx_to_pdf(self, path):
        def _attempt():
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            word = None
            doc = None
            try:
                word = win32com.client.DispatchEx("Word.Application")
                word.Visible = False
                word.DisplayAlerts = 0
                abs_path = os.path.abspath(path)
                doc = word.Documents.Open(
                    abs_path, ReadOnly=True, ConfirmConversions=False
                )
                time.sleep(1)
                pdf_path = tempfile.mktemp(suffix=".pdf")
                doc.SaveAs(pdf_path, FileFormat=17)
                time.sleep(1)
                return pdf_path
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
                time.sleep(1)
                pythoncom.CoUninitialize()

        try:
            return self._com_retry(_attempt)
        except:
            self._kill_word_processes()
            return _attempt()

    def convert_doc_to_pdf(self, path):
        def _attempt():
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            word = None
            doc = None
            try:
                word = win32com.client.DispatchEx("Word.Application")
                word.Visible = False
                word.DisplayAlerts = 0
                abs_path = os.path.abspath(path)
                doc = word.Documents.Open(abs_path, ReadOnly=True)
                time.sleep(1)
                pdf_path = tempfile.mktemp(suffix=".pdf")
                doc.SaveAs(pdf_path, FileFormat=17)
                time.sleep(1)
                return pdf_path
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
                time.sleep(1)
                pythoncom.CoUninitialize()

        try:
            return self._com_retry(_attempt)
        except:
            self._kill_word_processes()
            return _attempt()

    # =========================================
    # CONTACT CHECK
    # =========================================

    @staticmethod
    def _has_contact_info(text):
        if not text:
            return False, False
        email_re = re.compile(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
        )
        phone_re = re.compile(r"(?:\+?\d[\s\-\.]*){10,15}")
        has_email = bool(email_re.search(text))
        has_phone = bool(phone_re.search(text))
        return has_email, has_phone

    # =========================================
    # MAIN PROCESS
    # =========================================

    def process(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()

        # STEP 1 — Scanned PDF check → skip native, go straight to OCR
        if ext == ".pdf" and PDFExtractor.is_scanned(file_path):
            print(f"Scanned PDF detected: {file_path}")
            return self._run_ocr_pipeline(file_path, ext)

        # STEP 2 — Native text extraction
        extracted_text = ""
        try:
            if ext == ".pdf":
                extracted_text = PDFExtractor.extract_text(file_path)

                # =========================================
                # FIX: Prepend form field text for PDFs
                # Contact info is sometimes only in fields
                # and get_text() misses it entirely
                # =========================================
                form_text = PDFExtractor.extract_form_fields(file_path)
                if form_text:
                    print(f"Form fields found: {len(form_text)} chars")
                    extracted_text = form_text + "\n" + extracted_text

            elif ext == ".docx":
                extracted_text = DOCXExtractor.extract_text(file_path)
            elif ext == ".doc":
                extracted_text = self.doc_extractor.extract_text(file_path)
            else:
                return {
                    "status": "failed",
                    "text": "",
                    "reason": f"Unsupported file type: {ext}",
                    "stage": "native_extraction",
                }
        except Exception as e:
            return {
                "status": "failed",
                "text": "",
                "reason": str(e),
                "stage": "native_extraction",
            }

        # STEP 3 — Clean native text
        clean_text = TextCleaner.clean(extracted_text)

        # STEP 4 — Validate NATIVE text only
        # If native is good → use it
        if TextValidator.is_text_good(clean_text):
            print(f"Native text OK: {file_path}")
            return {"status": "native_text", "text": clean_text}

        # STEP 5 — Native text failed validation → OCR fallback
        print(f"Native text failed validation, trying OCR: {file_path}")
        return self._run_ocr_pipeline(file_path, ext, extracted_text)

    # =========================================
    # OCR PIPELINE — NO VALIDATION, always use result
    # =========================================

    def _run_ocr_pipeline(self, file_path, ext, native_text=""):
        print(f"OCR triggered: {file_path}")
        ocr_text = ""

        try:
            if ext == ".pdf":
                pdf_path = file_path

            elif ext in [".doc", ".docx"]:
                print("🔄 Converting using LibreOffice...")
                pdf_path = self.convert_doc_to_pdf_libreoffice(file_path)

            else:
                return {
                    "status": "failed",
                    "text": native_text,
                    "reason": "Unsupported OCR file type",
                    "stage": "ocr_conversion",
                }
            

            images = PDFToImage.convert(pdf_path)
            if not images:
                return {
                    "status": "failed",
                    "text": native_text,
                    "reason": "No images generated from PDF",
                    "stage": "pdf_to_image",
                }

            print(f"Pages to OCR: {len(images)}")

            for page_num, img in enumerate(images, start=1):
                print(f"  OCR page {page_num}/{len(images)}")
                image_stream = io.BytesIO(img)
                result_holder = []
                self.ocr_worker.submit(image_stream, result_holder)
                page_text = result_holder[0] if result_holder else ""

                # =========================================
                # FIX: Log per-page OCR result length so
                # you can spot which pages return empty
                # =========================================
                print(
                    f"  Page {page_num} OCR result: "
                    f"{len(page_text)} chars"
                )

                ocr_text += page_text + "\n\n"

        except Exception as e:
            print(f"[ERROR] OCR failed: {e}")
            return {
                "status": "failed",
                "text": native_text,
                "reason": f"OCR error: {str(e)}",
                "stage": "ocr_error",
            }

        # STEP 6 — ALWAYS use OCR text, no validation
        # Clean it and return
        clean_ocr = TextCleaner.clean(ocr_text)

        if clean_ocr.strip():
            print(f"OCR text accepted: {len(clean_ocr)} chars")
            return {"status": "ocr_text", "text": clean_ocr}
        else:
            return {
                "status": "failed",
                "text": native_text,
                "reason": "OCR returned empty text",
                "stage": "ocr_empty",
            }

    import subprocess
    import tempfile

    def convert_doc_to_pdf_libreoffice(self, path):
        try:
            output_dir = tempfile.gettempdir()

            subprocess.run([
                "soffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                path
            ], check=True)

            pdf_name = os.path.splitext(os.path.basename(path))[0] + ".pdf"
            pdf_path = os.path.join(output_dir, pdf_name)

            if not os.path.exists(pdf_path):
                raise Exception("LibreOffice failed to create PDF")

            return pdf_path

        except Exception as e:
            print(f"[LIBREOFFICE ERROR] {e}")
            raise
