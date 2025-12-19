from supabase_client import supabase
import sys

def create_admin():
    email = "o.shashwat10@gmail.com"
    password = "MIT1032233325"
    
    print(f"Attempting to register Admin: {email}")
    
    try:
        # Default signup with 'patient' role in metadata, but our app.py ignores this for this specific email
        # We just need the user to exist in Supabase Auth.
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "role": "admin" # We try to set it, though app.py override makes this redundant but good for clarity
                }
            }
        })
        
        if response.user:
            print("✅ Admin user created/registered successfully!")
            print("Please check your email for a confirmation link if Supabase requires it.")
        else:
             # If user exists, this might happen or throw error
             print("ℹ️ User might already exist.")
             
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        print("Note: If the error is 'User already registered', try logging in directly.")

if __name__ == "__main__":
    create_admin()
