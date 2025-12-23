from supabase_client import supabase
import time

def check_health():
    print("--- 🔍 Checking System Health ---")
    
    # 1. Check Connection
    try:
        user = supabase.auth.get_user()
        print("✅ Supabase Connection: OK")
    except Exception as e:
        print(f"❌ Supabase Connection: FAILED ({e})")
        return

    # 2. Check Profiles (RLS might hide them, but let's try)
    try:
        # We need to sign in or use a service key to see all, 
        # but with Anon key we might only see public ones (if we set policy to true)
        response = supabase.from_('profiles').select('*').execute()
        profiles = response.data
        print(f"✅ Profiles Table: Found {len(profiles)} profiles")
        for p in profiles:
            print(f"   - User: {p.get('full_name')} ({p.get('role')}) - ID: {p.get('id')}")
    except Exception as e:
        print(f"❌ Profiles Check: FAILED ({e})")

    # 3. Check Recordings
    try:
        response = supabase.from_('recordings').select('*').execute()
        recordings = response.data
        print(f"✅ Recordings Table: Found {len(recordings)} recordings")
    except Exception as e:
        print(f"❌ Recordings Check: FAILED ({e})")

    print("\n-------------------------------")
    if len(profiles) == 0:
        print("💡 TIP: If you signed up on Mobile but see 0 profiles here,")
        print("   it usually means the 'Trigger' script was not run OR Email Verification is pending.")

if __name__ == "__main__":
    check_health()
