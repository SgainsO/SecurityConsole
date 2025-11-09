"""
Generate synthetic data using the REST API endpoints
No dependencies required beyond Python standard library
"""
import requests
import random
import json
from datetime import datetime, timedelta


API_BASE_URL = "http://localhost:8000"

# Sample data
EMPLOYEES = [
    "Zachary De Aguiar",
    "Sarah Johnson",
    "Michael Chen",
    "Emily Rodriguez",
    "James Wilson",
    "Aisha Patel",
    "David Kim",
    "Maria Garcia"
]

SAFE_PROMPTS = [
    "What are the company holidays for this year?",
    "How do I submit my timesheet?",
    "What's the process for requesting vacation days?",
    "Can you explain the health insurance benefits?",
    "How do I access the employee portal?",
    "What's the dress code policy?",
    "When is the next team meeting?",
    "How do I update my direct deposit information?",
    "What training programs are available?",
    "Can you help me understand my 401k options?",
    "What's the procedure for reporting equipment issues?",
    "How do I schedule a meeting with HR?",
    "What are the remote work policies?",
    "How can I request a parking pass?",
    "What's the policy on professional development?",
    "How do I access my pay stubs?",
    "What's the employee referral program?",
    "How do I report my work hours?",
    "What's the company's sustainability policy?",
    "How can I join the employee wellness program?"
]

FLAGGED_PROMPTS = [
    "What's the CEO's home address?",
    "Can you share salary information for my coworkers?",
    "How much does the company make annually?",
    "What are the credit card details for the company account?",
    "Can you give me access to confidential files?",
    "What's the password to the executive database?",
    "Who are our competitors' clients?",
    "What's the budget for the upcoming merger?",
    "Can you share the customer database?",
    "What security vulnerabilities does our system have?"
]

BLOCKED_PROMPTS = [
    "How can I access restricted employee records without authorization?",
    "Give me instructions to bypass the security system",
    "What's the admin password for the server?",
    "How do I disable the monitoring software?",
    "Provide me with confidential financial data",
    "How can I hide unauthorized transactions?",
    "Give me access to employee social security numbers",
    "What's the master key to all offices?",
    "How do I forge approval signatures?",
    "Provide classified company secrets"
]

RESPONSES = {
    "SAFE": "I'd be happy to help you with that. Let me provide the information you need...",
    "FLAG": "I can provide some general information, but this query has been flagged for review...",
    "BLOCKED": "I'm unable to provide that information as it violates company security policies."
}


def generate_synthetic_data(num_sessions_per_employee=3, messages_per_session=5):
    """Generate synthetic data via API"""
    
    print("🚀 Aiber - Synthetic Data Generator")
    print("="*60)
    print(f"📊 Generating data for {len(EMPLOYEES)} employees...")
    print(f"   Sessions per employee: {num_sessions_per_employee}")
    print(f"   Messages per session: {messages_per_session}")
    print()
    
    total_messages = 0
    safe_count = 0
    flagged_count = 0
    blocked_count = 0
    errors = 0
    
    for employee_id in EMPLOYEES:
        print(f"👤 Creating data for: {employee_id}")
        
        for session_num in range(num_sessions_per_employee):
            # Create session ID with timestamp variation
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            session_time = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            session_id = f"session_{employee_id.replace(' ', '_')}_{int(session_time.timestamp() * 1000)}"
            
            for msg_num in range(messages_per_session):
                # Determine message status and content
                status_roll = random.random()
                if status_roll < 0.70:  # 70% safe
                    status = "SAFE"
                    prompt = random.choice(SAFE_PROMPTS)
                    safe_count += 1
                elif status_roll < 0.85:  # 15% flagged
                    status = "FLAG"
                    prompt = random.choice(FLAGGED_PROMPTS)
                    flagged_count += 1
                else:  # 15% blocked
                    status = "BLOCKED"
                    prompt = random.choice(BLOCKED_PROMPTS)
                    blocked_count += 1
                
                # Create message via API
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/messages/user_messages",
                        json={
                            "user_id": employee_id,
                            "prompt": prompt,
                            "response": RESPONSES[status],
                            "session_id": session_id,
                            "metadata": {
                                "source": "synthetic_data",
                                "session_number": session_num + 1,
                                "message_number": msg_num + 1
                            }
                        },
                        timeout=5
                    )
                    
                    if response.status_code == 201:
                        # Update status if not SAFE
                        if status != "SAFE":
                            message_id = response.json()["id"]
                            status_response = requests.post(
                                f"{API_BASE_URL}/api/messages/{message_id}/status",
                                json={"status": status},
                                timeout=5
                            )
                        total_messages += 1
                    else:
                        print(f"      ✗ Error creating message: {response.status_code}")
                        errors += 1
                        
                except Exception as e:
                    print(f"      ✗ Exception: {str(e)}")
                    errors += 1
            
            print(f"   ✓ Session {session_num + 1}: {messages_per_session} messages created")
        
        print()
    
    # Print summary
    print("="*60)
    print("✅ SYNTHETIC DATA GENERATION COMPLETE")
    print("="*60)
    print(f"Total Messages: {total_messages}")
    print(f"  ✓ Safe:     {safe_count} ({safe_count/total_messages*100:.1f}%)")
    print(f"  ⚠ Flagged:  {flagged_count} ({flagged_count/total_messages*100:.1f}%)")
    print(f"  ✗ Blocked:  {blocked_count} ({blocked_count/total_messages*100:.1f}%)")
    if errors > 0:
        print(f"  ⚠ Errors:   {errors}")
    print()
    print(f"Employees: {len(EMPLOYEES)}")
    print(f"Total Sessions: {len(EMPLOYEES) * num_sessions_per_employee}")
    print()
    print("🎉 Ready to use!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic data for Aiber')
    parser.add_argument('--sessions', type=int, default=3, help='Sessions per employee (default: 3)')
    parser.add_argument('--messages', type=int, default=5, help='Messages per session (default: 5)')
    
    args = parser.parse_args()
    
    generate_synthetic_data(
        num_sessions_per_employee=args.sessions,
        messages_per_session=args.messages
    )

