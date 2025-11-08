# Testing the Message Monitoring API

## Setup

1. Install dependencies:
```bash
cd Backend
pip install -r requirements.txt
```

2. Create a `.env` file with your MongoDB connection:
```bash
MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=security_console
```

3. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

## Running Tests

Run the test script:
```bash
python test_messages.py
```

## Architecture Overview

The platform uses a **message-based architecture** where each LLM interaction is stored as an individual message with:
- Employee tracking (user_id, employee_name)
- Prompt and response content
- Session grouping (session_id)
- Review system (needs_review, reviewed_by, reviewed_at)
- Flagging mechanism (is_flagged, flag_reason)
- Metadata for additional context

## What the Tests Cover

1. **Upload User Message** - Basic message with prompt and response
2. **Upload Sensitive Message** - Message with metadata and session tracking
3. **Session Messages** - Multiple messages grouped by session_id
4. **Get All Messages** - Retrieve all stored messages
5. **Get Employee Messages** - Filter by specific employee
6. **Get Session Messages** - Retrieve all messages in a session
7. **Flag Message** - Mark suspicious messages (employer flagging)
8. **Mark for Review** - Set messages that need employer review
9. **Complete Review** - Mark review as completed
10. **Get Flagged Messages** - Retrieve all flagged items
11. **Get Pending Reviews** - Messages needing review
12. **Filter Messages** - Combined filtering by flags and review status

## API Endpoints

### Upload Messages
- `POST /api/messages/user_messages` - Upload employee LLM messages

### Retrieve Messages
- `GET /api/messages/` - Get all messages (with optional filters)
- `GET /api/messages/{message_id}` - Get specific message
- `GET /api/messages/employee/{employee_id}` - Get employee's messages
- `GET /api/messages/session/{session_id}` - Get session messages

### Review & Flagging System
- `POST /api/messages/{message_id}/flag` - Flag suspicious messages
- `POST /api/messages/{message_id}/review` - Mark for review / complete review
- `GET /api/messages/flagged/all` - Get all flagged messages
- `GET /api/messages/review/pending` - Get messages needing review

### Update & Delete
- `PATCH /api/messages/{message_id}` - Update message details
- `DELETE /api/messages/{message_id}` - Delete message

## Manual Testing with curl

### Upload a user message:
```bash
curl -X POST "http://localhost:8000/api/messages/user_messages" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "emp_001",
    "prompt": "What is the company revenue?",
    "response": "The Q4 revenue was $10M",
    "employee_name": "John Doe",
    "model_name": "gpt-4",
    "session_id": "session_123"
  }'
```

### Flag a message (employer action):
```bash
curl -X POST "http://localhost:8000/api/messages/{message_id}/flag" \
  -H "Content-Type: application/json" \
  -d '{
    "is_flagged": true,
    "flag_reason": "Attempted to access sensitive credentials",
    "reviewed_by": "manager_001"
  }'
```

### Mark message for review:
```bash
curl -X POST "http://localhost:8000/api/messages/{message_id}/review" \
  -H "Content-Type: application/json" \
  -d '{
    "needs_review": true,
    "reviewed_by": "security_admin"
  }'
```

### Get all flagged messages:
```bash
curl "http://localhost:8000/api/messages/flagged/all"
```

### Get messages needing review:
```bash
curl "http://localhost:8000/api/messages/review/pending"
```

### Filter messages:
```bash
# Get flagged messages for specific employee
curl "http://localhost:8000/api/messages/?employee_id=emp_001&is_flagged=true"

# Get messages needing review in a session
curl "http://localhost:8000/api/messages/?session_id=session_123&needs_review=true"
```

### Get employee's messages:
```bash
curl "http://localhost:8000/api/messages/employee/emp_001"
```

### Get session messages:
```bash
curl "http://localhost:8000/api/messages/session/session_123"
```

## Dashboard Use Cases

### Employer Dashboard - Monitoring View

1. **View all messages** - `GET /api/messages/`
2. **View flagged messages** - `GET /api/messages/flagged/all`
3. **View pending reviews** - `GET /api/messages/review/pending`
4. **View specific employee** - `GET /api/messages/employee/{employee_id}`

### Employer Actions

1. **Flag suspicious message** - `POST /api/messages/{message_id}/flag`
2. **Mark for review** - `POST /api/messages/{message_id}/review`
3. **Review and clear flag** - Update flags using `PATCH`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Review & Flagging Workflow

```
Employee sends message
        ↓
Message stored with needs_review=false, is_flagged=false
        ↓
Employer reviews dashboard
        ↓
[If suspicious] → Flag message (is_flagged=true, flag_reason)
        ↓
[If needs attention] → Mark for review (needs_review=true)
        ↓
Security/Manager reviews
        ↓
Complete review (needs_review=false, reviewed_by, reviewed_at)
```
