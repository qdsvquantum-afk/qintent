Public Scope
============

The public QIntent repository includes:

* Python SDK package ``qdsv-qintent``.
* CLI command ``qintent``.
* Public examples and notebooks.
* Public preview grammar notes.
* Documentation for using QIntent through the QDSV public API.
* QIntent Explain and Semantic Execution Passport outputs.
* Controlled helper operations for prepared values and small examples.

Not included
------------

The following are intentionally not included:

* QDSV Runtime.
* Backend selector internals.
* Lowering and materialization internals.
* QuEST, Aer, IBM or hardware adapters.
* Noise mitigation internals.
* Crypto internals.
* Private endpoints, secrets, keys, tokens, production deployment
  configuration, or private decision formulas.

Positioning
-----------

QIntent is the public language and SDK layer. QDSV is the underlying semantic
computation model and runtime. Qruba is the visual platform built on top of
QDSV.

The public preview exposes a bounded subset first. That should not be read as
the ceiling of QDSV.
