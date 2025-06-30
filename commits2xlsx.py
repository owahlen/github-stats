import json
import pandas as pd

def convert_commits_to_excel(json_file, excel_file):
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        commit_data = json.load(f)

    # Convert to DataFrame
    df = pd.json_normalize(commit_data)

    # Convert date columns to Europe/Berlin time (Excel-safe format)
    for col in ['authored_date', 'committed_date']:
        if col in df.columns:
            df[col] = (
                pd.to_datetime(df[col], utc=True, errors='coerce')         # Parse as UTC
                .dt.tz_convert('Europe/Berlin')                            # Convert to Berlin time
                .dt.tz_localize(None)                                      # Strip tz info for Excel
            )

    # Optional: Reorder columns
    columns_order = [
        "repository",
        "author",
        "author_email",
        "authored_date",
        "committed_date",
        "commit_sha",
        "message",
        "changed_files",
        "additions",
        "deletions",
        "url"
    ]
    df = df[[col for col in columns_order if col in df.columns]]

    # Write to Excel
    df.to_excel(excel_file, index=False)
    print(f"✅ Saved {len(df)} commits to {excel_file}")

if __name__ == "__main__":
    convert_commits_to_excel("commits.json", "commits.xlsx")
