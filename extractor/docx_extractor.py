from docx import Document


class DOCXExtractor:

    @staticmethod
    def extract_text(docx_path):

        try:

            doc = Document(docx_path)

            text = "\n".join(
                para.text
                for para in doc.paragraphs
            )

            return text.strip()

        except Exception as e:

            print(f"DOCX Extraction Error: {e}")
            return ""