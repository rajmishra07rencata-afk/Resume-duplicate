import re


class ContactExtractor:
    """
    Resume contact extractor — handles every format observed in the dataset:

    Phone formats seen:
      8903619195                         (bare 10-digit Indian)
      +91 8939521316                     (E.164 with space)
      +91-9047467187                     (E.164 with dash)
      +91 - 7845745158                   (E.164 with spaced dash)
      +91 - 98427 63108                  (spaced digits)
      +919629806214                      (E.164 no sep)
      00919136739639                     (IDD 0091 prefix)
      0091-7339618912                    (IDD with dash)
      91+8555938482                      (reversed: digits then +)
      +1 914-999-6826                    (US format)
      +44 20 6366 4567                   (UK format)
      +4917673568977                     (DE format)
      +14084289952                       (US E.164)
      Mobile: +91 8056884395,Mail:...    (inline label)
      Phone:+91-9047510997E-Mail:...     (no space before label)

    Email formats seen:
      user@gmail.com
      user@yahoo.com
      user@outlook.com
      E-Mail: user@domain.com            (label prefix)
      E.Mail-user@domain.com             (dot-dash label fused)
      Email:user@domain.com              (no space)
      Mail:user@domain.com               (short label)
      user@g.com                         (short TLD domain — valid)
      deepak06_mkn@yahoo.com             (underscore+digits)
      E-Mail ID : user@domain.com        (with ID suffix)

    Known garbage/invalid:
      Rtrtr$@.com                        (invalid local/domain)
      WWWWW...SSS@g.com                  (absurd local part)
      Malin@@@d.com                      (multiple @)
      98746555555555555555555            (>15 digits)
      98744444454545454                  (>15 digits)
      91+8555938482                      (need special handling — reversed +)
    """

    # =========================================================================
    # EMAIL REGEX
    # Handles:  label prefixes fused with no space (E.Mail-user@...)
    #           short TLD domains like @g.com
    #           standard TLDs (com/in/org/net/edu/gov/co.in/io/uk/de/au/...)
    # =========================================================================

    # Strip common label prefixes that may be fused directly onto the address
    _EMAIL_LABEL_RE = re.compile(
        r'(?:e[\.\-]?mail(?:\s*id)?[\s:\-]*|mail[\s:\-]+)',
        re.IGNORECASE
    )

    EMAIL_RE = re.compile(
        r'''
        (?<![/@\w])             # not preceded by email-unfriendly chars
        [a-zA-Z0-9][a-zA-Z0-9._%+\-]*  # local part — must start with alnum
        @
        [a-zA-Z0-9][a-zA-Z0-9.\-]*     # domain — must start with alnum
        \.
        [a-zA-Z]{2,10}          # TLD (up to 10 chars covers modern TLDs)
        (?:\.[a-zA-Z]{2})?      # optional ccTLD suffix e.g. .co.in, .co.uk
        (?![a-zA-Z0-9_%+\-@])  # not followed by more email chars (period OK — we strip trailing dots in post)
        ''',
        re.IGNORECASE | re.VERBOSE
    )

    # =========================================================================
    # EMAIL VALIDATION CONSTANTS
    # =========================================================================

    # Local parts that are clearly garbage (all repeated letters, etc.)
    _LOCAL_GARBAGE_RE = re.compile(
        r'^([A-Z])\1{5,}',   # 6+ repeated uppercase letters e.g. WWWWWWW
        re.IGNORECASE
    )

    # =========================================================================
    # PHONE REGEX
    # =========================================================================

    # Handles reversed "91+NNNN" pattern (digits before +)
    _REVERSED_CC_RE = re.compile(r'^(\d{1,3})\+(\d{7,13})$')

    # Full phone candidate pattern
    PHONE_RE = re.compile(
        r'''
        (?:
            # Standard: optional country code, then number
            (?:\+|00)?                     # + or 00 IDD prefix
            \d{1,4}                        # country / area code start
            [\s\-\.]?
            (?:\(?\d{2,5}\)?[\s\-\.]?)?   # optional area code in parens
            \d{3,5}[\s\-\.]?\d{3,5}       # subscriber number (two halves)
            (?:[\s\-\.]?\d{1,5})?         # optional extension / last chunk
        )
        ''',
        re.VERBOSE
    )

    # =========================================================================
    # BAD PHONE FILTERS
    # =========================================================================

    INVALID_PHONE_PATTERNS = [
        re.compile(r'^(19|20)\d{2}$'),          # 4-digit years
        re.compile(r'^(\d)\1{5,}$'),            # all-same digit run
        re.compile(r'^12345'),                  # fake ascending sequence
        re.compile(r'^\d{16,}$'),               # absurdly long (>15 digits)
        re.compile(r'^(\d{2,5})\1{2,}$'),       # repeating blocks e.g. 123123123
    ]

    # =========================================================================
    # EMAIL EXTRACTION
    # =========================================================================

    @classmethod
    def extract_email(cls, text):
        if not text:
            return ""

        # Normalise the text so fused labels separate out
        # e.g. "E.Mail-foo@bar.com" → "foo@bar.com"
        clean = cls._EMAIL_LABEL_RE.sub(' ', text)

        matches = cls.EMAIL_RE.finditer(clean)
        emails = []

        for match in matches:
            email = match.group().strip()

            # Strip trailing punctuation that OCR / PDF often attaches
            email = email.strip(".,;:|]}>)(\"'")

            # Strip OCR junk appended after the TLD
            email = re.sub(
                r'(com|in|org|net|edu|gov|io|co)([A-Z].*)$',
                r'\1',
                email
            )

            if cls._is_valid_email(email):
                emails.append(email.lower())

        # Deduplicate, preserving order
        emails = list(dict.fromkeys(emails))
        return emails[0] if emails else ""

    # =========================================================================
    # EMAIL VALIDATION
    # =========================================================================

    @classmethod
    def _is_valid_email(cls, email):
        if email.count('@') != 1:
            return False                        # catches Malin@@@d.com

        local, domain = email.split('@', 1)

        if not local or not domain:
            return False

        if '.' not in domain:
            return False

        # Reject garbage local parts (all repeated uppercase etc.)
        if cls._LOCAL_GARBAGE_RE.match(local):
            return False

        # Local part must be at least 1 real character (not just symbols)
        if not re.search(r'[a-zA-Z0-9]', local):
            return False

        # Domain must have a valid-looking TLD
        tld = domain.split('.')[-1]
        if len(tld) < 2 or len(tld) > 10:
            return False

        # Reject domain that starts with a dot
        if domain.startswith('.'):
            return False

        return True

    # =========================================================================
    # PHONE EXTRACTION
    # =========================================================================

    @classmethod
    def extract_phone(cls, text):
        if not text:
            return ""

        text = cls._normalize_phone_text(text)

        candidates = []

        for match in cls.PHONE_RE.finditer(text):
            raw = match.group().strip()
            cleaned = cls._clean_phone(raw)

            if cls._is_valid_phone(cleaned):
                formatted = cls._format_phone(cleaned)
                candidates.append(formatted)

        # Deduplicate (normalised digits)
        seen_digits = {}
        unique = []
        for c in candidates:
            d = re.sub(r'\D', '', c)
            if d not in seen_digits:
                seen_digits[d] = True
                unique.append(c)

        if not unique:
            return ""

        # Priority:
        #   1. Has a + international prefix
        #   2. Longer digit count (more specific)
        unique.sort(
            key=lambda x: (
                not x.startswith('+'),
                -len(re.sub(r'\D', '', x))
            )
        )

        return unique[0]

    # =========================================================================
    # TEXT NORMALISATION
    # =========================================================================

    @classmethod
    def _normalize_phone_text(cls, text):
        # Remove zero-width Unicode characters
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)

        # Rejoin OCR-split phone lines:
        #   "98765\n43210" → "9876543210"
        text = re.sub(r'(\d)\s*\n\s*(\d)', r'\1\2', text)

        # Normalise multiple spaces / tabs
        text = re.sub(r'[ \t]+', ' ', text)

        # Fix reversed country-code format:  "91+8555938482" → "+918555938482"
        # Pattern: digits (1-3), literal +, more digits — at a word boundary
        text = re.sub(
            r'(?<!\d)(\d{1,3})\+(\d{7,13})(?!\d)',
            lambda m: '+' + m.group(1) + m.group(2),
            text
        )

        # Normalise IDD 00-prefix to + so PHONE_RE can handle it uniformly
        # "00919136739639" → "+919136739639"
        text = re.sub(
            r'(?<!\d)00(\d{10,13})(?!\d)',
            r'+\1',
            text
        )

        # "0091-7339618912" → "+91-7339618912"
        text = re.sub(
            r'(?<!\d)0091([\-\s]?\d{10})(?!\d)',
            r'+91\1',
            text
        )

        # Collapse "+CC - NNNNN" spaced-dash pattern into "+CCNNNNN"
        # e.g. "+91 - 7845745158" → "+917845745158"
        text = re.sub(r'(\+\d{1,3})\s*-\s*(\d)', r'\1\2', text)

        # Replace tilde (used as field separator in some resumes) with space
        text = text.replace('~', ' ')

        return text

    # =========================================================================
    # PHONE CLEANING
    # =========================================================================

    @classmethod
    def _clean_phone(cls, raw):
        raw = raw.strip()

        # Normalise parenthesised country code:  "(+91)" → "+91"
        raw = re.sub(r'\(\s*(\+\d+)\s*\)', r'\1', raw)

        # Keep only digits and leading +
        has_plus = raw.lstrip().startswith('+')
        cleaned = re.sub(r'[^\d]', '', raw)

        if has_plus:
            cleaned = '+' + cleaned

        # Discard if multiple + ended up inside
        if cleaned.count('+') > 1:
            cleaned = re.sub(r'\+', '', cleaned)

        return cleaned

    # =========================================================================
    # PHONE FORMATTING
    # =========================================================================

    @classmethod
    def _format_phone(cls, phone):
        digits = re.sub(r'\D', '', phone)

        if phone.startswith('+'):
            return '+' + digits

        return digits

    # =========================================================================
    # PHONE VALIDATION
    # =========================================================================

    @classmethod
    def _is_valid_phone(cls, phone):
        digits = re.sub(r'\D', '', phone)

        # ITU-T E.164: 7–15 digits
        if len(digits) < 7 or len(digits) > 15:
            return False

        # Apply hard-filter patterns
        for pat in cls.INVALID_PHONE_PATTERNS:
            if pat.search(digits):
                return False

        # Must not be all the same digit
        if len(set(digits)) == 1:
            return False

        return True

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    @classmethod
    def extract(cls, text):
        return {
            "email": cls.extract_email(text),
            "phone": cls.extract_phone(text)
        }


# =============================================================================
# SELF-TEST  —  covers every format observed in the combined.txt dataset
# Run:  python contact_extractor.py
# =============================================================================

if __name__ == "__main__":
    tests = [
        # (label, text, expected_phone, expected_email)

        # ── bare formats ──────────────────────────────────────────────────────
        ("bare 10-digit Indian",
         "A.RAJASEKAR 8903619195 rajasekar03101993@gmail.com.",
         "8903619195", "rajasekar03101993@gmail.com"),

        ("E.164 no sep",
         "PH:+919629806214 jai@example.com",
         "+919629806214", "jai@example.com"),

        ("E.164 with space",
         "+91 8939521316 abdalqadhir@gmail.com",
         "+918939521316", "abdalqadhir@gmail.com"),

        ("E.164 with dash",
         "Mobile: +91-9047467187 Email:thamizhselvan2710@gmail.com",
         "+919047467187", "thamizhselvan2710@gmail.com"),

        ("E.164 with spaced-dash",
         "Mobile: +91 - 7845745158",
         "+917845745158", ""),

        ("IDD 0091 prefix",
         "Mobile: 00919136739639 badhurudeen_a@yahoo.com",
         "+919136739639", "badhurudeen_a@yahoo.com"),

        ("IDD 0091 with dash",
         "+0091-7339618912 x@y.com",
         "+917339618912", "x@y.com"),

        ("reversed 91+ format",
         "Contact: 91+8555938482 kganesh1377@gmail.com",
         "+918555938482", "kganesh1377@gmail.com"),

        ("US E.164",
         "Mobile: +14084289952 E-Mail: NewLocation@gmail.com",
         "+14084289952", "newlocation@gmail.com"),

        ("UK format",
         "Mobile: +44 20 6366 4567 E-Mail: UKCV6366@gmail.com",
         "+442063664567", "ukcv6366@gmail.com"),

        ("inline no-space labels",
         "Phone:+91-9047510997E-Mail:ahmiltongeorge@gmail.com",
         "+919047510997", "ahmiltongeorge@gmail.com"),

        ("E.Mail-fused label",
         "E.Mail-deepa1997lakshmi@gmail.com",
         "", "deepa1997lakshmi@gmail.com"),

        ("E-Mail ID label",
         "E-Mail ID : humaneamol1998@gmail.com",
         "", "humaneamol1998@gmail.com"),

        ("spaced digits with label",
         "+91 - 98427 63108 foo@bar.in",
         "+9198427 63108".replace(" ", ""), "foo@bar.in"),

        ("multi-field inline",
         "Mobile: +91 8056884395,Mail:ananthdamodaran@gmail.com",
         "+918056884395", "ananthdamodaran@gmail.com"),

        ("tilde separator",
         "Mobile:+91 - 7358006355~E-Mail:govrajtech@gmail.com",
         "+917358006355", "govrajtech@gmail.com"),

        ("short domain @g.com",
         "mdmfdf@g.com 9876543210",
         "9876543210", "mdmfdf@g.com"),

        # ── garbage / invalid ─────────────────────────────────────────────────
        ("too-long phone (>15 digits) → reject",
         "98746555555555555555555",
         "", ""),

        ("repeated-block phone → reject",
         "98744444454545454",
         "", ""),

        ("valid 10-digit phone not rejected",
         "8321389222",
         "8321389222", ""),

        ("multi-@ email → reject",
         "Malin@@@d.com 9876543210",
         "9876543210", ""),

        ("garbage local part WWWWW → reject",
         "WWWWWWWWWWWWWSSS@g.com 9876543210",
         "9876543210", ""),

        ("invalid email Rtrtr$@.com → reject",
         "Rtrtr$@.com 343455",
         "", ""),
    ]

    passed = 0
    failed = 0
    for label, text, exp_phone, exp_email in tests:
        result = ContactExtractor.extract(text)
        got_phone = re.sub(r'\D', '', result["phone"])
        exp_phone_d = re.sub(r'\D', '', exp_phone)

        phone_ok = got_phone == exp_phone_d
        email_ok = result["email"].lower() == exp_email.lower()

        status = "PASS" if phone_ok and email_ok else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1

        if status == "FAIL":
            print(f"[{status}] {label}")
            if not phone_ok:
                print(f"       phone  got={result['phone']!r}  want={exp_phone!r}")
            if not email_ok:
                print(f"       email  got={result['email']!r}  want={exp_email!r}")
        else:
            print(f"[{status}] {label}")

    print(f"\n{passed}/{passed+failed} tests passed")





