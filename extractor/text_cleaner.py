import re


class TextCleaner:

    # =========================================
    # MAIN PIPELINE
    # =========================================

    @staticmethod
    def clean(text):

        if not text:
            return ""

        text = TextCleaner._fix_encoding(text)
        text = TextCleaner._fix_broken_words(text)       # BEFORE header fix
        text = TextCleaner._remove_duplicate_lines(text)
        text = TextCleaner._fix_sequence_repetitions(text)
        text = TextCleaner._fix_word_repetitions(text)
        text = TextCleaner._clean_whitespace(text)
        text = TextCleaner._fix_section_headers(text)    # LAST

        return text.strip()

    # =========================================
    # STEP 1 — FIX ENCODING
    # =========================================

    @staticmethod
    def _fix_encoding(text):

        replacements = {
            "\u2019": "'",  "\u2018": "'",
            "\u201c": '"',  "\u201d": '"',
            "\u2013": "-",  "\u2014": "-",
            "\u2022": "*",  "\u00a0": " ",
            "\u00b7": "*",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    # =========================================
    # STEP 2 — FIX BROKEN WORDS
    #
    # DOCX sometimes splits words across lines:
    # "Experience\nd test engineer"
    #   → "Experienced test engineer"
    #
    # Detects: line ending with a word +
    # next line starting with a short lowercase
    # suffix (d, ed, ing, ly, er, s etc.)
    # =========================================

    WORD_SUFFIXES = re.compile(
        r"^(d|ed|ing|er|ly|es|s|al|tion|ment)\b",
        re.IGNORECASE
    )

    @staticmethod
    def _fix_broken_words(text):

        lines  = text.split("\n")
        result = []
        i      = 0

        while i < len(lines):

            line = lines[i]

            if (
                i + 1 < len(lines)
                and line.strip()
                and lines[i + 1].strip()
            ):

                next_line = lines[i + 1].strip()

                # Next line starts with a word suffix
                if TextCleaner.WORD_SUFFIXES.match(next_line):

                    # Merge: no space (broken mid-word)
                    result.append(
                        line.rstrip() + next_line
                    )

                    i += 2
                    continue

            result.append(line)
            i += 1

        return "\n".join(result)

    # =========================================
    # STEP 3 — REMOVE DUPLICATE LINES
    #
    # Removes exact duplicate lines.
    # Keeps first occurrence.
    # =========================================

    @staticmethod
    def _remove_duplicate_lines(text):

        lines  = text.split("\n")
        seen   = set()
        result = []

        for line in lines:

            key = re.sub(r"\s+", " ", line.strip().lower())

            if not key:
                result.append("")
                continue

            if key not in seen:
                seen.add(key)
                result.append(line)

        return "\n".join(result)

    # =========================================
    # STEP 4 — FIX SEQUENCE REPETITIONS
    #
    # Fixes: "work along work along" → "work along"
    # Fixes: "a progressive a progressive" → "a progressive"
    #
    # Works by detecting repeated word sequences
    # at the start of each line using a sliding
    # chunk window.
    # =========================================

    @staticmethod
    def _fix_sequence_repetitions(text):

        lines  = text.split("\n")
        result = []

        for line in lines:
            result.append(
                TextCleaner._dedupe_word_sequence(line)
            )

        return "\n".join(result)

    @staticmethod
    def _dedupe_word_sequence(line):

        words = line.split()

        if len(words) < 2:
            return line

        changed = True

        while changed:

            changed = False
            n       = len(words)

            for chunk_size in range(1, n // 2 + 1):

                chunk = words[:chunk_size]
                rest  = words[chunk_size:]

                if rest[:chunk_size] == chunk:

                    words   = chunk + rest[chunk_size:]
                    changed = True
                    break

        return " ".join(words)

    # =========================================
    # STEP 5 — FIX WORD REPETITIONS
    #
    # "TeamTeam"    → "Team"
    # "playerplayer"→ "player"
    # "Team Team"   → "Team"
    # =========================================

    @staticmethod
    def _fix_word_repetitions(text):

        lines  = text.split("\n")
        result = []

        for line in lines:

            # CamelCase repetition: "TeamTeam" → "Team"
            line = re.sub(
                r"\b([A-Z][a-z]+|[A-Z]{2,})\1\b",
                r"\1",
                line
            )

            # Space-separated repetition: "Team Team" → "Team"
            line = re.sub(
                r"\b(\w+)(\s+\1)+\b",
                r"\1",
                line,
                flags=re.IGNORECASE
            )

            result.append(line)

        return "\n".join(result)

    # =========================================
    # STEP 6 — CLEAN WHITESPACE
    # =========================================

    @staticmethod
    def _clean_whitespace(text):

        # Multiple spaces → single
        text = re.sub(r" {2,}", " ", text)

        # More than 2 newlines → 2
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip trailing spaces per line
        lines = [line.rstrip() for line in text.split("\n")]

        return "\n".join(lines)

    # =========================================
    # STEP 7 — FIX SECTION HEADERS
    #
    # KEY FIX: use (?<![A-Za-z]) and (?![A-Za-z])
    #
    # OLD broken regex: (?<!\n)EXPERIENCE(?!\n)
    #   → breaks "Experienced" into "Experience\nd"
    #
    # NEW fixed regex: (?<![A-Za-z])EXPERIENCE(?![A-Za-z])
    #   → "Experienced": next char is 'd' (letter) → NO MATCH ✓
    #   → "EXPERIENCE"  standalone → MATCH ✓
    # =========================================

    SECTION_HEADERS = [
        "SUMMARY", "OBJECTIVE", "CAREER OBJECTIVE",
        "PROFESSIONAL SUMMARY", "PROFILE",
        "EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT",
        "EDUCATION", "ACADEMIC",
        "SKILLS", "TECHNICAL SKILLS", "KEY SKILLS",
        "CORE COMPETENCIES", "SKILL HIGHLIGHTS",
        "PROJECTS", "PROJECT EXPERIENCE",
        "CERTIFICATIONS", "ACHIEVEMENTS", "AWARDS",
        "LANGUAGES", "CONTACT", "REFERENCES",
        "PUBLICATIONS", "INTERNSHIP", "TRAINING",
        "HOBBIES", "INTERESTS",
        "ROLES AND RESPONSIBILITIES",
        "PROFESSIONAL EXPERIENCE",
        "ADDITIONAL INFORMATION",
        "PERSONAL INFORMATION",
        "SOCIAL LINKS",
    ]

    @staticmethod
    def _fix_section_headers(text):

        for header in TextCleaner.SECTION_HEADERS:

            pattern = (
                r"(?<![A-Za-z])("
                + re.escape(header)
                + r")(?![A-Za-z])"
            )

            text = re.sub(
                pattern,
                r"\n\1\n",
                text,
                flags=re.IGNORECASE
            )

        text = re.sub(r"\n{3,}", "\n\n", text)

        return text