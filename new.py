import os

input_dir = "regex"   # folder containing files
output_file = "combined.txt" # output file

separator = "\n\n----- FILE SEPARATOR -----\n\n"

with open(output_file, "w", encoding="utf-8") as outfile:
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)

        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as infile:
                outfile.write(f"File: {filename}\n")  # optional header
                outfile.write(infile.read())
                outfile.write(separator)

print("Done!")