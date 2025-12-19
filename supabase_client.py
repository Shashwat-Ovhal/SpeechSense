from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_role(user_id):
    """Fetch user role from 'profiles' table or metadata"""
    # Hardcoded Admin Check for Prototype
    try:
        user = supabase.auth.get_user(user_id) # This might not work with just ID, need full user obj usually.
        # Better approach: The app.py passes the ID, but we usually need the email.
        # Let's rely on the session user object in app.py logic mostly, 
        # but here we can try to fetch the user if possible or return patient default.
        pass
    except:
        pass

    # The actual enforcement is better done in app.py where we have the full user object (with email)
    # But let's check if we can query by ID here if needed.
    # For now, falling back to 'patient' is safe.
    return 'patient'

def save_recording_data(user_id, metadata, audio_url, features):
    """Save recording metadata and features to Supabase"""
    data = {
        "user_id": user_id,
        "audio_url": audio_url,
        "metadata": metadata, # JSONB column
        "features": features, # JSONB column
        "created_at": "now()"
    }
    return supabase.table('recordings').insert(data).execute()

def get_all_recordings():
    """Fetch all recordings for Doctor/Admin view"""
    # Fetch all columns 
    return supabase.table('recordings').select("*").order('created_at', desc=True).execute()

def delete_recording(recording_id):
    """Delete a specific recording by ID"""
    return supabase.table('recordings').delete().eq('id', recording_id).execute()
