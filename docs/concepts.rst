Concepts
========

QIntent starts from intent rather than circuits:

.. code-block:: text

   problem intent
   -> semantic representation
   -> state space / operation / predicate / relation
   -> execution route
   -> evidence

What QIntent is
---------------

* A Python SDK and declarative language for bounded QDSV-native intent.
* A way to validate, compile, explain and run small public-preview examples.
* A developer entry point into QDSV and Qruba workflows.
* A public surface for predicates, rankings, domains, prepared signals,
  decision declarations and semantic execution evidence.

What QIntent is not
-------------------

* It is not the private QDSV Runtime.
* It is not an unrestricted Python execution environment.
* It is not a local QuEST, Aer or IBM installation.
* It does not expose backend selection internals, lowering logic, private
  formulas, credentials, secrets, or production orchestration.

Default narrative
-----------------

.. code-block:: text

   QIntent -> QDSV -> semantic/statevector route -> evidence

Circuit materialization is not the required starting point. It appears only
when an enabled backend or handoff workflow requires a circuit-oriented
artifact.
