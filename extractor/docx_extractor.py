from docx import Document
from docx.oxml.ns import qn


class DOCXExtractor:

    @staticmethod
    def extract_text(docx_path):

        try:

            doc = Document(docx_path)

            text_parts = []

            # =========================================
            # EXTRACT HEADERS (name, contact often here)
            # =========================================

            for section in doc.sections:

                for header in [section.header, section.footer]:

                    if header:

                        for para in header.paragraphs:

                            if para.text.strip():
                                text_parts.append(para.text.strip())

            # =========================================
            # WALK BODY IN DOCUMENT ORDER
            # Paragraphs AND tables, not just paragraphs
            # =========================================

            for element in doc.element.body:

                tag = element.tag

                # --- Paragraph ---
                if tag.endswith("}p"):

                    para_text = "".join(
                        node.text
                        for node in element.iter()
                        if node.text
                    )

                    if para_text.strip():
                        text_parts.append(para_text.strip())

                # --- Table ---
                elif tag.endswith("}tbl"):

                    for row in element.iter(qn("w:tr")):

                        row_cells = []

                        for cell in row.iter(qn("w:tc")):

                            cell_text = "".join(
                                node.text
                                for node in cell.iter()
                                if node.text
                            )

                            if cell_text.strip():
                                row_cells.append(cell_text.strip())

                        if row_cells:
                            text_parts.append(" | ".join(row_cells))

            return "\n".join(text_parts).strip()

        except Exception as e:

            print(f"DOCX Extraction Error: {e}")
            return ""