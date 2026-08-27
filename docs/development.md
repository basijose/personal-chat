# Development

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --port 8000
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Notes

- Si `OPENAI_API_KEY` no está presente, se usa `MockLLMProvider`.
- Para pruebas, el backend se puede apuntar a SQLite usando `DATABASE_URL`.

