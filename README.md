# Personal Finance Tracker

A web application for tracking personal finances, transactions, and investments.

## Project Structure

```
personal-finance-tracker/
├── backend/
│   ├── app/              # FastAPI application
│   ├── scripts/          # Migration scripts
│   ├── uploads/          # Temporary file storage
│   ├── pyproject.toml    # Poetry dependencies
│   └── run.py           # Application entry point
├── frontend/            # HTML/JS frontend
├── data/                # SQLite database
└── exports/             # Generated CSV exports
```

## Setup

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install Python dependencies:**
   ```bash
   cd backend
   poetry install
   ```

3. **Run the application:**
   ```bash
   cd backend
   poetry run python run.py
   ```

   Or using uvicorn directly:
   ```bash
   cd backend
   poetry run uvicorn app.main:app --reload
   ```

3. **Access the application:**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Frontend: http://localhost:8000

## Environment Variables

Create a `.env` file in the project root (optional):
```
DATABASE_URL=sqlite:///./data/finance.db
HOST=0.0.0.0
PORT=8000
```

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Pandas
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: SQLite