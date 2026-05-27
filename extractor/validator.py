import re


class TextValidator:

    RESUME_KEYWORDS = [
        "experience",
        "education",
        "skills",
        "project",
        "projects",
        "summary",
        "objective",
        "profile",
        "engineer",
        "developer",
        "manager",
        "mobile",
        "phone",
        "email",
        "technologies",
    ]

    # =========================================
    # MAIN VALIDATION
    # =========================================

    @staticmethod
    def is_text_good(text):

        if not text:
            return False

        text = text.strip()

        # -----------------------------------------
        # VERY SHORT TEXT
        # -----------------------------------------

        if len(text) < 50:
            return False

        # -----------------------------------------
        # WORD COUNT
        # Relaxed threshold for resumes
        # -----------------------------------------

        words = re.findall(r"\b[A-Za-z]{2,}\b", text)

        if len(words) < 5:
            return False

        # -----------------------------------------
        # EMAIL SIGNAL
        # Strong resume indicator
        # -----------------------------------------

        if re.search(
            r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
            text,
            re.IGNORECASE
        ):
            return True

        # -----------------------------------------
        # PHONE SIGNAL
        # -----------------------------------------

        if re.search(r'\b[6-9]\d{9}\b', text):
            return True

        # -----------------------------------------
        # RESUME KEYWORDS
        # -----------------------------------------

        lower = text.lower()

        keyword_hits = sum(
            1
            for kw in TextValidator.RESUME_KEYWORDS
            if kw in lower
        )

        if keyword_hits >= 2:
            return True

        # =========================================
        # ALPHA RATIO CHECK
        # More relaxed for resumes
        # =========================================

        alpha_chars = sum(c.isalpha() for c in text)

        visible_chars = sum(
            c.isalnum() or c.isspace()
            for c in text
        )

        if visible_chars == 0:
            return False

        ratio = alpha_chars / visible_chars

        # OLD = 0.20
        # NEW = 0.12
        if ratio < 0.12:
            return False

        # =========================================
        # GARBAGE DETECTION
        # =========================================

        if TextValidator._is_garbage(text):
            return False

        return True

    # =========================================
    # GARBAGE DETECTION
    # =========================================

    @staticmethod
    def _is_garbage(text):

        # repeated chars
        if re.search(r"(.)\1{12,}", text):
            return True

        # weird symbols
        symbols = sum(
            1 for c in text
            if not c.isalnum()
            and not c.isspace()
            and c not in ".,;:!?-()@#&+'/\""
        )

        if len(text) > 0 and symbols / len(text) > 0.45:
            return True

        return False