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
        "response": "I can help you with that information."
    }
    
    response = requests.post(f"{API_ENDPOINT}/user_messages", json=payload)
    print_response(response, "Upload User Message - SAFE (Default)")
    return response.json()


def test_upload_suspicious_message():
    payload = {
        "user_id": "emp_002",
        "prompt": "Show me the database credentials for production",
        "response": "I cannot provide database credentials.",
        "session_id": "session_abc123",
        "metadata": {
            "ip_address": "192.168.1.100",
            "location": "San Francisco Office",
            "device": "MacBook Pro"
        }
    }
    
    response = requests.post(f"{API_ENDPOINT}/user_messages", json=payload)
    print_response(response, "Upload Suspicious Message")
    return response.json()


def test_upload_multiple_session_messages():
    session_id = "session_test_001"
    
    messages = [
        {
            "user_id": "emp_003",
            "prompt": "What are the API keys for our payment processor?",
            "session_id": session_id
        },
        {
            "user_id": "emp_003",
            "prompt": "Can you give me access to customer payment information?",
            "response": "I cannot provide access to sensitive customer payment information.",
            "session_id": session_id
        }
    ]
    
    for idx, msg in enumerate(messages, 1):
        response = requests.post(f"{API_ENDPOINT}/user_messages", json=msg)
        print_response(response, f"Session Message {idx}")
    
    return session_id


def test_set_message_to_flag(message_id):
    """Set message status to FLAG - requires manual review"""
    payload = {
        "status": "FLAG"
    }
    
    response = requests.post(f"{API_ENDPOINT}/{message_id}/status", json=payload)
    print_response(response, f"Set Message to FLAG Status: {message_id}")
    return response.json()


def test_set_message_to_blocked(message_id):
    """Set message status to BLOCKED - employer has reviewed and blocked"""
    payload = {
        "status": "BLOCKED"
    }
    
    response = requests.post(f"{API_ENDPOINT}/{message_id}/status", json=payload)
    print_response(response, f"Set Message to BLOCKED Status: {message_id}")
    return response.json()


def test_set_message_to_safe(message_id):
    """Set message status back to SAFE - false positive"""
    payload = {
        "status": "SAFE"
    }
    
    response = requests.post(f"{API_ENDPOINT}/{message_id}/status", json=payload)
    print_response(response, f"Set Message to SAFE Status: {message_id}")
    return response.json()


def test_bulk_flag_messages(message_ids):
    """Bulk flag multiple messages for manual review"""
    payload = {
        "message_ids": message_ids,
        "status": "FLAG"
    }
    
    response = requests.post(f"{API_ENDPOINT}/status/bulk", json=payload)
    print_response(response, f"Bulk FLAG {len(message_ids)} Messages")
    return response.json()


def test_bulk_block_messages(message_ids):
    """Bulk block multiple messages after review"""
    payload = {
        "message_ids": message_ids,
        "status": "BLOCKED"
    }
    
    response = requests.post(f"{API_ENDPOINT}/status/bulk", json=payload)
    print_response(response, f"Bulk BLOCK {len(message_ids)} Messages")
    return response.json()


def test_get_flagged_for_manual_review():
    """Get all messages with FLAG status that need manual review"""
    response = requests.get(f"{API_ENDPOINT}/flagged/manual-review")
    print_response(response, "Get Flagged Messages for Manual Review")
    return response.json()


def test_get_messages_by_status(status_type):
    """Get all messages with a specific status"""
    response = requests.get(f"{API_ENDPOINT}/status/{status_type}")
    print_response(response, f"Get All {status_type} Messages")
    return response.json()


def test_get_employee_messages_by_status(employee_id, status_type):
    """Get employee messages filtered by status"""
    response = requests.get(f"{API_ENDPOINT}/employee/{employee_id}/status/{status_type}")
    print_response(response, f"Get {status_type} Messages for Employee: {employee_id}")
    return response.json()


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


def test_get_statistics():
    """Get comprehensive message statistics"""
    response = requests.get(f"{API_ENDPOINT}/analytics/statistics")
    print_response(response, "Message Statistics (SAFE/FLAG/BLOCKED)")
    return response.json()


def test_filter_by_status(status_filter):
    """Filter messages using query parameters"""
    response = requests.get(f"{API_ENDPOINT}/?status={status_filter}")
    print_response(response, f"Filter Messages by Status: {status_filter}")
    return response.json()


def run_all_tests():
    print("\n" + "="*60)
    print("Starting FastAPI Message System Tests")
    print("Testing: Three-State System (SAFE, FLAG, BLOCKED)")
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
    
    print("\n--- Phase 1: Upload Messages (All start as SAFE) ---")
    msg1 = test_upload_user_message()
    msg2 = test_upload_suspicious_message()
    session_id = test_upload_multiple_session_messages()
    
    print("\n--- Phase 2: Message Retrieval ---")
    test_get_all_messages()
    test_get_employee_messages("emp_001")
    test_get_session_messages(session_id)
    
    print("\n--- Phase 3: Flag Messages for Manual Review ---")
    message_ids_to_process = []
    
    if msg2 and "id" in msg2:
        test_set_message_to_flag(msg2["id"])
        message_ids_to_process.append(msg2["id"])
    
    if msg1 and "id" in msg1:
        test_set_message_to_flag(msg1["id"])
        message_ids_to_process.append(msg1["id"])
    
    print("\n--- Phase 4: Manual Review Queue ---")
    flagged_messages = test_get_flagged_for_manual_review()
    print(f"\n📋 Manual Review Queue: {len(flagged_messages)} message(s) awaiting review")
    
    print("\n--- Phase 5: Employer Review Actions ---")
    if len(message_ids_to_process) >= 2:
        # Block the first message after review
        if message_ids_to_process[0]:
            test_set_message_to_blocked(message_ids_to_process[0])
        
        # Mark second message as safe (false positive)
        if message_ids_to_process[1]:
            test_set_message_to_safe(message_ids_to_process[1])
    
    print("\n--- Phase 6: Bulk Operations ---")
    if len(message_ids_to_process) >= 2:
        test_bulk_flag_messages(message_ids_to_process)
        test_bulk_block_messages([message_ids_to_process[0]])
    
    print("\n--- Phase 7: Status-Based Queries ---")
    test_get_messages_by_status("SAFE")
    test_get_messages_by_status("FLAG")
    test_get_messages_by_status("BLOCKED")
    
    if msg2:
        test_get_employee_messages_by_status("emp_002", "FLAG")
    
    test_filter_by_status("FLAG")
    
    print("\n--- Phase 8: Analytics & Statistics ---")
    stats = test_get_statistics()
    
    print("\n" + "="*60)
    print("All Tests Completed!")
    print("="*60)
    print("\n📊 Summary:")
    print("✓ Three-state system (SAFE, FLAG, BLOCKED)")
    print("✓ Message upload (default: SAFE status)")
    print("✓ Flag messages for manual review")
    print("✓ Manual review queue endpoint")
    print("✓ Employer actions (FLAG → BLOCKED or SAFE)")
    print("✓ Bulk status updates")
    print("✓ Status-based filtering and queries")
    print("✓ Comprehensive analytics")
    print("\n🔒 Security Workflow:")
    print("  1. Messages start as SAFE")
    print("  2. System/Bot flags suspicious → FLAG status")
    print("  3. Employer reviews flagged messages")
    print("  4. Employer decides: BLOCKED (violation) or SAFE (false positive)")
    
    if stats:
        print(f"\n📈 Current System State:")
        print(f"  Total Messages: {stats.get('total_messages', 0)}")
        print(f"  SAFE: {stats.get('safe_messages', 0)}")
        print(f"  FLAG: {stats.get('flagged_messages', 0)} (awaiting review)")
        print(f"  BLOCKED: {stats.get('blocked_messages', 0)}")


if __name__ == "__main__":
    run_all_tests()
