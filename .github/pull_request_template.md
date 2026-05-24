## Summary

-

## Verification

- [ ] `make ci`
- [ ] `make web-ci`
- [ ] `make smoke`
- [ ] `python -m ruff check src tests tools`
- [ ] `python -m ruff format --check src tests tools`
- [ ] `python -m compileall -q src tests tools`
- [ ] `PYTHONPATH=src python tools/api_smoke.py`
- [ ] `git diff --check`

## Notes

- Implemented framework scope:
  - SOC 2-oriented controls
  - NIST AI RMF
- Do not claim unsupported framework coverage without catalog entries and tests.
- Link the issue this PR closes or advances.
