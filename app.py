import streamlit as st
import os
from dotenv import load_dotenv

# Basic Streamlit Setup
st.set_page_config(
    page_title="SpeechSense",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load env
load_dotenv()

def main():
    st.title("SpeechSense")
    st.subheader("Parkinson's Speech Biomarker Platform")
    
    # Auth & Session Management
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'role' not in st.session_state:
        st.session_state.role = None

    # Sidebar Logout Button (if logged in)
    if st.session_state.user:
        with st.sidebar:
            st.write(f"User: {st.session_state.user.email}")
            
            # Determine role from metadata if not set
            if not st.session_state.role:
                # 1. Hardcoded Admin Check
                if st.session_state.user.email == "o.shashwat10@gmail.com":
                    st.session_state.role = "admin"
                else:
                    try:
                        # 2. Check user metadata (from signup)
                        meta_role = st.session_state.user.user_metadata.get('role')
                        if meta_role:
                            st.session_state.role = meta_role
                        else:
                            from supabase_client import get_user_role
                            st.session_state.role = get_user_role(st.session_state.user.id)
                    except:
                        st.session_state.role = 'patient'
            
            st.info(f"Role: {st.session_state.role.upper()}")
            
            from views.auth import logout
            if st.button("Logout"):
                logout()

    # Main Routing
    if not st.session_state.user:
        # Show Login/Signup
        from views.auth import render_auth
        render_auth()
    else:
        # Route based on role
        role = st.session_state.role
        
        if role == 'admin':
            # st.warning("Admin Dashboard - Coming Soon")
            from views.admin import render_admin_view
            render_admin_view()
        elif role == 'doctor':
            # st.warning("Doctor Dashboard - Coming Soon")
            from views.doctor import render_doctor_view
            render_doctor_view()
        else: # Patient
            # st.success("Patient Dashboard - Coming Soon")
            from views.patient import render_patient_view
            render_patient_view()


if __name__ == "__main__":
    main()
