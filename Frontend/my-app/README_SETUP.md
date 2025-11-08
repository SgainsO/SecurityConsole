# Frontend Setup Instructions

## Prerequisites

1. **Backend Must Be Running**
   ```bash
   cd Backend
   uvicorn main:app --reload
   ```
   The backend should be running on `http://localhost:8000`

2. **Install Dependencies**
   ```bash
   cd Frontend/my-app
   npm install
   ```

## Environment Configuration

The `.env.local` file has been created with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

This points to your local backend API.

## Running the Frontend

```bash
cd Frontend/my-app
npm run dev
```

The app will be available at `http://localhost:3000`

## How It Works

### Chat Interface
- When a user sends a message in the chat:
  1. Message is posted to `/api/messages/user_messages`
  2. Message is immediately flagged (status set to "FLAG")
  3. Message appears in the Flagged Messages panel on the right

### Review Panel
- Automatically loads flagged messages from the backend
- Auto-refreshes every 10 seconds
- Manual refresh button available
- Actions:
  - **Clear**: Marks message as SAFE (removes from flagged list)
  - **Block**: Marks message as BLOCKED (removes from flagged list)

## Testing the Integration

1. Start the backend: `cd Backend && uvicorn main:app --reload`
2. Start the frontend: `cd Frontend/my-app && npm run dev`
3. Open browser to `http://localhost:3000`
4. Type a message in the chat and click Send
5. Watch it appear in the Flagged Messages panel on the right
6. Click "Clear" or "Block" to change its status

## API Endpoints Used

- `POST /api/messages/user_messages` - Create new message
- `POST /api/messages/{id}/status` - Change message status
- `GET /api/messages/flagged/manual-review` - Get all flagged messages

## Features

- Real-time integration with FastAPI backend
- Auto-refresh of flagged messages (every 10 seconds)
- Loading states and error handling
- Toast notifications for user feedback
- Employee ID: `emp_test_001` (hardcoded for testing)
- Unique session ID per page load

## Troubleshooting

### CORS Errors
If you see CORS errors, make sure the backend has CORS enabled for `http://localhost:3000`

The backend `main.py` should have:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Connection Refused
Make sure the backend is running on port 8000:
```bash
cd Backend
uvicorn main:app --reload
```

### Messages Not Appearing
Check the browser console for errors. The toast notifications will show in the console as well.

