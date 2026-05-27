import re


class ContactExtractor:

    # =========================================
    # EMAIL REGEX
    # =========================================

    EMAIL_RE = re.compile(
        r'''
        [a-zA-Z0-9._%+\-]+
        @
        [a-zA-Z0-9.\-]+
        \.
        (?:com|in|org|net|edu|gov|co\.in)
        ''',
        re.IGNORECASE | re.VERBOSE
    )

    # =========================================
    # GENERIC INTERNATIONAL PHONE
    #
    # Supports:
    # (718) 555-0100
    # +1 718 555 0100
    # +91 9876543210
    # 9876543210
    # 718.555.0100
    # =========================================

    GENERIC_PHONE_RE = re.compile(
        r'''
        (?:
            (?:\+?\d{1,3}[\s\-\.]?)?      # optional country code
            (?:\(?\d{2,5}\)?[\s\-\.]?)?  # optional area code
            \d{3,5}[\s\-\.]?\d{3,5}[\s\-\.]?\d{2,5}
        )
        ''',
        re.VERBOSE
    )

    # =========================================
    # BAD NUMBER FILTERS
    # =========================================

    INVALID_PATTERNS = [

        re.compile(r'^(19|20)\d{2}$'),   # years
        re.compile(r'^(\d)\1{5,}$'),     # 1111111111
        re.compile(r'^12345'),           # fake sequence
        re.compile(r'^98765$'),          # OCR junk
    ]

    # =========================================
    # EMAIL EXTRACTION
    # =========================================

    @classmethod
    def extract_email(cls, text):

        if not text:
            return ""

        matches = cls.EMAIL_RE.finditer(text)

        emails = []

        for match in matches:

            email = match.group().strip()

            # Remove OCR trailing junk
            email = re.sub(
                r'(com|in|org|net|edu|gov)([A-Z].*)$',
                r'\1',
                email
            )

            email = email.strip(".,;:|]}>)")

            if cls._is_valid_email(email):
                emails.append(email)

        emails = list(dict.fromkeys(emails))

        return emails[0] if emails else ""

    # =========================================
    # EMAIL VALIDATION
    # =========================================

    @classmethod
    def _is_valid_email(cls, email):

        if '@' not in email:
            return False

        local, domain = email.split('@', 1)

        if '.' not in domain:
            return False

        tld = domain.split('.')[-1]

        # Reject OCR garbage TLDs
        if len(tld) > 6:
            return False

        return True

    # =========================================
    # PHONE EXTRACTION
    # =========================================

    @classmethod
    def extract_phone(cls, text):

        if not text:
            return ""

        text = cls._normalize_text(text)

        candidates = []

        # =====================================
        # FIND ALL PHONE CANDIDATES
        # =====================================

        matches = cls.GENERIC_PHONE_RE.finditer(text)

        for match in matches:

            raw = match.group().strip()

            cleaned = cls._clean_phone(raw)

            if cls._is_valid_phone(cleaned):

                formatted = cls._format_phone(cleaned)

                candidates.append(formatted)

        # =====================================
        # REMOVE DUPLICATES
        # =====================================

        candidates = list(dict.fromkeys(candidates))

        if not candidates:
            return ""

        # =====================================
        # PRIORITY SORTING
        #
        # Prefer:
        # 1. country code
        # 2. longer numbers
        # =====================================

        candidates.sort(
            key=lambda x: (
                not x.startswith("+"),
                -len(re.sub(r"\D", "", x))
            )
        )

        return candidates[0]

    # =========================================
    # NORMALIZE OCR TEXT
    # =========================================

    @classmethod
    def _normalize_text(cls, text):

        # Remove zero-width chars
        text = re.sub(
            r'[\u200b\u200c\u200d]',
            '',
            text
        )

        # Join broken OCR phone lines
        # Example:
        # 98765
        # 43210
        #
        # becomes:
        # 9876543210

        text = re.sub(
            r'(\d)\s*\n\s*(\d)',
            r'\1\2',
            text
        )

        # Normalize spaces
        text = re.sub(r'[ \t]+', ' ', text)

        return text

    # =========================================
    # CLEAN PHONE
    # =========================================

    @classmethod
    def _clean_phone(cls, raw):

        raw = raw.strip()

        # Normalize:
        # (+91) -> +91

        raw = re.sub(
            r'\(\s*(\+\d+)\s*\)',
            r'\1',
            raw
        )

        # Keep only digits and +
        cleaned = re.sub(
            r'[^\d+]',
            '',
            raw
        )

        # Fix multiple +
        if cleaned.count('+') > 1:
            cleaned = cleaned.replace('+', '')

        return cleaned

    # =========================================
    # FORMAT PHONE
    # =========================================

    @classmethod
    def _format_phone(cls, phone):

        digits = re.sub(r'\D', '', phone)

        # Preserve international format
        if phone.startswith('+'):
            return "+" + digits

        return digits

    # =========================================
    # PHONE VALIDATION
    # =========================================

    @classmethod
    def _is_valid_phone(cls, phone):

        digits = re.sub(r'\D', '', phone)

        # International length
        if len(digits) < 10 or len(digits) > 15:
            return False

        # Reject bad patterns
        for pattern in cls.INVALID_PATTERNS:

            if pattern.search(digits):
                return False

        # Reject repeated digits
        if len(set(digits)) == 1:
            return False

        return True

    # =========================================
    # MAIN EXTRACT
    # =========================================

    @classmethod
    def extract(cls, text):

        return {
            "email": cls.extract_email(text),
            "phone": cls.extract_phone(text)
        }