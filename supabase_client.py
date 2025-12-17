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
    # Assuming there's a profiles table linked to auth.users
    try:
        response = supabase.table('profiles').select('role').eq('id', user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['role']
        return 'patient' # Default to patient
    except Exception as e:
        print(f"Error fetching role: {e}")
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
