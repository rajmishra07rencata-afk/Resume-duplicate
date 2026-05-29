import re

class RegexExtractor:

    @staticmethod
    def extract_email(text):

        # ✅ Fix broken words (VERY IMPORTANT)
        text = re.sub(r"(\w)\s*\n\s*(\w)", r"\1\2", text)

        # ✅ Normalize whitespace
        text = text.replace("\n", " ").replace("\r", " ")

        # ✅ Email regex (OCR tolerant)
        pattern = r"[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}"

        matches = re.findall(pattern, text)

        if not matches:
            return ""

        # ✅ Clean spaces inside email
        email = matches[0]
        email = re.sub(r"\s+", "", email)

        # ✅ Remove trailing dot
        email = email.rstrip(".")

        return email

    @staticmethod
    def extract_phone(text):

        # ✅ Fix broken tokens
        text = re.sub(r"(\w)\s*\n\s*(\w)", r"\1\2", text)

        # ✅ Normalize whitespace
        text = text.replace("\n", " ").replace("\r", " ")

        # =========================
        # ✅ Extract candidates
        # =========================
        pattern = r"\+?\d[\d\s\-\(\),]{6,}\d"
        matches = re.findall(pattern, text)

        candidates = []

        for m in matches:

            # ✅ Skip if letters present (avoid email junk)
            if re.search(r"[a-zA-Z]", m):
                continue

            # ✅ Split multiple numbers (comma case)
            parts = re.split(r"[,\|]", m)

            for p in parts:
                cleaned = re.sub(r"[^\d+]", "", p)
                digits = re.sub(r"\D", "", cleaned)

                # ✅ FILTER RULES

                # Reject too short
                if len(digits) < 8:
                    continue

                # Accept valid range
                if 8 <= len(digits) <= 15:
                    candidates.append(cleaned)

        if not candidates:
            return ""

        return candidates[0]