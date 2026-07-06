from qintent import QIntentClient


client = QIntentClient()

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
