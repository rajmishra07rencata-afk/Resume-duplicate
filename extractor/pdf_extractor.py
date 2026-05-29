# import fitz


# class PDFExtractor:

#     MIN_CHARS_PER_PAGE = 50

#     @staticmethod
#     def is_scanned(pdf_path):
#         try:
#             doc = fitz.open(pdf_path)
#             total_chars = sum(len(page.get_text().strip()) for page in doc)
#             total_pages = len(doc)
#             doc.close()
#             if total_pages == 0:
#                 return True
#             return (total_chars / total_pages) < PDFExtractor.MIN_CHARS_PER_PAGE
#         except Exception:
#             return True

#     # =========================================
#     # SIMPLE EXTRACTION — Let PyMuPDF handle layout
#     # =========================================

#     @staticmethod
#     def extract_text(pdf_path):
#         """Extract text using PyMuPDF's built-in reading order logic"""
#         try:
#             doc = fitz.open(pdf_path)
#             text = ""
#             for page in doc:
#                 text += page.get_text() + "\n\n"
#             doc.close()
#             return text.strip()
#         except Exception as e:
#             print(f"PDF Extraction Error: {e}")
#             return ""

#     # =========================================
#     # BLOCKS EXTRACTION — Better for complex layouts
#     # =========================================

#     @staticmethod
#     def extract_blocks_text(pdf_path):
#         """Extract text blocks in reading order — handles columns better"""
#         try:
#             doc = fitz.open(pdf_path)
#             text = ""
#             for page in doc:
#                 blocks = page.get_text("blocks")
#                 # Sort by vertical position, then horizontal
#                 blocks.sort(key=lambda b: (b[1], b[0]))
#                 for b in blocks:
#                     text += b[4] + "\n"
#                 text += "\n"
#             doc.close()
#             return text.strip()
#         except Exception as e:
#             print(f"PDF Blocks Extraction Error: {e}")
#             return ""

#     # =========================================
#     # HTML EXTRACTION — Preserves structure
#     # =========================================

#     @staticmethod
#     def extract_html_text(pdf_path):
#         """Extract with HTML tags — helps identify headers/footers"""
#         try:
#             doc = fitz.open(pdf_path)
#             text = ""
#             for page in doc:
#                 text += page.get_text("html") + "\n\n"
#             doc.close()
#             # Strip HTML tags for plain text
#             import re
#             text = re.sub(r'<[^>]+>', ' ', text)
#             text = re.sub(r'\s+', ' ', text)
#             return text.strip()
#         except Exception as e:
#             print(f"PDF HTML Extraction Error: {e}")
#             return ""


import re
import fitz


class PDFExtractor:

    MIN_CHARS_PER_PAGE = 50

    @staticmethod
    def is_scanned(pdf_path):
        try:
            doc = fitz.open(pdf_path)
            total_chars = sum(
                len(page.get_text().strip()) for page in doc
            )
            total_pages = len(doc)
            doc.close()
            if total_pages == 0:
                return True
            return (total_chars / total_pages) < PDFExtractor.MIN_CHARS_PER_PAGE
        except Exception:
            return True

    # =========================================
    # SIMPLE EXTRACTION — Let PyMuPDF handle layout
    # =========================================

    @staticmethod
    def extract_text(pdf_path):
        """Extract text using PyMuPDF — includes annotation text for
        headers/footers that live outside the main content stream"""
        try:
            doc = fitz.open(pdf_path)
            text = ""

            for page in doc:

                # =========================================
                # FIX: Grab annotation content first
                # Many PDFs store header/footer contact info
                # in annotations, not the main text stream.
                # Prepend it so ContactExtractor finds it.
                # =========================================
                annot_text = ""
                for annot in page.annots():
                    content = annot.info.get("content", "").strip()
                    if content:
                        annot_text += content + "\n"

                page_text = page.get_text()
                text += annot_text + page_text + "\n\n"

            doc.close()
            return text.strip()

        except Exception as e:
            print(f"PDF Extraction Error: {e}")
            return ""

    # =========================================
    # FORM FIELDS EXTRACTION
    #
    # FIX: Some PDFs embed contact info in form
    # fields (AcroForm widgets). PyMuPDF's
    # get_text() skips these entirely.
    # =========================================

    @staticmethod
    def extract_form_fields(pdf_path):
        """Extract text from PDF form field widgets"""
        try:
            doc = fitz.open(pdf_path)
            field_text = ""
            for page in doc:
                for widget in page.widgets():
                    val = widget.field_value
                    if val and str(val).strip():
                        field_text += str(val).strip() + "\n"
            doc.close()
            return field_text.strip()
        except Exception:
            return ""

    # =========================================
    # BLOCKS EXTRACTION — Better for complex layouts
    # =========================================

    @staticmethod
    def extract_blocks_text(pdf_path):
        """Extract text blocks in reading order — handles columns better"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                blocks = page.get_text("blocks")
                blocks.sort(key=lambda b: (b[1], b[0]))
                for b in blocks:
                    text += b[4] + "\n"
                text += "\n"
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"PDF Blocks Extraction Error: {e}")
            return ""

    # =========================================
    # HTML EXTRACTION — Preserves structure
    # =========================================

    @staticmethod
    def extract_html_text(pdf_path):
        """Extract with HTML tags — helps identify headers/footers"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text("html") + "\n\n"
            doc.close()
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text)
            return text.strip()
        except Exception as e:
            print(f"PDF HTML Extraction Error: {e}")
            return ""