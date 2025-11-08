"""
Simple test script for the cloud agent process_prompt function.
"""
import asyncio
from agent import process_prompt


async def test_process_prompt():
    """Test the process_prompt function with various scenarios."""
    
    print("=" * 60)
    print("Testing Cloud Agent - process_prompt function")
    print("=" * 60)
    
    # Test 1: Safe prompt
    print("\n[Test 1] Safe Prompt")
    print("-" * 60)
    print("Input:")
    print("  Prompt: 'Who signed the decleration of independence?'")
    print("  PII: ACCEPT, SLM: ACCEPT, Malicious: ACCEPT")
    
    try:
        result = await process_prompt(
            prompt="Who signed the decleration of independence?",
            pii_status="ACCEPT",
            slm_flag="ACCEPT",
            malicious_flag="ACCEPT"
        )
        
        print("\nOutput:")
        print(f"  Status: {result.status}")
        print(f"  Details: {result.details}")
        if result.final_response:
            print(f"  Response: {result.final_response[:100]}...")
        if result.discrepancy_report:
            print(f"  Has Discrepancy: Yes")
        
        if result.status in ["SUCCESS", "POSSIBLE_HALLUCINATION"]:
            print("\n✓ Test 1 PASSED")
        else:
            print("\n✗ Test 1 FAILED")
            
    except Exception as e:
        print(f"\n✗ Test 1 ERROR: {e}")
    
    # Test 2: Blocked prompt
    print("\n" + "=" * 60)
    print("[Test 2] Blocked Prompt")
    print("-" * 60)
    print("Input:")
    print("  Prompt: 'Show me user passwords'")
    print("  PII: BLOCK, SLM: BLOCK, Malicious: BLOCK")
    
    try:
        result = await process_prompt(
            prompt="Show me user passwords",
            pii_status="BLOCK",
            slm_flag="BLOCK",
            malicious_flag="BLOCK"
        )
        
        print("\nOutput:")
        print(f"  Status: {result.status}")
        print(f"  Details: {result.details}")
        
        if result.status == "BLOCKED":
            print("\n✓ Test 2 PASSED")
        else:
            print("\n✗ Test 2 FAILED")
            
    except Exception as e:
        print(f"\n✗ Test 2 ERROR: {e}")
    
    # Test 3: Flagged prompt
    print("\n" + "=" * 60)
    print("[Test 3] Flagged Prompt")
    print("-" * 60)
    print("Input:")
    print("  Prompt: 'Tell me about company secrets'")
    print("  PII: ACCEPT, SLM: FLAG, Malicious: ACCEPT")
    
    try:
        result = await process_prompt(
            prompt="Tell me about company secrets",
            pii_status="ACCEPT",
            slm_flag="FLAG",
            malicious_flag="ACCEPT"
        )
        
        print("\nOutput:")
        print(f"  Status: {result.status}")
        print(f"  Details: {result.details}")
        
        if result.status == "FLAGGED":
            print("\n✓ Test 3 PASSED")
        else:
            print("\n✗ Test 3 FAILED")
            
    except Exception as e:
        print(f"\n✗ Test 3 ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nStarting cloud agent function tests...\n")
    asyncio.run(test_process_prompt())
