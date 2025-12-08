# Contributing

Small project, small process.

1. Open an issue describing what you want to change, or what broke.
2. Keep pull requests scoped to one thing. I would rather merge three small
   patches than one that touches the encoder, the decoder and the CI file.
3. Run the suite before you push:

   ```bash
   python -m venv .venv && . .venv/bin/activate
   pip install -e ".[dev]"
   pytest -q
   ruff check .
   ```

4. If you change anything in the wire format, update `docs/PROTOCOL.md` and the
   firmware scaffold in the same pull request. A protocol that only exists in
   the Python side is a protocol that will silently disagree with the robot.

## What gets rejected

- Anything that adds a network dependency to the default path.
- Silent fallbacks: if a camera cannot be opened, the bridge should say so.
- New configuration knobs without validation and without a test.
