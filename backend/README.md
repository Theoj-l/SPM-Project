# SPM Backend API

FastAPI backend for SPM Frontend application with organized structure for team development.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── database.py            # Database setup
│   ├── middleware.py          # Custom middleware
│   ├── models/                # Pydantic models
│   │   ├── __init__.py
│   │   ├── base.py           # Base response models
│   │   └── item.py           # Item-specific models
│   ├── routers/              # API route handlers
│   │   ├── __init__.py
│   │   ├── health.py         # Health check routes
│   │   └── items.py          # Item CRUD routes
│   └── services/             # Business logic layer
│       ├── __init__.py
│       └── item_service.py   # Item business logic
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
└── README.md
```

## Setup

1. **Create virtual environment:**

   ```bash
   cd backend
   python -m venv venv
   ```

2. **Activate virtual environment:**

   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server:**
   ```bash
   python main.py
   ```

### Adding New Features

1. Create model in `app/models/`
2. Create service in `app/services/`
3. Create router in `app/routers/`
4. Import and include in `main.py`

## Current API Endpoints

- `GET /` - Root endpoint
- `GET /api/health` - Health check (used by frontend connection test)
- `GET /docs` - Interactive API documentation (Swagger)
- `GET /redoc` - Alternative API documentation

**Note:** Additional endpoints will be added as the frontend requires them.

## Environment Variables

Create a `.env` file in the backend directory:

```
PORT=5000
FRONTEND_URL=http://localhost:3000
NODE_ENV=development
DATABASE_URL=sqlite:///./spm.db
```

## Development

The server runs with auto-reload enabled in development mode. Any changes to the code will automatically restart the server.

## API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc
