"""
Reset Rate Limiter Script

This script resets the rate limiting state by making an API call to a special endpoint.
"""

import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def reset_rate_limiter():
    """Reset the rate limiter via API endpoint."""
    print("\n🔄 Resetting Rate Limiter...")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Try to access the reset endpoint (we'll create this)
            response = await client.post(f"{BASE_URL}/api/v1/admin/reset-rate-limiter")
            print(f"✅ Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\nAlternative: Restart the server to clear in-memory rate limits")

if __name__ == "__main__":
    asyncio.run(reset_rate_limiter())

