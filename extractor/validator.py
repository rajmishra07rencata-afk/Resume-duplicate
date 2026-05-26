import re


class TextValidator:

    @staticmethod
    def is_text_good(text):

        if not text:
            return False

        text = text.strip()

        if len(text) < 50:
            return False

        words = re.findall(r'\b[A-Za-z]{2,}\b', text)

        if len(words) < 8:
            return False

        alpha_chars = sum(c.isalpha() for c in text)

        visible_chars = sum(
            c.isalnum() or c.isspace()
            for c in text
        )

        if visible_chars == 0:
            return False

        ratio = alpha_chars / visible_chars

        # =========================================
        # RELAXED: resumes have dates, pipes,
        # bullets, phone numbers which lower ratio
        # =========================================
        if ratio < 0.20:   # was 0.30
            return False

        return True