## What this changes

## How it was tested

- [ ] `pytest -q` passes locally
- [ ] `ruff check .` is clean
- [ ] the synthetic run still works: `python -m fruitfly_brain.main --source mock --frames 30 --no-journal`

## Notes for the reviewer

Anything here that touches `protocol.py` or the stop rule needs a sentence about
what happens when the other side misbehaves.
