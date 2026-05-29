import os
import csv
import re

from extractor.azure_ocr import AzureOCRExtractor
from extractor.processor import ResumeProcessor
from extractor.doc_extractor import DOCExtractor
from extractor.azure_ocr_gate import AzureOCRGate
from extractor.ocr_worker import OCRWorker
from extractor.contact_extractor import ContactExtractor
from extractor.llm_extractor import LLMExtractor
from extractor.name_validator import (is_valid_candidate_name, clean_candidate_name)
from extractor.name_from_filename import (extract_name_from_filename)

from dotenv import load_dotenv

load_dotenv()


# =========================================
# ENV VARIABLES
# =========================================

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_KEY")
GROQ_API_KEYS = os.getenv("GROQ_API_KEYS","").split(",")


# =========================================
# PATHS
# =========================================

RESUME_FOLDER = "resumes"

OUTPUT_NATIVE = "output/native_text"
OUTPUT_OCR    = "output/ocr_required"
OUTPUT_FAILED = "output/failed"
OUTPUT_CSV    = "output/contacts.csv"


# =========================================
# SAVE TEXT FILE
# =========================================

def save_text(output_folder, original_name, text):

    os.makedirs(output_folder, exist_ok=True)

    txt_name = os.path.splitext(
        original_name
    )[0] + ".txt"

    output_path = os.path.join(
        output_folder,
        txt_name
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(text)


# =========================================
# CSV HELPERS
# =========================================

def init_csv(csv_path):

    os.makedirs(
        os.path.dirname(csv_path),
        exist_ok=True
    )

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "filename",
                "candidate_name",
                "email",
                "phone"
            ]
        )

        writer.writeheader()


def append_csv(csv_path, row):

    with open(
        csv_path,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "filename",
                "candidate_name",
                "email",
                "phone"
            ]
        )

        writer.writerow(row)


# =========================================
# CLEAN TEXT
# =========================================

def clean_text(text):

    # Remove control characters
    text = re.sub(
        r'[\x00-\x1F\x7F]',
        ' ',
        text
    )

    # Remove excessive spaces
    text = re.sub(
        r'[ \t]+',
        ' ',
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r'\n{3,}',
        '\n\n',
        text
    )

    return text.strip()



# =========================================
# PHONE VALIDATION
# =========================================

def validate_phone(phone):

    if not phone:
        return ""

    digits_only = re.sub(
        r"\D",
        "",
        phone
    )

    if len(digits_only) < 10:
        return ""

    return phone


# =========================================
# MAIN
# =========================================

def main():

    # =========================================
    # IGNORE TEMP WORD FILES
    # =========================================

    files = [
        f for f in os.listdir(RESUME_FOLDER)
        if not f.startswith("~$")
    ]

    # =========================================
    # CORE OBJECTS
    # =========================================

    doc_extractor = DOCExtractor()

    ocr_gate = AzureOCRGate(
        requests_per_sec=2
    )

    azure_ocr = AzureOCRExtractor(
        endpoint=AZURE_ENDPOINT,
        key=AZURE_KEY,
        gate=ocr_gate
    )

    ocr_worker = OCRWorker(
        azure_ocr
    )

    processor = ResumeProcessor(
        doc_extractor,
        azure_ocr,
        ocr_worker
    )

    llm = LLMExtractor(
        api_keys=GROQ_API_KEYS
    )

    # =========================================
    # INIT CSV
    # =========================================

    init_csv(OUTPUT_CSV)

    # =========================================
    # COUNTERS
    # =========================================

    total        = 0
    native_count = 0
    ocr_count    = 0
    failed_count = 0

    # =========================================
    # PROCESS FILES
    # =========================================

    for file_name in files:

        file_path = os.path.join(
            RESUME_FOLDER,
            file_name
        )

        if not os.path.isfile(file_path):
            continue

        print("\n====================================")
        print(f"Processing: {file_name}")

        status = "failed"

        email = ""
        phone = ""
        candidate_name = ""

        try:

            # =========================================
            # PROCESS RESUME
            # =========================================

            result = processor.process(
                file_path
            )

            status = result.get(
                "status",
                "failed"
            )

            text = result.get(
                "text",
                ""
            )

            reason = result.get(
                "reason",
                ""
            )

            stage = result.get(
                "stage",
                ""
            )

            print(f"Status     : {status}")
            print(f"Text Length: {len(text)}")

            if reason:
                print(f"Failure Reason: {reason}")

            if stage:
                print(f"Failed Stage  : {stage}")

            # =========================================
            # CLEAN TEXT
            # =========================================

            if text:

                text = clean_text(text)

            # =========================================
            # EXTRACTION
            # =========================================

            if text:

                # =========================================
                # REGEX EXTRACTION
                # =========================================

                contacts = ContactExtractor.extract(
                    text
                )

                email = contacts.get(
                    "email",
                    ""
                )

                phone = contacts.get(
                    "phone",
                    ""
                )

                # Validate phone
                phone = validate_phone(phone)

                print(
                    f"Regex Email : "
                    f"{email or 'NOT FOUND'}"
                )

                print(
                    f"Regex Phone : "
                    f"{phone or 'NOT FOUND'}"
                )

                # =========================================
                # LLM EXTRACTION
                # =========================================

                needs_llm = False

                if not email:
                    needs_llm = True

                if not phone:
                    needs_llm = True

                # Always use LLM for candidate name
                needs_llm = True

                if needs_llm:

                    print(
                        "Using LLM extraction..."
                    )

                    try:

                        llm_data = llm.extract(text)

                        # =========================================
                        # CANDIDATE NAME
                        # =========================================

                        
                        candidate_name = llm_data.get(
                            "candidate_name",
                            ""
                        )
                        
                        # =====================================
                        # FILENAME FALLBACK
                        # =====================================

                        if not candidate_name:

                            candidate_name = (
                                extract_name_from_filename(
                                    file_name
                                )
                            )

                            print(
                                f"[FILENAME FALLBACK] "
                                f"{candidate_name}"
                            )
                        


                        candidate_name = clean_candidate_name(
                            candidate_name
                        )



                        # Validate candidate name
                        if not is_valid_candidate_name(
                            candidate_name
                        ):
                            candidate_name = ""

                        # =========================================
                        # EMAIL FALLBACK
                        # =========================================

                        if not email:

                            email = llm_data.get(
                                "email",
                                ""
                            )

                        # =========================================
                        # PHONE FALLBACK
                        # =========================================

                        if not phone:

                            phone = llm_data.get(
                                "phone_number",
                                ""
                            )

                            phone = validate_phone(
                                phone
                            )

                        print(
                            f"LLM Name : "
                            f"{candidate_name or 'NOT FOUND'}"
                        )

                    except Exception as e:

                        print(f"[LLM ERROR] {e}")

            # =========================================
            # PREVIEW
            # =========================================

            preview = text[:500]

            print(f"\nPreview:\n{preview}")

            # =========================================
            # SAVE TEXT OUTPUT
            # =========================================

            if status == "native_text":

                save_text(
                    OUTPUT_NATIVE,
                    file_name,
                    text
                )

                native_count += 1

            elif status == "ocr_text":

                save_text(
                    OUTPUT_OCR,
                    file_name,
                    text
                )

                ocr_count += 1

            else:

                failed_content = f"""
STATUS:
{status}

FAILED STAGE:
{stage}

FAILURE REASON:
{reason}

====================================

PARTIAL TEXT:

{text}
"""

                save_text(
                    OUTPUT_FAILED,
                    file_name,
                    failed_content
                )

                failed_count += 1

            total += 1

        except Exception as e:

            print(f"[FATAL ERROR] {e}")

            failed_content = f"""
STATUS:
fatal_error

FAILURE REASON:
{str(e)}
"""

            save_text(
                OUTPUT_FAILED,
                file_name,
                failed_content
            )

            status = "fatal_error"

            failed_count += 1

        # =========================================
        # APPEND CSV
        # =========================================

        if status in (
            "native_text",
            "ocr_text"
        ):

            append_csv(
                OUTPUT_CSV,
                {
                    "filename"       : file_name,
                    "candidate_name" : candidate_name,
                    "email"          : email,
                    "phone"          : phone
                }
            )

    # =========================================
    # FINAL SUMMARY
    # =========================================

    print("\n====================================")
    print("FINAL SUMMARY")

    print(f"Total Files      : {total}")
    print(f"Native Extraction: {native_count}")
    print(f"OCR Files        : {ocr_count}")
    print(f"Failed Files     : {failed_count}")

    print(f"CSV saved to     : {OUTPUT_CSV}")


if __name__ == "__main__":
    main()