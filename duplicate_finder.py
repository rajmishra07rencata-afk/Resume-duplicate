import pandas as pd


df = pd.read_csv("output/contacts.csv", dtype={"phone": str})

df["phone"] = df["phone"].str.replace(r"\.0$", "", regex=True)


df = df.replace("", pd.NA)


def dup_ignore_null(series):
    return series.notna() & series.duplicated(keep="first")

dup_mask = (
    dup_ignore_null(df["filename"]) |
    dup_ignore_null(df["email"]) |
    dup_ignore_null(df["phone"])
)


duplicates_df = df[dup_mask]
clean_df = df[~dup_mask]

duplicates_df.to_csv("duplicates.csv", index=False)
clean_df.to_csv("clean.csv", index=False)
print("phone: ", df["phone"].isna().sum())
print("email: ", df["email"].isna().sum())
print("both null: ", df[df["phone"].isna() & df["email"].isna()].shape[0])

import os

missing_both_df = df[df["phone"].isna() & df["email"].isna()]
filenames = missing_both_df["filename"].dropna().unique()

text_folder = "output/native_text"
output_file = "combined_missing_texts.txt"

all_texts = []

for fname in filenames:
    base_name = os.path.splitext(fname)[0]
    txt_path = os.path.join(text_folder, base_name + ".txt")

    separator = "\n" + "="*80 + "\n"

    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            all_texts.append(f"{separator}FILE: {fname}\n{separator}{content}")
    else:
        all_texts.append(f"{separator}FILE: {fname} (NOT FOUND){separator}")

with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(all_texts))

print(f"✅ Combined text file created: {output_file}")

