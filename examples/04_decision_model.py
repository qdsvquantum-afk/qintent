import os

from qintent import QIntentClient


client = QIntentClient(api_key=os.getenv("QINTENT_API_KEY") or "YOUR_QDSV_API_KEY")

rows = [
    {"candidate_index": 0, "credit_score_norm": 780, "default_score": 1000, "debt_burden_score": 900},
    {"candidate_index": 1, "credit_score_norm": 700, "default_score": 700, "debt_burden_score": 700},
    {"candidate_index": 2, "credit_score_norm": 950, "default_score": 1000, "debt_burden_score": 980},
]

source = """
find_rows("candidate_index")
  .using_decision_model([
      criterion("credit_score_norm", importance=25, priority=1),
      criterion("default_score", importance=25, priority=1),
      criterion("debt_burden_score", importance=20, priority=1),
  ])
  .accept_if(threshold=850)
  .rank()
  .top_k(10)
"""

result = client.run(source, rows=rows)

print(result["status"])
print(result["result"]["selected_rows"])
