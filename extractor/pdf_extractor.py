import fitz


class PDFExtractor:

    @staticmethod
    def extract_text(pdf_path):

        text = ""

        try:
            doc = fitz.open(pdf_path)

            for page in doc:
                text += page.get_text()

            doc.close()

        except Exception as e:
            print(f"PDF Extraction Error: {e}")

        return text.strip()