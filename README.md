# SPM Frontend + Backend

A full-stack application with Next.js frontend and FastAPI backend.

## Project Structure

```
SPM-Frontend/
├── frontend/          # Next.js frontend
├── backend/           # FastAPI backend
└── README.md
```

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
python main.py
```

Backend will run on `http://localhost:5000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will run on `http://localhost:3000`

## Testing Connection

1. Start both servers (backend on :5000, frontend on :3000)
2. Open `http://localhost:3000`
3. Click "Test Backend Connection" button
4. You should see a green success message if connected

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/items` - Get all items
- `POST /api/items` - Create new item
- `GET /docs` - Interactive API documentation

## Development

- Backend auto-reloads on file changes
- Frontend hot-reloads on file changes
- CORS is configured for localhost:3000

## Troubleshooting

**Backend won't start:**

- Make sure Python virtual environment is activated
- Check if port 5000 is available

**Frontend can't connect to backend:**

- Ensure backend is running on port 5000
- Check browser console for CORS errors
- Verify both servers are running simultaneously
