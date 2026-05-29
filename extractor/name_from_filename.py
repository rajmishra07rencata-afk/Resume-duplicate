
import os
import re


def extract_name_from_filename(filename):

    """
    Example:
    Rencata_A.RAJASEKAR_20240618133316.doc
    -> A.RAJASEKAR

    Rencata_ArchanaJadhav_20241104121429.pdf
    -> Archana Jadhav
    """

    # Remove extension
    name = os.path.splitext(filename)[0]

    # Remove timestamps
    name = re.sub(
        r'_\d{8,}$',
        '',
        name
    )

    # Remove prefix
    name = re.sub(
        r'^Rencata_',
        '',
        name,
        flags=re.IGNORECASE
    )

    # Replace underscores
    name = name.replace("_", " ")

    # Remove extra dots around initials carefully
    name = re.sub(
        r'\.(?=[A-Za-z])',
        '. ',
        name
    )

    # Split camel case
    name = re.sub(
        r'([a-z])([A-Z])',
        r'\1 \2',
        name
    )

    # Normalize spaces
    name = re.sub(
        r'\s+',
        ' ',
        name
    ).strip()

    # Remove garbage-only filenames
    if len(name) < 2:
        return ""

    return name

