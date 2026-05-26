import re


class ContactExtractor:

    # =========================================
    # EMAIL REGEX
    # =========================================

    EMAIL_RE = re.compile(
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )

    # =========================================
    # PHONE LABEL REGEX
    # Detects labeled phone fields:
    # "Phone:", "Mobile:", "Mob:", "Tel:" etc.
    # =========================================

    PHONE_LABEL_RE = re.compile(
        r'(?:phone|mobile|mob|cell|tel|contact|ph|whatsapp)'
        r'\s*[:\-]?\s*',
        re.IGNORECASE
    )

    # =========================================
    # PHONE DIGIT REGEX
    # Covers formats:
    # +91 98765 43210
    # +1 (555) 123-4567
    # 9876543210
    # 98765-43210
    # 044-12345678
    # =========================================

    PHONE_DIGIT_RE = re.compile(
        r'''
        (?:\+?\d{1,4}[\s\-]?)?          # country code  +91 / +1
        (?:\(?\d{2,5}\)?[\s\-]?)?       # area code     (044)
        \d{3,5}[\s\-]?\d{3,5}           # main number   98765 43210
        ''',
        re.VERBOSE
    )

    # =========================================
    # FALLBACK: bare 10-digit number
    # Catches Indian mobile numbers directly
    # e.g. 9876543210
    # =========================================

    BARE_PHONE_RE = re.compile(
        r'\b(?:\+91[\s\-]?)?[6-9]\d{9}\b'  # Indian mobile
        r'|'
        r'\b\d{10}\b'                        # any 10-digit
    )

    # =========================================
    # EXTRACT EMAIL
    # =========================================

    @classmethod
    def extract_email(cls, text):

        matches = cls.EMAIL_RE.findall(text)

        if not matches:
            return ""

        # Return first valid email found
        return matches[0].strip()

    # =========================================
    # EXTRACT PHONE
    # =========================================

    @classmethod
    def extract_phone(cls, text):

        # -----------------------------------------
        # STRATEGY 1: labeled phone
        # Look for "Phone: XXXXXXXXXX"
        # Most reliable — use this first
        # -----------------------------------------

        for match in cls.PHONE_LABEL_RE.finditer(text):

            # Grab text right after the label (up to 30 chars)
            after_label = text[match.end(): match.end() + 30]

            digit_match = cls.PHONE_DIGIT_RE.search(after_label)

            if digit_match:

                phone = cls._clean_phone(digit_match.group())

                if cls._is_valid_phone(phone):
                    return phone

        # -----------------------------------------
        # STRATEGY 2: bare number pattern
        # Fallback when no label present
        # -----------------------------------------

        bare_match = cls.BARE_PHONE_RE.search(text)

        if bare_match:

            phone = cls._clean_phone(bare_match.group())

            if cls._is_valid_phone(phone):
                return phone

        # -----------------------------------------
        # STRATEGY 3: raw digit pattern
        # Last resort — broader search
        # -----------------------------------------

        digit_match = cls.PHONE_DIGIT_RE.search(text)

        if digit_match:

            phone = cls._clean_phone(digit_match.group())

            if cls._is_valid_phone(phone):
                return phone

        return ""

    # =========================================
    # CLEAN PHONE
    # Normalize to digits + leading +
    # =========================================

    @classmethod
    def _clean_phone(cls, raw):

        # Keep digits and leading +
        cleaned = re.sub(r'[^\d+]', '', raw.strip())

        return cleaned

    # =========================================
    # VALIDATE PHONE
    # Reject garbage matches like years (2024)
    # =========================================

    @classmethod
    def _is_valid_phone(cls, phone):

        digits_only = re.sub(r'\D', '', phone)

        # Must have at least 7 digits, max 15
        if len(digits_only) < 7 or len(digits_only) > 15:
            return False

        return True

    # =========================================
    # MAIN EXTRACT — returns dict
    # =========================================

    @classmethod
    def extract(cls, text):

        return {
            "email": cls.extract_email(text),
            "phone": cls.extract_phone(text)
        }