import os
from supabase import create_client, Client

# Hardcoded credentials as per user context
url = "https://pviknccxlxjwordfqxrg.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB2aWtuY2N4bHhqd29yZGZxeHJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5NDkyNzcsImV4cCI6MjA3MzUyNTI3N30.WJSrmA6F41tSeF5OiiXV1yu0F_ExxdB_zmN1JgMSLLk"

supabase: Client = create_client(url, key)
