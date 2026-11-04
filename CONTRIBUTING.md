# Contributing

Thanks for considering a contribution.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

## Pull requests

- Explain the user problem and the behavior change.
- Add tests for new behavior and regression fixes.
- Keep the core local-first and network-free unless a proposal is discussed first.
- Never include real prompts, API keys, tokens, customer data, or private repository content in tests.
- Do not describe estimated token costs as provider-billed amounts.
- Document data collection and retention changes explicitly.

## Good first contributions

- Improve CSV export tests.
- Add CLI tests for invalid arguments.
- Add synthetic fixtures for import formats.
- Improve cross-platform Git path handling.
- Clarify documentation and examples.
