import json

import pandas as pd

with open('user-prs.json', 'r') as f:
    data = json.loads(f.read())

flattened_data = []
for d in data:
    new_record = {
        "saml_email": d["saml_email"]
    }
    for m in d["pr_history"]:
        new_record[m["month"]] = m["n_merged"]
    flattened_data.append(new_record)

df = pd.json_normalize(flattened_data)
df = df.set_index('saml_email')
df.to_excel("prs.xlsx")
