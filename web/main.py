import streamlit as st
import os
import sys

# Add the current directory to python path
sys.path.append(os.getcwd())

# Import views - ensure these match your actual folder structure
# Assuming 'views' is a package (has __init__.py)
from views.auth import render_auth, logout
from views.patient import render_patient_view
from views.doctor import render_doctor_view
from views.admin import render_admin_view

st.set_page_config(page_title="SpeechSense", layout="wide")

def main():
    if "user" not in st.session_state:
        st.session_state.user = None
        
    if not st.session_state.user:
        render_auth()
    else:
        # User is logged in
        with st.sidebar:
            st.title("SpeechSense")
            st.write(f"Logged in as: {st.session_state.user.email}")
            
            # Retrieve role from metadata or session
            # Note: The auth.py sets 'role' in metadata, but we might need to fetch or defaulting it
            # For now, let's assume it's attached to user object or we fetch it
            user_role = st.session_state.user.user_metadata.get('role', 'patient')
            st.write(f"Role: {user_role}")
            
            if st.button("Logout"):
                logout()

        # Route based on role
        if user_role == 'admin':
            render_admin_view()
        elif user_role == 'doctor':
            render_doctor_view()
        else:
            render_patient_view()

if __name__ == "__main__":
    main()
