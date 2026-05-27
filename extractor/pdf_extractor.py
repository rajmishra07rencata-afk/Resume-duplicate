import fitz
from collections import defaultdict


class PDFExtractor:

    # =========================================
    # SCANNED PDF DETECTION
    #
    # If average chars per page is below
    # threshold → it is a scanned image PDF
    # → skip native extraction → go straight to OCR
    # =========================================

    MIN_CHARS_PER_PAGE = 50

    @staticmethod
    def is_scanned(pdf_path):

        try:

            doc = fitz.open(pdf_path)

            total_chars = 0
            total_pages = len(doc)

            for page in doc:
                total_chars += len(page.get_text().strip())

            doc.close()

            if total_pages == 0:
                return True

            avg = total_chars / total_pages

            return avg < PDFExtractor.MIN_CHARS_PER_PAGE

        except Exception:
            return True

    # =========================================
    # MAIN EXTRACT
    # =========================================

    @staticmethod
    def extract_text(pdf_path):

        text = ""

        try:

            doc = fitz.open(pdf_path)

            for page in doc:

                page_text = PDFExtractor._extract_page(page)

                text += page_text + "\n\n"

            doc.close()

        except Exception as e:

            print(f"PDF Extraction Error: {e}")

        return text.strip()

    # =========================================
    # EXTRACT SINGLE PAGE
    # =========================================

    @staticmethod
    def _extract_page(page):

        # Each word: (x0, y0, x1, y1, word, block, line, word_no)
        words = page.get_text("words")

        if not words:
            return ""

        # Step 1: deduplicate overlapping words
        unique = PDFExtractor._deduplicate(words)

        if not unique:
            return ""

        # Step 2: detect columns and reconstruct
        return PDFExtractor._reconstruct(unique, page.rect.width)

    # =========================================
    # DEDUPLICATE WORDS BY BOUNDING BOX
    #
    # If two words occupy the same position
    # on the page they are from duplicate
    # layers → keep only the first occurrence
    # =========================================

    @staticmethod
    def _deduplicate(words):

        words_sorted = sorted(
            words,
            key=lambda w: (round(w[1] / 5) * 5, w[0])
        )

        accepted       = []
        accepted_rects = []

        for w in words_sorted:

            x0, y0, x1, y1, word = w[0], w[1], w[2], w[3], w[4]

            if not word.strip():
                continue

            if PDFExtractor._overlaps(x0, y0, x1, y1, accepted_rects):
                continue

            accepted_rects.append((x0, y0, x1, y1))
            accepted.append((x0, y0, x1, y1, word))

        return accepted

    @staticmethod
    def _overlaps(x0, y0, x1, y1, rects):

        for (ax0, ay0, ax1, ay1) in rects:

            ox = min(x1, ax1) - max(x0, ax0)
            oy = min(y1, ay1) - max(y0, ay0)

            if ox > 0 and oy > 0:
                return True

        return False

    # =========================================
    # COLUMN DETECTION + LAYOUT RECONSTRUCT
    #
    # Many resumes use 2-column layout.
    # Detect column split point by finding
    # a horizontal gap in word distribution.
    # Read left column fully before right.
    # =========================================

    @staticmethod
    def _reconstruct(words, page_width):

        mid_x = PDFExtractor._find_column_split(words, page_width)

        if mid_x is None:

            # Single column
            return PDFExtractor._build_lines(words)

        else:

            # Multi-column: left first then right
            left  = [w for w in words if w[2] <= mid_x]
            right = [w for w in words if w[0] >= mid_x]

            parts = []

            left_text = PDFExtractor._build_lines(left)
            if left_text.strip():
                parts.append(left_text)

            right_text = PDFExtractor._build_lines(right)
            if right_text.strip():
                parts.append(right_text)

            return "\n\n".join(parts)

    @staticmethod
    def _find_column_split(words, page_width):

        if not words:
            return None

        strips      = 20
        strip_w     = page_width / strips
        counts      = defaultdict(int)

        for w in words:

            x_center = (w[0] + w[2]) / 2
            strip    = int(x_center / strip_w)
            counts[strip] += 1

        # Look for gap in middle 50% of page
        mid_start = strips // 4
        mid_end   = 3 * strips // 4

        min_count = float("inf")
        min_strip = None

        for s in range(mid_start, mid_end):

            c = counts.get(s, 0)

            if c < min_count:
                min_count = c
                min_strip = s

        avg = sum(counts.values()) / max(len(counts), 1)

        # Clear gap = less than 10% of average density
        if min_count < avg * 0.1 and min_strip is not None:
            return min_strip * strip_w

        return None

    # =========================================
    # BUILD LINES FROM WORD LIST
    #
    # Groups words into lines using y position.
    # Words within 5px vertically = same line.
    # =========================================

    @staticmethod
    def _build_lines(words):

        if not words:
            return ""

        words_sorted = sorted(
            words,
            key=lambda w: (round(w[1] / 5) * 5, w[0])
        )

        lines        = []
        current_line = []
        current_y    = round(words_sorted[0][1] / 5) * 5

        for wt in words_sorted:

            x0, y0, x1, y1, word = wt

            line_y = round(y0 / 5) * 5

            if abs(line_y - current_y) <= 5:
                current_line.append(wt)
            else:
                if current_line:
                    current_line.sort(key=lambda w: w[0])
                    lines.append(
                        " ".join(w[4] for w in current_line)
                    )
                current_line = [wt]
                current_y    = line_y

        if current_line:
            current_line.sort(key=lambda w: w[0])
            lines.append(
                " ".join(w[4] for w in current_line)
            )

        return "\n".join(lines)