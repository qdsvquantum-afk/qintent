import os

from qintent import QIntentClient


client = QIntentClient(api_key=os.getenv("QINTENT_API_KEY") or "YOUR_QDSV_API_KEY")

rows = [
    {"candidate_index": 0, "score": 720},
    {"candidate_index": 1, "score": 910},
    {"candidate_index": 2, "score": 840},
]

result = client.run(
    'find_rows("candidate_index").where("score", ">=", 850)',
    rows=rows,
)

print(result["status"])
print(result["result"]["selected_rows"])
