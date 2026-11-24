# Changelog

## 0.3.0 - 2026-11-24

- Promote the public QIntent contract to ``qintent_public.v1``.
- Align public service metadata and documentation with the QIntent product
  surface instead of a preview release channel.
- Keep backend and execution limits explicit per capability and provider.

## 0.2.3 - 2026-11-19

- Add per-job hardware optimization profiles: baseline, balanced and advanced.
- Make SDK hardware status reads storage-backed by default; live provider
  polling is opt-in with live_poll=True.
- Document the shared QIntent/Qruba hardware path and profile evidence.

## 0.2.2 - 2026-09-11

- Exposes ``divmod(value, divisor)`` in the public canonical QIntent operation
  catalog as the bounded quotient/remainder multi-output helper.
- Documents quotient/remainder pair comparison through canonical QDSV
  predicates, for example ``eq(divmod(x, 3), [2, 1])``.

## 0.2.1 - 2026-09-02

- Updates the public canonical capability catalog to 45 operations.
- Documents ``select_if(predicate, value_if_true, value_if_false)`` as the
  bounded conditional selection helper shared with QDSV Operation Compiler v2.

## 0.2.0 - 2026-07-16

- Publish the exact 43-operation QDSV canonical capability catalog.
- Add flat and hierarchical ScoreModel v2 examples.
- Add capability discovery and safe IBM hardware preflight/submission methods.
- Add CLI commands for capabilities and hardware job lifecycle operations.
- Retire legacy scoring spellings from the public language surface.

## 0.1.0

- Initial public QIntent SDK, CLI, examples and documentation.
