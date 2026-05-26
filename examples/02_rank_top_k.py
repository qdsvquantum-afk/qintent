from qintent import QIntentClient


client = QIntentClient()

rows = [
    {"candidate_index": 0, "quality_score": 720, "risk_ok": True},
    {"candidate_index": 1, "quality_score": 910, "risk_ok": True},
    {"candidate_index": 2, "quality_score": 860, "risk_ok": False},
    {"candidate_index": 3, "quality_score": 970, "risk_ok": True},
]

source = 'find_rows("candidate_index").where("quality_score", ">=", 850).rank_by("quality_score").top_k(2)'

result = client.run(source, rows=rows)

print(result["status"])
print(result["result"]["selected_rows"])
