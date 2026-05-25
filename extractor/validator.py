import re


class TextValidator:

    @staticmethod
    def is_text_good(text):

        if not text:
            return False

        text = text.strip()

        # Too small
        if len(text) < 100:
            return False

        # Word count
        words = re.findall(r'\b[A-Za-z]{2,}\b', text)

        if len(words) < 20:
            return False

        # Alphabet ratio
        alpha_chars = sum(c.isalpha() for c in text)

        visible_chars = sum(
            c.isalnum() or c.isspace()
            for c in text
        )

        if visible_chars == 0:
            return False

        ratio = alpha_chars / visible_chars

        if ratio < 0.5:
            return False

        return True