import re


class ContactExtractor:

    # =========================================================
    # EMAIL REGEX
    # =========================================================

    EMAIL_RE = re.compile(
        r'''
        (?<![\w.+-])
        [A-Z0-9._%+\-]+
        @
        [A-Z0-9.\-]+
        \.[A-Z]{2,}
        (?![\w.-])
        ''',
        re.IGNORECASE | re.VERBOSE
    )

    # =========================================================
    # PHONE LABELS
    #
    # Helps prioritize likely contact numbers
    # =========================================================

    PHONE_LABEL_RE = re.compile(
        r'''
        (?:phone|mobile|mob|cell|tel|telephone|
        contact|ph|whatsapp|call|m\b)
        \s*[:\-]?\s*
        ''',
        re.IGNORECASE | re.VERBOSE
    )

    # =========================================================
    # GLOBAL PHONE REGEX
    #
    # Supports:
    # +91 9876543210
    # +1 (718) 555-0100
    # 718-555-0100
    # 718.555.0100
    # (044) 23456789
    # +44 20 7946 0958
    # +61 412 345 678
    # =========================================================

    PHONE_RE = re.compile(
        r'''
        (?<!\d)
        (
            (?:
                \+?\d{1,3}
                [\s\-.]*
            )?

            (?:
                \(?\d{2,5}\)?
                [\s\-.]*
            )?

            (?:
                \d{2,5}
                [\s\-.]*
            ){1,4}

            \d{2,5}
        )
        (?!\d)
        ''',
        re.VERBOSE
    )

    # =========================================================
    # INVALID PHONE PATTERNS
    # =========================================================

    INVALID_PATTERNS = [

        re.compile(r'^(19|20)\d{2}$'),       # years
        re.compile(r'^(\d)\1{6,}$'),         # 1111111111
        re.compile(r'^12345'),               # fake sequence
        re.compile(r'^98765$'),              # OCR junk
        re.compile(r'0000'),                 # suspicious
    ]

    # =========================================================
    # MAIN EXTRACT
    # =========================================================

    @classmethod
    def extract(cls, text):

        return {
            "email": cls.extract_email(text),
            "phone": cls.extract_phone(text)
        }

    # =========================================================
    # EMAIL EXTRACTION
    # =========================================================

    @classmethod
    def extract_email(cls, text):

        if not text:
            return ""

        text = cls._normalize_text(text)

        emails = []

        for match in cls.EMAIL_RE.finditer(text):

            email = match.group().strip()

            email = email.strip(".,;:|]}>)")

            if cls._is_valid_email(email):
                emails.append(email.lower())

        emails = list(dict.fromkeys(emails))

        return emails[0] if emails else ""

    # =========================================================
    # EMAIL VALIDATION
    # =========================================================

    @classmethod
    def _is_valid_email(cls, email):

        try:

            if '@' not in email:
                return False

            local, domain = email.split('@', 1)

            if '.' not in domain:
                return False

            tld = domain.split('.')[-1]

            if len(tld) < 2 or len(tld) > 10:
                return False

            return True

        except:
            return False

    # =========================================================
    # PHONE EXTRACTION
    # =========================================================

    @classmethod
    def extract_phone(cls, text):

        if not text:
            return ""

        text = cls._normalize_text(text)

        candidates = []

        # =====================================================
        # STRATEGY 1
        # Prefer labeled numbers
        # =====================================================

        for label_match in cls.PHONE_LABEL_RE.finditer(text):

            nearby = text[
                label_match.end():
                label_match.end() + 80
            ]

            for match in cls.PHONE_RE.finditer(nearby):

                raw = match.group(1)

                cleaned = cls._clean_phone(raw)

                if cls._is_valid_phone(cleaned):

                    score = cls._score_phone(cleaned)

                    candidates.append(
                        (score, cleaned)
                    )

        # =====================================================
        # STRATEGY 2
        # Search globally
        # =====================================================

        for match in cls.PHONE_RE.finditer(text):

            raw = match.group(1)

            cleaned = cls._clean_phone(raw)

            if cls._is_valid_phone(cleaned):

                score = cls._score_phone(cleaned)

                candidates.append(
                    (score, cleaned)
                )

        # =====================================================
        # NO RESULT
        # =====================================================

        if not candidates:
            return ""

        # =====================================================
        # REMOVE DUPLICATES
        # =====================================================

        unique = {}

        for score, phone in candidates:

            if phone not in unique:
                unique[phone] = score

            else:
                unique[phone] = max(
                    unique[phone],
                    score
                )

        candidates = [
            (score, phone)
            for phone, score in unique.items()
        ]

        # =====================================================
        # SORT BY SCORE
        # =====================================================

        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )

        best_phone = candidates[0][1]

        return cls._format_phone(best_phone)

    # =========================================================
    # NORMALIZE OCR TEXT
    # =========================================================

    @classmethod
    def _normalize_text(cls, text):

        # remove zero-width chars
        text = re.sub(
            r'[\u200b\u200c\u200d]',
            '',
            text
        )

        # join broken OCR digits
        text = re.sub(
            r'(\d)\s*\n\s*(\d)',
            r'\1\2',
            text
        )

        # normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)

        return text

    # =========================================================
    # CLEAN PHONE
    # =========================================================

    @classmethod
    def _clean_phone(cls, raw):

        raw = raw.strip()

        # remove spaces/newlines
        raw = re.sub(r'\s+', '', raw)

        # keep only digits and +
        cleaned = re.sub(
            r'[^\d+]',
            '',
            raw
        )

        # fix multiple +
        if cleaned.count('+') > 1:

            cleaned = (
                '+' +
                cleaned.replace('+', '')
            )

        return cleaned

    # =========================================================
    # PHONE VALIDATION
    # =========================================================

    @classmethod
    def _is_valid_phone(cls, phone):

        digits = re.sub(r'\D', '', phone)

        # international length
        if len(digits) < 10:
            return False

        if len(digits) > 15:
            return False

        # invalid patterns
        for pattern in cls.INVALID_PATTERNS:

            if pattern.search(digits):
                return False

        # reject all same digits
        if len(set(digits)) == 1:
            return False

        # reject likely years
        if digits.startswith(("19", "20")) and len(digits) <= 12:
            return False

        return True

    # =========================================================
    # PHONE SCORING
    #
    # Higher score = better candidate
    # =========================================================

    @classmethod
    def _score_phone(cls, phone):

        score = 0

        digits = re.sub(r'\D', '', phone)

        # prefer international
        if phone.startswith('+'):
            score += 50

        # prefer realistic lengths
        if 10 <= len(digits) <= 12:
            score += 30

        # prefer non-repeating
        if len(set(digits)) > 4:
            score += 20

        return score

    # =========================================================
    # FORMAT PHONE
    # =========================================================

    @classmethod
    def _format_phone(cls, phone):

        digits = re.sub(r'\D', '', phone)

        if phone.startswith('+'):
            return "+" + digits

        return digits