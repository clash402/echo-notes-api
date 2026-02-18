# Developer Setup

## 1. Install dependencies

```bash
python3 -m pip install --upgrade pip
pip install -e ".[dev]"
```

## 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set provider values for your target environment. See:
`docs/guides/provider-setup.md`.

## 3. Run API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

## 4. Run tests

```bash
pytest
```
