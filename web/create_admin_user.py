from supabase_client import supabase
import time

def create_user():
    email = "o.shashwat10@gmail.com"
    password = "MIT1032233325"
    full_name = "admin@325"
    
    print(f"--- 👤 Creating User: {email} ---")

    try:
        # 1. Create Auth User
        # We use explicit sign_up. 
        # Note: If email confirmation is ON, this user won't be able to login immediately 
        # UNLESS we use the admin api (service_role) which we don't have.
        # But user said they will turn off email confirm.
        
        print("1. Attempting Auth Signup...")
        auth_response = supabase.auth.sign_up({
            "email": email, 
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "role": "doctor" # Assuming admin/doctor role
                }
            }
        })
        
        if auth_response.user:
            print(f"✅ Auth User Created! ID: {auth_response.user.id}")
            
            # 2. Manual Profile Insert (Just in case Trigger didn't fire or RLS blocked it)
            # We try to insert. If it fails due to duplicate, that's fine (means trigger worked).
            print("2. Ensuring Profile Exists...")
            profile_data = {
                "id": auth_response.user.id,
                "full_name": full_name,
                "role": "doctor"
            }
            try:
                supabase.from_('profiles').upsert(profile_data).execute()
                print("✅ Profile /upsert successful.")
            except Exception as pe:
                print(f"ℹ️ Profile Upsert Note: {pe} (This might be normal if trigger ran)")

        else:
            # If user already exists, auth_response.user might be None or dummy
            print("⚠️ User might already exist.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_user()
