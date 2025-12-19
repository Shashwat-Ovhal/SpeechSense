"""
Network Diagnostics for Supabase Connection
"""
import socket
import sys

print("=== Network Diagnostics ===\n")

# Test 1: Basic DNS resolution
print("1. Testing DNS Resolution...")
hostname = "pviknccxlxjwordfqxrg.supabase.co"
try:
    ip = socket.gethostbyname(hostname)
    print(f"   ✅ DNS Resolution successful: {hostname} -> {ip}")
except socket.gaierror as e:
    print(f"   ❌ DNS Resolution FAILED: {e}")
    print(f"   This means your computer cannot find the Supabase server.")
    print(f"\n   Possible fixes:")
    print(f"   - Check your internet connection")
    print(f"   - Flush DNS cache: ipconfig /flushdns")
    print(f"   - Change DNS to Google DNS (8.8.8.8, 8.8.4.4)")
    print(f"   - Disable VPN/Proxy if active")
    print(f"   - Check firewall settings")
    sys.exit(1)

# Test 2: General internet connectivity
print("\n2. Testing General Internet...")
try:
    socket.gethostbyname("google.com")
    print("   ✅ Internet connection working (google.com reachable)")
except:
    print("   ❌ No internet connection detected")
    sys.exit(1)

# Test 3: Supabase.co main domain
print("\n3. Testing Supabase Main Domain...")
try:
    socket.gethostbyname("supabase.co")
    print("   ✅ supabase.co is reachable")
except:
    print("   ❌ supabase.co is blocked or unreachable")

print("\n=== All Tests Passed ===")
print("Your network should be able to connect to Supabase.")
