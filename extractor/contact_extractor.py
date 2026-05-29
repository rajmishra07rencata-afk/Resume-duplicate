import re


class ContactExtractor:

    # =========================================
    # EMAIL REGEX
    # =========================================

    EMAIL_RE = re.compile(
        r'''
        \b
        [a-zA-Z0-9._%+\-]+
        @
        [a-zA-Z0-9.\-]+
        \.
        [a-zA-Z]{2,}
        \b
        ''',
        re.IGNORECASE | re.VERBOSE
    )

    # =========================================
    # GENERIC INTERNATIONAL PHONE
    #
    # Supports:
    # +91 98765 43210
    # +91 9876543210
    # 98765 43210
    # 987-654-3210
    # (044) 1234-5678
    # 9876543210
    # =========================================

    GENERIC_PHONE_RE = re.compile(
        r'''
        (?<!\d)                        # not preceded by a digit
        (?:
            (?:\+?\d{1,3}[\s\-\.]?)?   # optional country code
            (?:\(?\d{2,5}\)?[\s\-\.]?)? # optional area code
            (?:
                \d{3,5}[\s\-\.]?\d{3,5}[\s\-\.]?\d{2,5}   # 3 groups
                |
                \d{5}[\s\-\.]?\d{5}                         # 2 groups mobile
                |
                \d{10,15}                                   # continuous
            )
        )
        (?!\d)                           # not followed by a digit
        ''',
        re.VERBOSE
    )

    # =========================================
    # BAD NUMBER FILTERS
    # =========================================

    INVALID_PATTERNS = [
        re.compile(r'^(19|20)\d{2}$'),      # years
        re.compile(r'^(\d)\1{5,}$'),          # 1111111111
        re.compile(r'^12345'),               # fake sequence
        re.compile(r'^98765$'),              # OCR junk
        re.compile(r'^\d{4,6}$'),            # too short alone
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
                r'([a-z]{2,})([A-Z][a-zA-Z]+)$',
                r'\1',
                email
            )

            email = email.strip(".,;:|]}>)\"'")

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

        local, domain = email.rsplit('@', 1)

        if '.' not in domain:
            return False

        tld = domain.split('.')[-1]

        if not tld.isalpha() or len(tld) < 2 or len(tld) > 10:
            return False

        if len(local) < 1:
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

        matches = cls.GENERIC_PHONE_RE.finditer(text)

        for match in matches:

            raw = match.group().strip()
            cleaned = cls._clean_phone(raw)

            if cls._is_valid_phone(cleaned):

                formatted = cls._format_phone(cleaned)
                candidates.append(formatted)

        candidates = list(dict.fromkeys(candidates))

        if not candidates:
            return ""

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

        text = re.sub(
            r'[\u200b\u200c\u200d\ufeff]',
            '',
            text
        )

        text = re.sub(
            r'(\d)\s*\n\s*(\d)',
            r'\1\2',
            text
        )

        text = re.sub(r'[ \t]+', ' ', text)

        return text

    # =========================================
    # CLEAN PHONE
    # =========================================

    @classmethod
    def _clean_phone(cls, raw):

        raw = raw.strip()

        raw = re.sub(
            r'\(\s*(\+\d+)\s*\)',
            r'\1',
            raw
        )

        cleaned = re.sub(
            r'[^\d+]',
            '',
            raw
        )

        if cleaned.count('+') > 1:
            parts = cleaned.split('+')
            cleaned = '+' + ''.join(parts[1:])

        if '+' in cleaned and not cleaned.startswith('+'):
            cleaned = cleaned.replace('+', '')

        return cleaned

    # =========================================
    # FORMAT PHONE
    # =========================================

    @classmethod
    def _format_phone(cls, phone):

        digits = re.sub(r'\D', '', phone)

        if phone.startswith('+'):
            return "+" + digits

        return digits

    # =========================================
    # PHONE VALIDATION
    # =========================================

    @classmethod
    def _is_valid_phone(cls, phone):

        digits = re.sub(r'\D', '', phone)

        if len(digits) < 10 or len(digits) > 15:
            return False

        for pattern in cls.INVALID_PATTERNS:

            if pattern.search(digits):
                return False

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