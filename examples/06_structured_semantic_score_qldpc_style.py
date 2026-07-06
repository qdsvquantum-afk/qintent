import os

from qintent import QIntentClient


client = QIntentClient(api_key=os.getenv("QINTENT_API_KEY"))

# Toy qLDPC-style post-decoding candidates.
# Values are prepared on a 0..1000 scale before entering QIntent.
rows = [
    {
        "candidate_index": 0,
        "syndrome_support": 930,
        "check_consistency": 900,
        "logical_preservation": 820,
        "distance_safety": 830,
        "decoder_confidence": 850,
        "propagation_safety": 820,
        "syndrome_risk": 50,
        "logical_risk": 120,
        "syndrome_entropy_adjustment": -10,
    },
    {
        "candidate_index": 1,
        "syndrome_support": 940,
        "check_consistency": 880,
        "logical_preservation": 720,
        "distance_safety": 700,
        "decoder_confidence": 870,
        "propagation_safety": 760,
        "syndrome_risk": 80,
        "logical_risk": 260,
        "syndrome_entropy_adjustment": -20,
    },
    {
        "candidate_index": 2,
        "syndrome_support": 890,
        "check_consistency": 910,
        "logical_preservation": 930,
        "distance_safety": 910,
        "decoder_confidence": 830,
        "propagation_safety": 890,
        "syndrome_risk": 30,
        "logical_risk": 40,
        "syndrome_entropy_adjustment": 15,
    },
]

source = """
find_rows("candidate_index")
  .using_structured_semantic_score([
      block("syndrome", [
          signal("syndrome_support", influence=30, priority=2),
          signal("check_consistency", influence=20, priority=1),
      ], influence=30, priority=2, risk_adjustment="syndrome_risk", adjustments=[
          adjustment("syndrome_entropy_adjustment", influence=5),
      ]),
      block("logical_safety", [
          signal("logical_preservation", influence=40, priority=3),
          signal("distance_safety", influence=20, priority=2),
      ], influence=40, priority=3, risk_adjustment="logical_risk"),
      block("decoder", [
          signal("decoder_confidence", influence=25, priority=1),
          signal("propagation_safety", influence=15, priority=2),
      ], influence=30, priority=1),
  ], global_risk="logical_risk", profile="qldpc_post_decoding")
  .accept_if(threshold=600)
  .rank()
  .top_k(2)
"""

passport = client.explain(source, rows=rows)
result = client.run(source, rows=rows)

print(passport["semantic_execution_passport"]["predicate"])
print(result["status"])
print(result["result"]["selected_rows"])
