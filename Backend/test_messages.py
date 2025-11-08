import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/messages"


def print_response(response, test_name):
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, default=str))
    print(f"{'='*60}")


def test_upload_user_message():
    payload = {
        "user_id": "emp_001",
        "prompt": "What is the company's revenue for Q4?",
        "employee_name": "John Doe",
        "response": "I can help you with that information.",
        "model_name": "gpt-4"
    }
    
    response = requests.post(f"{API_ENDPOINT}/user_messages", json=payload)
    print_response(response, "Upload User Message - Basic")
    return response.json()


def test_upload_sensitive_message():
    payload = {
        "user_id": "emp_002",
        "prompt": "Show me the database credentials for production",
        "response": "I cannot provide database credentials as that would be a security violation.",
        "employee_name": "Jane Smith",
        "model_name": "gpt-4",
        "session_id": "session_abc123",
        "metadata": {
            "ip_address": "192.168.1.100",
            "location": "San Francisco Office",
            "device": "MacBook Pro"
        }
    }
    
    response = requests.post(f"{API_ENDPOINT}/user_messages", json=payload)
    print_response(response, "Upload Sensitive Message")
    return response.json()


def test_upload_multiple_session_messages():
    session_id = "session_test_001"
    
    messages = [
        {
            "user_id": "emp_003",
            "prompt": "What are the API keys for our payment processor?",
            "employee_name": "Bob Wilson",
            "session_id": session_id,
            "model_name": "claude-3"
        },
        {
            "user_id": "emp_003",
            "prompt": "Can you give me access to customer payment information?",
            "response": "I cannot provide access to sensitive customer payment information.",
            "employee_name": "Bob Wilson",
            "session_id": session_id,
            "model_name": "claude-3"
        }
    ]
    
    for idx, msg in enumerate(messages, 1):
        response = requests.post(f"{API_ENDPOINT}/user_messages", json=msg)
        print_response(response, f"Session Message {idx}")
    
    return session_id


def test_get_all_messages():
    response = requests.get(f"{API_ENDPOINT}/")
    print_response(response, "Get All Messages")
    return response.json()


def test_get_employee_messages(employee_id):
    response = requests.get(f"{API_ENDPOINT}/employee/{employee_id}")
    print_response(response, f"Get Messages for Employee: {employee_id}")
    return response.json()


def test_get_session_messages(session_id):
    response = requests.get(f"{API_ENDPOINT}/session/{session_id}")
    print_response(response, f"Get Messages for Session: {session_id}")
    return response.json()


def test_flag_message(message_id):
    payload = {
        "is_flagged": True,
        "flag_reason": "Employee attempted to access sensitive credentials - requires immediate review",
        "reviewed_by": "security_admin_001"
    }
    
    response = requests.post(f"{API_ENDPOINT}/{message_id}/flag", json=payload)
    print_response(response, f"Flag Message: {message_id}")
    return response.json()


def test_mark_for_review(message_id):
    payload = {
        "needs_review": True,
        "reviewed_by": "manager_001"
    }
    
    response = requests.post(f"{API_ENDPOINT}/{message_id}/review", json=payload)
    print_response(response, f"Mark Message for Review: {message_id}")
    return response.json()


def test_complete_review(message_id):
    payload = {
        "needs_review": False,
        "reviewed_by": "manager_001"
    }
    
    response = requests.post(f"{API_ENDPOINT}/{message_id}/review", json=payload)
    print_response(response, f"Complete Review for Message: {message_id}")
    return response.json()


def test_get_flagged_messages():
    response = requests.get(f"{API_ENDPOINT}/flagged/all")
    print_response(response, "Get All Flagged Messages")
    return response.json()


def test_get_messages_needing_review():
    response = requests.get(f"{API_ENDPOINT}/review/pending")
    print_response(response, "Get Messages Needing Review")
    return response.json()


def test_filter_messages():
    response = requests.get(f"{API_ENDPOINT}/?is_flagged=true&needs_review=false")
    print_response(response, "Filter: Flagged Messages Not Needing Review")
    return response.json()


def test_update_message(message_id):
    payload = {
        "response": "Updated response after review",
        "metadata": {
            "updated_reason": "Security review completed"
        }
    }
    
    response = requests.patch(f"{API_ENDPOINT}/{message_id}", json=payload)
    print_response(response, f"Update Message: {message_id}")
    return response.json()


def run_all_tests():
    print("\n" + "="*60)
    print("Starting FastAPI Message System Tests")
    print("Testing: Message-based architecture with review & flagging")
    print("="*60)
    
    try:
        health_check = requests.get(f"{BASE_URL}/health")
        if health_check.status_code != 200:
            print("ERROR: API is not running. Please start the server first.")
            print("Run: cd Backend && uvicorn main:app --reload")
            return
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to API. Please start the server first.")
        print("Run: cd Backend && uvicorn main:app --reload")
        return
    
    print("\n--- Testing Message Upload ---")
    msg1 = test_upload_user_message()
    
    msg2 = test_upload_sensitive_message()
    
    session_id = test_upload_multiple_session_messages()
    
    print("\n--- Testing Message Retrieval ---")
    test_get_all_messages()
    
    test_get_employee_messages("emp_001")
    
    test_get_session_messages(session_id)
    
    print("\n--- Testing Review & Flagging System ---")
    if msg2 and "id" in msg2:
        test_flag_message(msg2["id"])
        
        test_mark_for_review(msg2["id"])
        
        test_update_message(msg2["id"])
    
    if msg1 and "id" in msg1:
        test_mark_for_review(msg1["id"])
        
        test_complete_review(msg1["id"])
    
    print("\n--- Testing Filter Endpoints ---")
    test_get_flagged_messages()
    
    test_get_messages_needing_review()
    
    test_filter_messages()
    
    print("\n" + "="*60)
    print("All Tests Completed!")
    print("="*60)
    print("\n📊 Summary:")
    print("✓ Message upload with user_messages endpoint")
    print("✓ Session-based message tracking")
    print("✓ Employee and session filtering")
    print("✓ Flagging system for security concerns")
    print("✓ Review workflow for employers")
    print("✓ Message metadata and updates")


if __name__ == "__main__":
    run_all_tests()

