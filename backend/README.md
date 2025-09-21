# SPM Backend API

FastAPI backend for SPM Frontend application.

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

   Or with uvicorn directly:

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 5000
   ```

## API Endpoints

- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `GET /api/items` - Get all items
- `POST /api/items` - Create new item
- `GET /api/items/{item_id}` - Get item by ID
- `GET /docs` - Interactive API documentation (Swagger)
- `GET /redoc` - Alternative API documentation

## Environment Variables

Create a `.env` file in the backend directory:

```
PORT=5000
FRONTEND_URL=http://localhost:3000
NODE_ENV=development
```

## Development

The server runs with auto-reload enabled in development mode. Any changes to the code will automatically restart the server.

## API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc
