import os

from extractor.azure_ocr import AzureOCRExtractor
from extractor.processor import ResumeProcessor
from extractor.doc_extractor import DOCExtractor
from extractor.azure_ocr_gate import AzureOCRGate
from extractor.ocr_worker import OCRWorker
from dotenv import load_dotenv

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_KEY")

RESUME_FOLDER = "resumes"

OUTPUT_NATIVE = "output/native_text"
OUTPUT_OCR = "output/ocr_required"
OUTPUT_FAILED = "output/failed"


def save_text(output_folder, original_name, text):

    os.makedirs(output_folder, exist_ok=True)

    txt_name = os.path.splitext(original_name)[0] + ".txt"
    output_path = os.path.join(output_folder, txt_name)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


def main():

    files = os.listdir(RESUME_FOLDER)

    # =========================
    # CORE OBJECTS (GLOBAL ONCE)
    # =========================

    doc_extractor = DOCExtractor()

    # 🔥 GLOBAL RATE LIMIT GATE
    ocr_gate = AzureOCRGate(requests_per_sec=2)

    # 🔥 AZURE OCR CLIENT (LOW LEVEL)
    azure_ocr = AzureOCRExtractor(
        endpoint=AZURE_ENDPOINT,
        key=AZURE_KEY,
        gate=ocr_gate
    )

    # 🔥 STEP 4 — OCR WORKER QUEUE (CRITICAL FIX)
    ocr_worker = OCRWorker(azure_ocr)

    # 🔥 PROCESSOR NOW USES WORKER (NOT DIRECT OCR CALL)
    processor = ResumeProcessor(doc_extractor, azure_ocr, ocr_worker)

    total = 0
    native_count = 0
    ocr_count = 0

    try:

        for file_name in files:

            file_path = os.path.join(RESUME_FOLDER, file_name)

            if not os.path.isfile(file_path):
                continue

            print("\n====================================")
            print(f"Processing: {file_name}")

            # =========================
            # PROCESS RESUME
            # =========================
            result = processor.process(file_path)

            status = result["status"]
            text = result["text"]

            print(f"Status: {status}")
            print(f"Text Length: {len(text)}")

            preview = text[:500].replace("\n", " ")
            print(f"\nPreview:\n{preview}")

            # =========================
            # SAVE OUTPUT
            # =========================
            if status == "native_text":

                save_text(OUTPUT_NATIVE, file_name, text)
                native_count += 1

            elif status == "ocr_text":

                save_text(OUTPUT_OCR, file_name, text)
                ocr_count += 1

            else:

                save_text(OUTPUT_FAILED, file_name, text)

            total += 1

    finally:
        doc_extractor.close()

    # =========================
    # FINAL REPORT
    # =========================
    print("\n====================================")
    print("FINAL SUMMARY")
    print(f"Total Files: {total}")
    print(f"Native Extraction: {native_count}")
    print(f"OCR Files: {ocr_count}")


if __name__ == "__main__":
    main()