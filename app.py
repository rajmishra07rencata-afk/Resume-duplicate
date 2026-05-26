import os
import csv

from extractor.azure_ocr import AzureOCRExtractor
from extractor.processor import ResumeProcessor
from extractor.doc_extractor import DOCExtractor
from extractor.azure_ocr_gate import AzureOCRGate
from extractor.ocr_worker import OCRWorker
from extractor.contact_extractor import ContactExtractor
from dotenv import load_dotenv

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_KEY")

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
# Only 3 columns: filename, email, phone
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
            fieldnames=["filename", "email", "phone"]
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
            fieldnames=["filename", "email", "phone"]
        )

        writer.writerow(row)


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

    # =========================================
    # INIT CSV — fresh file every run
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
        email  = ""
        phone  = ""

        try:

            result = processor.process(
                file_path
            )

            status = result.get("status", "failed")
            text   = result.get("text", "")
            reason = result.get("reason", "")
            stage  = result.get("stage", "")

            print(f"Status     : {status}")
            print(f"Text Length: {len(text)}")

            if reason:
                print(f"Failure Reason: {reason}")

            if stage:
                print(f"Failed Stage  : {stage}")

            # =========================================
            # EXTRACT EMAIL & PHONE
            # =========================================

            if text:

                contacts = ContactExtractor.extract(text)

                email = contacts["email"]
                phone = contacts["phone"]

                print(f"Email : {email or 'NOT FOUND'}")
                print(f"Phone : {phone or 'NOT FOUND'}")

            preview = text[:500].replace("\n", " ")
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
        # APPEND TO CSV
        # Skip failed and fatal_error files
        # Only save when text was extracted
        # =========================================

        if status in ("native_text", "ocr_text"):

            append_csv(OUTPUT_CSV, {
                "filename": file_name,
                "email"   : email,
                "phone"   : phone
            })

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