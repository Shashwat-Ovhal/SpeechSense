"""
Simple test to verify Supabase connection
"""
import os
from dotenv import load_dotenv

print("=== Supabase Connection Test ===\n")

# 1. Check .env loading
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"1. Environment Variables:")
print(f"   URL: {url}")
print(f"   KEY: {key[:20]}..." if key else "   KEY: NOT FOUND")
print()

# 2. Test basic HTTP connection
print("2. Testing HTTP connection to Supabase...")
try:
    import requests
    response = requests.get(f"{url}/rest/v1/", headers={
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }, timeout=10)
    print(f"   ✅ HTTP Response: {response.status_code}")
except Exception as e:
    print(f"   ❌ HTTP Error: {e}")
print()

# 3. Test Supabase client
print("3. Testing Supabase Python Client...")
try:
    from supabase import create_client
    client = create_client(url, key)
    print("   ✅ Client created successfully")
    
    # Try a simple query
    result = client.table('recordings').select("id").limit(1).execute()
    print(f"   ✅ Database query successful (found {len(result.data)} records)")
except Exception as e:
    print(f"   ❌ Client Error: {e}")
print()

print("=== Test Complete ===")
