QIntent
=======

QIntent is the native intent-first language for **QDSV - Quantum Declarative
Semantic Value**. It lets users declare computational intent over rows, state
spaces, predicates, rankings, prepared values, evidence, and decision
workflows without starting by writing circuits.

The public SDK is intentionally lightweight: users write QIntent, submit it to
the QDSV public API or a configured private node, and receive validation,
compilation, explanation, execution results, and semantic execution evidence.

.. grid:: 1 1 2 2
   :gutter: 2

   .. grid-item-card:: Intent-first workflow
      :link: concepts
      :link-type: doc

      Declare what the problem means before choosing a backend-specific
      execution form.

   .. grid-item-card:: Python SDK
      :link: quickstart
      :link-type: doc

      Install ``qdsv-qintent`` and run small public-preview examples from
      Python.

   .. grid-item-card:: QIntent to Bridge to Qiskit
      :link: bridge_qiskit
      :link-type: doc

      Use QIntent upstream and QDSV Bridge when a workflow needs an
      OpenQASM/Qiskit-oriented artifact.

   .. grid-item-card:: Public scope
      :link: public_scope
      :link-type: doc

      Understand what is public, what is intentionally private, and where the
      preview boundaries are.

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   quickstart
   concepts
   bridge_qiskit
   public_scope
   api
   GitHub <https://github.com/qdsvquantum-afk/qintent>

Project links
-------------

* `GitHub repository <https://github.com/qdsvquantum-afk/qintent>`_
* `PyPI package <https://pypi.org/project/qdsv-qintent/>`_
* `QDSV Cloud <https://qdsv.cloud/>`_
* `Qruba Cloud <https://cloud.qruba.site/>`_
