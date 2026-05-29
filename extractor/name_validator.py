import re


INVALID_NAME_PATTERNS = [

    r"resume",
    r"curriculum vitae",
    r"personal details",
    r"software engineer",
    r"python developer",
    r"developer",
    r"engineer",
    r"ui/ux",
    r"designer",
    r"email",
    r"phone",
    r"mobile",
    r"address",
    r"languages",
    r"known",
    r"objective",
    r"summary",
    r"experience",
    r"education",
    r"skills"

]



import re


INVALID_NAME_TERMS = {

    # headings
    "resume",
    "cv",
    "profile",
    "summary",
    "objective",
    "career objective",
    "professional summary",
    "declaration",
    "personal details",
    "contact details",

    # role titles
    "software engineer",
    "developer",
    "ui/ux designer",
    "production officer",
    "java developer",
    "python developer",
    "data analyst",
    "accountant",

    # garbage
    "mobile",
    "email",
    "phone",
    "address",
    "curriculum vitae"
}


def is_valid_candidate_name(name):

    if not name:
        return False

    name = name.strip()

    # Remove extra spaces
    name = re.sub(
        r'\s+',
        ' ',
        name
    )

    # Too short
    if len(name) < 2:
        return False

    # Too long
    if len(name) > 60:
        return False

    lower_name = name.lower()

    # Reject obvious invalid terms
    for term in INVALID_NAME_TERMS:

        if term in lower_name:
            return False

    # Reject if contains email
    if "@" in name:
        return False

    # Reject if too numeric
    digit_count = sum(
        c.isdigit()
        for c in name
    )

    if digit_count > 3:
        return False

    # Reject weird symbols
    if re.search(
        r'[<>{}\[\]|=_~]',
        name
    ):
        return False

    # VERY IMPORTANT:
    # DO NOT force 2-word names

    return True



def clean_candidate_name(name):

    if not name:
        return ""

    # Remove emails
    name = re.sub(
        r'\S+@\S+',
        '',
        name
    )

    # Remove phone numbers
    name = re.sub(
        r'[\+\d\-\(\)\s]{7,}',
        '',
        name
    )

    # Remove leading/trailing symbols
    name = re.sub(
        r'^[^A-Za-z]+|[^A-Za-z\.]+$',
        '',
        name
    )

    # Normalize spaces
    name = re.sub(
        r'\s+',
        ' ',
        name
    )

    return name.strip()




