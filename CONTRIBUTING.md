# Contributing To QIntent

Thanks for helping improve QIntent.

This repository is a Developer Preview for the public Python SDK, examples, notebooks, grammar notes and documentation.

## Good Contributions

- Bug reports with minimal reproducible examples.
- Documentation improvements.
- New examples using the public preview grammar.
- Notebook improvements.
- Clear reports of confusing error messages.
- Suggestions for bounded, auditable semantic operations.

## Out Of Scope

- Requests to expose QDSV Runtime internals.
- Requests for private backend adapters or credentials.
- Arbitrary Python execution.
- Unbounded workloads or bulk private data processing through the public preview.

## Development

```bash
pip install -e .
python -m pytest
```

Before opening an issue, please include:

- package version;
- Python version;
- API endpoint used;
- minimal QIntent source;
- small sample rows if needed;
- expected result;
- actual result or traceback.
