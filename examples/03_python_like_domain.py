from qintent import QIntentClient


client = QIntentClient()

source = """
x = domain(0, 15)
score = clip(round(max(x, 0)), 0, 10)
find(x).where(all([score >= 7, score <= 9, x not in [8]])).rank_by(score).top_k(3)
"""

compiled = client.compile(source)
executed = client.run(source)

print(compiled["compiled_summary"])
print(executed["status"])
print(executed["result"].get("ranked_candidates"))
