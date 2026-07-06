from qintent import QIntentClient


client = QIntentClient()

# Toy qLDPC-style correction candidates.
# Values are prepared on a 0..1000 scale before entering QIntent.
rows = [
    {
        "candidate_index": 0,
        "syndrome_support": 920,
        "logical_preservation": 860,
        "decoder_confidence": 810,
        "propagation_safety": 830,
        "distance_safety": 850,
        "logical_risk": 80,
    },
    {
        "candidate_index": 1,
        "syndrome_support": 910,
        "logical_preservation": 700,
        "decoder_confidence": 840,
        "propagation_safety": 730,
        "distance_safety": 720,
        "logical_risk": 220,
    },
    {
        "candidate_index": 2,
        "syndrome_support": 870,
        "logical_preservation": 910,
        "decoder_confidence": 820,
        "propagation_safety": 880,
        "distance_safety": 900,
        "logical_risk": 40,
    },
]

source = """
find_rows("candidate_index")
  .using_semantic_score([
      signal("syndrome_support", influence=30, priority=2),
      signal("logical_preservation", influence=30, priority=3),
      signal("decoder_confidence", influence=20, priority=1),
      signal("propagation_safety", influence=10, priority=2),
      signal("distance_safety", influence=10, priority=3),
  ], risk_adjustment="logical_risk")
  .accept_if(threshold=780)
  .rank()
  .top_k(2)
"""

passport = client.explain(source, rows=rows)
result = client.run(source, rows=rows)

print(passport["semantic_execution_passport"]["predicate"])
print(result["status"])
print(result["result"]["selected_rows"])
