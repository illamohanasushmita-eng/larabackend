# PostgreSQL Setup for LARA

We have configured the backend to use PostgreSQL instead of SQLite.

## Configuration
- **Database URL**: `postgresql+asyncpg://postgre:postgre@localhost:5432/lara_db`
- **Driver**: `asyncpg` (for FastAPI), `psycopg2` (for Alembic migrations)

## Status
1. `.env` file updated with connection details.
2. `requirements.txt` updated with necessary drivers.
3. `alembic/env.py` updated to support migrations.

## Verification Steps
If the automatic setup scripts ran silently, you can verify manually:

1. **Install Dependencies** (if not done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Create Database**:
   ```bash
   python create_db.py
   ```

3. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Test Connection**:
   ```bash
   python test_db_connection.py
   ```

5. **Start Server**:
   ```bash
   uvicorn app.main:app --reload
   ```
