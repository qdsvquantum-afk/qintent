# Changelog

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

- Initial QIntent Developer Preview SDK, CLI, examples and documentation.
