import csv
import os
import webbrowser
import subprocess
import sys

# Paths (adjust if needed)
RESUME_DIR = "resumes"
CONTACTS_FILE = "contacts.csv"
FILES_BASE_DIR = "output"  # where original files are
TEXT_DIR = os.path.join(FILES_BASE_DIR, "native_text")

# Function to detect missing values
def has_missing(row):
    return any(v is None or str(v).strip() == "" for v in row.values())

# Function to open file with appropriate program
def open_file(filepath):
    if not os.path.exists(filepath):
        print(f"[WARNING] File not found: {filepath}")
        return

    ext = os.path.splitext(filepath)[1].lower()

    try:
        # Web-viewable formats
        if ext in [".html", ".htm", ".pdf"]:
            webbrowser.open(f"file://{os.path.abspath(filepath)}")

        # Images / text / others → OS default
        elif sys.platform.startswith("win"):
            os.startfile(filepath)
        elif sys.platform.startswith("darwin"):
            subprocess.run(["open", filepath])
        else:  # Linux
            subprocess.run(["xdg-open", filepath])

    except Exception as e:
        print(f"[ERROR] Could not open {filepath}: {e}")


def main():
    rows_with_missing = []

    # Read CSV
    with open(CONTACTS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if has_missing(row):
                rows_with_missing.append(row)

    print(f"Found {len(rows_with_missing)} rows with missing values.\n")

    for idx, row in enumerate(rows_with_missing, start=1):
        print(f"\n=== File {idx} ===")

        # Assuming CSV has a column named 'filename'
        filename = row.get("filename")

        if not filename:
            print("[WARNING] Missing 'filename' column value")
            continue

        original_path = os.path.join(RESUME_DIR, filename)

        # Construct corresponding txt path
        base_name = os.path.splitext(filename)[0] + ".txt"
        txt_path = os.path.join(TEXT_DIR, base_name)

        print(f"Opening original: {original_path}")
        open_file(original_path)

        print(f"Opening text file: {txt_path}")
        open_file(txt_path)

        # Wait for user input
        user_input = input("\nPress ENTER for next, 'q' to quit: ").strip().lower()
        if user_input == "q":
            print("Exiting...")
            break


if __name__ == "__main__":
    main()