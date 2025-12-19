import streamlit as st
from views.components import render_recording_section

def render_patient_view():
    st.header("Patient Dashboard")
    st.markdown("Welcome. You can contribute to our research or check your voice.")
    
    # Use the shared component with role='patient'
    render_recording_section(source_role="patient")
