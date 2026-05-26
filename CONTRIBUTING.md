# Contributing

Thanks for considering a contribution.

## Getting started

```bash
git clone https://github.com/apratamaa516/mimo-multilang-bridge.git
cd mimo-multilang-bridge
python -m venv .venv
. .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
pip install pytest pytest-asyncio ruff

# Configure MiMo credentials
cp .env.example .env
# Edit .env with your MIMO_API_KEY

# Run tests
pytest tests/ -v

# Run the API locally
uvicorn src.main:app --reload --port 8000
# Visit http://localhost:8000/docs
```

## Pull request workflow

1. Fork the repo and create a topic branch from `main`
2. Make changes — keep commits focused and atomic
3. Add or update tests in `tests/`
4. Run `ruff check src/ tests/` and `pytest tests/` locally
5. Open a PR with a clear description of what changed and why

## Code style

- Python 3.11+
- Format with ruff (default config)
- Type hints encouraged but not required for first draft
- Docstrings on public functions

## Reporting issues

Open a GitHub issue with:
- What you tried
- What happened (full error trace if any)
- What you expected
- Your environment (OS, Python version, MiMo plan tier)
