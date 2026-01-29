# Personal Finance Tracker

A web application for tracking personal finances, transactions, and investments.

## Project Structure

```
personal-finance-tracker/
├── backend/
│   ├── app/              # FastAPI application
│   ├── scripts/          # Migration scripts
│   ├── data/             # Raw uploaded transaction files
│   ├── pyproject.toml    # Poetry dependencies
│   └── run.py           # Application entry point
├── frontend/            # Vue 3 + Vite + TypeScript frontend
│   ├── src/             # Source files
│   │   ├── views/       # Vue page components
│   │   ├── router/      # Vue Router configuration
│   │   ├── api/         # API client
│   │   └── ...
│   ├── dist/            # Production build (generated)
│   ├── package.json     # npm dependencies
│   └── vite.config.ts   # Vite configuration
├── data/                # SQLite database
└── exports/             # Generated CSV exports
```

## Setup

### Backend Setup

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install Python dependencies:**
   ```bash
   cd backend
   poetry install
   ```

### Frontend Setup

1. **Install Node.js** (if not already installed):
   - Download from https://nodejs.org/ (LTS version recommended)

2. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```

## Development

### Running the Application

**Development Mode** (recommended for development):

1. **Start FastAPI backend:**
   ```bash
   cd backend
   poetry run uvicorn app.main:app --reload
   ```
   Backend will be available at: http://localhost:8000

2. **Start Vite dev server** (in a separate terminal):
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will be available at: http://localhost:5173
   
   The Vite dev server automatically proxies API requests to the FastAPI backend.

**Production Mode** (for testing production build):

1. **Build the frontend:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Start FastAPI backend:**
   ```bash
   cd backend
   poetry run uvicorn app.main:app
   ```
   FastAPI will serve the built frontend files from `frontend/dist/`

### Access Points

- **Development Frontend**: http://localhost:5173 (Vite dev server)
- **Production Frontend**: http://localhost:8000 (served by FastAPI)
- **API**: http://localhost:8000/api
- **API Docs**: http://localhost:8000/docs

## Environment Variables

Create a `.env` file in the project root (optional):
```
DATABASE_URL=sqlite:///./data/finance.db
HOST=0.0.0.0
PORT=8000
```

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Pandas
- **Frontend**: Vue 3, Vue Router, Vite, TypeScript, Tabulator.js (tables), Chart.js (dashboards)
- **Database**: SQLite

## Frontend Development

The frontend uses Vue 3 with Vite and TypeScript for a modern Single Page Application (SPA) experience:

- **Vue 3**: Progressive JavaScript framework with Composition API
- **Vue Router**: Client-side routing for SPA navigation
- **Hot Module Replacement (HMR)**: Instant updates during development
- **TypeScript**: Type safety and better IDE support
- **ES Modules**: Modern JavaScript module system
- **Optimized Builds**: Automatic code splitting and minification for production

### Frontend Scripts

- `npm run dev` - Start Vite dev server with HMR
- `npm run build` - Build for production (outputs to `dist/`)
- `npm run preview` - Preview production build locally

### Frontend Project Structure

- `src/main.ts` - Vue application entry point
- `src/App.vue` - Root Vue component with navigation
- `src/router/index.ts` - Vue Router configuration
- `src/views/` - Vue page components (Dashboard.vue, Edit.vue, Upload.vue)
- `src/api/client.ts` - Type-safe API client for FastAPI
- `src/types/index.ts` - TypeScript type definitions
- `src/utils/` - Utility functions
- `src/static/css/` - Stylesheets