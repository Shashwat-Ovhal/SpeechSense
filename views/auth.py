import streamlit as st
import time
from supabase_client import supabase

def render_auth():
    """Render Login/Signup container"""
    st.header("Authentication")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        render_login()
        
    with tab2:
        render_signup()

def render_login():
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if response.user:
                    st.success("Login successful!")
                    st.session_state.user = response.user
                    st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")

def render_signup():
    with st.form("signup_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password", help="Min 6 characters")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        # Simple role selection for Prototype (In real app, this would be admin-controlled)
        # For now, we allow users to self-identify to test easier
        role_options = ["patient", "doctor", "admin"]
        role = st.selectbox("I am a:", role_options)
        
        submit = st.form_submit_button("Sign Up")
        
        if submit:
            if password != confirm_password:
                st.error("Passwords do not match!")
                return
            
            try:
                # 1. Sign up auth user
                response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "role": role # Storing role in metadata for now
                        }
                    }
                })
                
                if response.user:
                    st.success("Signup successful! Please check your email to confirm.")
                    # In development, we might not have email confirm on, so we try to login immediately if session exists
                    if response.session:
                        st.session_state.user = response.user
                        st.rerun()
            except Exception as e:
                st.error(f"Signup failed: {str(e)}")

def logout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()
