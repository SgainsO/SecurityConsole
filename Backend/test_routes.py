"""
Test script for the New Backend API routes.
"""
import asyncio
import httpx
import json


async def test_process_prompt_route():
    """Test the /api/process-prompt endpoint."""
    
    # Test request matching the expected format
    test_request = {
        "prompt": "What is the weather like today?",
        "pii_status": "ACCEPT",
        "slm_flag": "ACCEPT",
        "malicious_flag": "ACCEPT",
        "employee_id": "test_employee_001",
        "session_id": "test_session_001"
    }
    
    url = "http://localhost:8000/api/process-prompt"
    
    print("=" * 60)
    print("Testing New Backend API - /api/process-prompt")
    print("=" * 60)
    print(f"\nEndpoint: {url}")
    print(f"\nRequest:")
    print(json.dumps(test_request, indent=2))
    print("\n" + "-" * 60)
    
    try:
        print("\nSending request...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=test_request)
            
            print(f"\n✓ Response received!")
            print(f"\nStatus Code: {response.status_code}")
            print(f"\nResponse Body:")
            print(json.dumps(response.json(), indent=2))
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n{'=' * 60}")
                print("SUMMARY:")
                print(f"  Status: {result['status']}")
                print(f"  Details: {result['details']}")
                if result.get('final_response'):
                    print(f"  Response Preview: {result['final_response'][:100]}...")
                print("\n✓ Test PASSED")
            else:
                print("\n✗ Test FAILED")
                
    except httpx.ConnectError:
        print("\n✗ ERROR: Could not connect to the server.")
        print("\nMake sure the New Backend is running:")
        print("  python main.py (port 8000)")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
    
    print("=" * 60)


async def test_health_check():
    """Test the /api/health endpoint."""
    
    url = "http://localhost:8000/api/health"
    
    print("\n" + "=" * 60)
    print("Testing Health Check - /api/health")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"\nResponse:")
            print(json.dumps(response.json(), indent=2))
            
            if response.status_code == 200:
                print("\n✓ Health Check PASSED")
            else:
                print("\n✗ Health Check FAILED")
                
    except httpx.ConnectError:
        print("\n✗ ERROR: Could not connect to the server.")
        print("Make sure the New Backend is running: python main.py")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
    
    print("=" * 60)


async def main():
    """Run all tests."""
    print("\n🚀 Starting New Backend API Tests\n")
    
    # Test health check first
    await test_health_check()
    
    # Small delay
    await asyncio.sleep(1)
    
    # Test main endpoint
    await test_process_prompt_route()
    
    print("\n✅ All tests completed!\n")


if __name__ == "__main__":
    asyncio.run(main())

