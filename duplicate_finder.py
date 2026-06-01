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
