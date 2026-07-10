QIntent to Bridge to Qiskit
===========================

QIntent can act as an upstream intent layer for QDSV Bridge when a workflow
needs to end in a Qiskit-oriented artifact.

.. code-block:: text

   QIntent source
   -> QDSV semantic validation
   -> QDSV Bridge specification
   -> OpenQASM artifact
   -> Qiskit-oriented workflow
   -> reproducibility report

This keeps QIntent positioned as the problem-intent language while QDSV Bridge
handles the semantic-to-OpenQASM/Qiskit handoff.

Related guide
-------------

See the repository guide:

* ``docs/integrations/qintent_bridge_qiskit.md``

Bridge documentation:

* `QDSV Bridge docs <https://qdsvquantum-afk.github.io/qdsv-bridge/>`_
