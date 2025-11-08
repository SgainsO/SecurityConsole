# Aiber Firewall - Security Console

A FastAPI-based backend system for monitoring employee LLM interactions with built-in security review and flagging mechanisms.

## Overview

This system enables employers to monitor employee conversations with LLMs, flagging potentially sensitive data leaks and managing security reviews through a comprehensive message tracking system.

## Architecture

**Message-Based System**: Each LLM interaction is stored as an individual message with:
- Employee identification and tracking
- Prompt and response content
- Session grouping for related messages
- Review workflow (`needs_review`, `reviewed_by`, `reviewed_at`)
- Internal flagging system (`is_flagged`, `flag_reason`)
- Flexible metadata for context (IP, location, device, etc.)

## Key Features

### For Employers
- **Dashboard-Ready API**: View all employee LLM messages
- **Flagging System**: Mark suspicious messages for security review
- **Review Workflow**: Track which messages need attention
- **Employee Monitoring**: Filter messages by employee or session
- **Audit Trail**: Track who reviewed what and when

### Security Features
- Real-time message storage
- Metadata tracking (IP, location, device)
- Session-based grouping
- Multi-level filtering
- Timestamp tracking

## Tech Stack

- **FastAPI** - Modern async Python web framework
- **MongoDB** - Document database (via Motor for async)
- **Pydantic v2** - Data validation and settings
- **Python 3.8+** - Required

## Quick Start

### 1. Install Dependencies

```bash
cd Backend
pip install -r requirements.txt
```

### 2. Configure MongoDB

Create `.env` file:
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=security_console
```

### 3. Run the Server

```bash
uvicorn main:app --reload
```

Server runs at: http://localhost:8000

### 4. API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Message Upload
```
POST /api/messages/user_messages
```
Upload employee LLM messages for monitoring

### Message Retrieval
```
GET  /api/messages/                    # All messages (with filters)
GET  /api/messages/{message_id}        # Specific message
GET  /api/messages/employee/{id}       # Employee's messages
GET  /api/messages/session/{id}        # Session messages
```

### Review & Flagging (Employer Actions)
```
POST /api/messages/{id}/flag          # Flag suspicious message
POST /api/messages/{id}/review        # Mark for/complete review
GET  /api/messages/flagged/all        # All flagged messages
GET  /api/messages/review/pending     # Messages needing review
```

### Management
```
PATCH /api/messages/{id}              # Update message
DELETE /api/messages/{id}             # Delete message
```

## Testing

Run automated tests:
```bash
python test_messages.py
```

See [TESTING.md](Backend/TESTING.md) for detailed testing guide.

## Usage Example

### Upload a message:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/messages/user_messages",
    json={
        "user_id": "emp_001",
        "prompt": "What are the database credentials?",
        "response": "I cannot provide sensitive credentials.",
        "employee_name": "John Doe",
        "model_name": "gpt-4",
        "session_id": "session_123",
        "metadata": {
            "ip_address": "192.168.1.100",
            "location": "Office"
        }
    }
)
```

### Flag a message (employer):
```python
message_id = "..."
response = requests.post(
    f"http://localhost:8000/api/messages/{message_id}/flag",
    json={
        "is_flagged": True,
        "flag_reason": "Attempted credential access",
        "reviewed_by": "security_admin"
    }
)
```

### View flagged messages:
```python
response = requests.get(
    "http://localhost:8000/api/messages/flagged/all"
)
```

## Dashboard Integration

The API is designed for dashboard consumption:

1. **Monitor View**: Display all messages with filtering
2. **Alert View**: Show flagged messages requiring attention
3. **Review Queue**: Display messages marked for review
4. **Employee View**: Per-employee message history
5. **Session View**: Group related messages together

## Workflow

```
Employee → LLM Interaction → Message Stored
                                    ↓
                          Employer Dashboard
                                    ↓
                    [Review] → Flag if suspicious
                                    ↓
                      Security Review & Action
```

## Project Structure

```
Backend/
├── main.py                  # FastAPI application
├── config.py                # Settings & configuration
├── requirements.txt         # Python dependencies
├── models/
│   └── message.py          # Pydantic models
├── routers/
│   └── message_routes.py   # API endpoints
├── database/
│   └── connection.py       # MongoDB connection
├── test_messages.py        # Automated tests
└── TESTING.md             # Testing documentation
```

## Development

The codebase follows FastAPI best practices:
- Async/await for all database operations
- Pydantic models for validation
- Type hints throughout
- RESTful API design
- Comprehensive error handling

## License

Hackathon Project
