Quickstart
==========

Install the SDK:

.. code-block:: bash

   pip install qdsv-qintent

Run a first intent:

.. code-block:: python

   from qintent import QIntentClient

   client = QIntentClient()

   rows = [
       {"candidate_index": 0, "score": 720, "risk_ok": True},
       {"candidate_index": 1, "score": 910, "risk_ok": True},
       {"candidate_index": 2, "score": 840, "risk_ok": False},
   ]

   result = client.run(
       'find_rows("candidate_index").where("score", ">=", 850).rank_by("score").top_k(5)',
       rows=rows,
   )

   print(result["status"])
   print(result["result"]["selected_rows"])

Explain before running:

.. code-block:: python

   passport = client.explain(
       'find_rows("candidate_index").where("score", ">=", 850).rank_by("score").top_k(5)',
       rows=rows,
   )

   plan = passport["semantic_execution_passport"]["execution_plan"]
   print(plan["selected_backend"])
   print(plan["uses_circuits"])
   print(plan["reason"])

Use a private Docker/local node when available:

.. code-block:: python

   client = QIntentClient.local()

Public informational endpoints do not require a key. Public demo deployments
may also allow small value-producing calls such as ``validate``, ``compile``,
``explain`` and ``run`` through deployment-controlled quota buckets.
