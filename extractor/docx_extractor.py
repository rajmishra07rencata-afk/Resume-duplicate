import re
from docx import Document
from docx.oxml.ns import qn


class DOCXExtractor:

    @staticmethod
    def extract_text(docx_path):

        try:

            doc = Document(docx_path)

            text_parts = []

            # =========================================
            # HEADERS & FOOTERS
            # =========================================

            for section in doc.sections:

                for container in [section.header, section.footer]:

                    if container is None:
                        continue

                    for para in container.paragraphs:

                        t = para.text.strip()

                        if t:
                            text_parts.append(t)

            # =========================================
            # BODY WALK
            #
            # Track seen content to deduplicate
            # paragraphs and table rows that appear
            # multiple times (common in PDF→DOCX
            # conversions and multi-column layouts)
            # =========================================

            seen = set()

            for element in doc.element.body:

                tag = element.tag

                # ---------------------------------
                # PARAGRAPH
                # ---------------------------------
                if tag.endswith("}p"):

                    para_text = DOCXExtractor._para_text(element)

                    if not para_text.strip():
                        continue

                    key = DOCXExtractor._normalize(para_text)

                    if key in seen:
                        continue

                    seen.add(key)
                    text_parts.append(para_text.strip())

                # ---------------------------------
                # TABLE
                # ---------------------------------
                elif tag.endswith("}tbl"):

                    for row in element.iter(qn("w:tr")):

                        row_text = DOCXExtractor._process_row(row)

                        if not row_text:
                            continue

                        key = DOCXExtractor._normalize(row_text)

                        if key in seen:
                            continue

                        seen.add(key)
                        text_parts.append(row_text)

            return "\n".join(text_parts).strip()

        except Exception as e:

            print(f"DOCX Extraction Error: {e}")
            return ""

    # =========================================
    # PARAGRAPH TEXT
    #
    # Collect ONLY from w:t nodes.
    # element.iter() on all nodes accidentally
    # picks up text from wrapper elements too.
    # =========================================

    @staticmethod
    def _para_text(element):

        return "".join(
            node.text
            for node in element.iter(qn("w:t"))
            if node.text
        )

    # =========================================
    # PROCESS TABLE ROW
    #
    # Deduplicate cells within the same row.
    # Many DOCX files from PDF converters have
    # identical text repeated across all cells.
    # =========================================

    @staticmethod
    def _process_row(row):

        seen_cells = set()
        row_cells  = []

        for cell in row.iter(qn("w:tc")):

            cell_text = DOCXExtractor._cell_text(cell)

            if not cell_text.strip():
                continue

            key = DOCXExtractor._normalize(cell_text)

            # Skip exact duplicate cells in same row
            if key in seen_cells:
                continue

            seen_cells.add(key)
            row_cells.append(cell_text.strip())

        if not row_cells:
            return ""

        # Join cells with separator
        return " | ".join(row_cells)

    # =========================================
    # CELL TEXT
    #
    # Join all paragraph texts within a cell.
    # =========================================

    @staticmethod
    def _cell_text(cell):

        paras = []

        for para in cell.iter(qn("w:p")):

            t = "".join(
                node.text
                for node in para.iter(qn("w:t"))
                if node.text
            )

            if t.strip():
                paras.append(t.strip())

        return "\n".join(paras)

    # =========================================
    # NORMALIZE FOR COMPARISON
    # =========================================

    @staticmethod
    def _normalize(text):

        return re.sub(r"\s+", " ", text.strip().lower())