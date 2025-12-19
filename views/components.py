import streamlit as st
import os
import tempfile
import json
from datetime import datetime
from supabase_client import save_recording_data
from feature_extractor import ComprehensiveSpeechAnalyzer

# Initialize analyzer
analyzer = ComprehensiveSpeechAnalyzer()
ALLOWED_EXTENSIONS = ['wav', 'mp3', 'm4a', 'ogg', 'webm']

def render_recording_section(source_role="patient"):
    """
    Reusable Recording Component
    source_role: 'patient' (Self) or 'doctor' (Recording a patient)
    """
    
    # --- Mode Selection ---
    st.subheader("Select Action")
    mode = st.radio("Choose Mode", 
        ["Contribute to Research Dataset (Labeled Data)", "Check Parkinson's Risk (Prediction)"],
        horizontal=True
    )

    if "Prediction" in mode:
        st.info("🔮 AI Prediction Module is currently under development.")
        st.warning("This feature will be available in Phase 3.")
        return # Stop rendering

    # --- Dataset Contribution Mode ---
    st.success("✅ You are contributing to the SpeechSense Open Research Dataset.")
    st.markdown("---")

    # --- Metadata Form ---
    st.subheader("1. Subject Information")
    with st.form("recording_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # If Doctor is recording, Participant ID is crucial. If Patient, it can be anon.
            default_id = "anon"
            label_id = "Participant ID (Anonymous)"
            if source_role == 'doctor':
                default_id = ""
                label_id = "Patient ID / Reference Number (Required)"
                
            participant_id = st.text_input(label_id, value=default_id)
            age = st.number_input("Age", min_value=18, max_value=120, step=1)
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
        
        with col2:
            language = st.selectbox("Native Language", ["English", "Hindi", "Marathi", "Tamil", "Other"])
            
            # Label is CRITICAL for dataset
            st.markdown("##### 🩺 Clinical Label (Crucial)")
            pd_status = st.selectbox("Does the subject have Parkinson's?", 
                ["Select...", "Yes (Diagnosed PD)", "No (Healthy Control)", "Unknown"],
                index=0
            )
            
        notes = st.text_area("Additional Clinical Notes (Medication, symptoms, etc.)")
        
        st.info("Audio recording section is below. You will submit after recording.")
        confirm_meta = st.form_submit_button("Confirm Metadata")

    # --- Audio Capture ---
    st.subheader("2. Audio Recording")
    st.markdown("### Reading Passage")
    st.info('"The north wind and the sun were disputing which was the stronger, when a traveler came along wrapped in a warm cloak."')

    tab_record, tab_upload = st.tabs(["🎙️ Record Voice", "📤 Upload File"])
    
    audio_data = None
    source_type = None

    with tab_record:
        try:
            audio_value = st.audio_input(f"Record ({source_role})")
            if audio_value:
                audio_data = audio_value
                source_type = "recording"
        except AttributeError:
            st.warning("Native recording not supported. Use Upload.")

    with tab_upload:
        uploaded_file = st.file_uploader("Upload Audio", type=ALLOWED_EXTENSIONS)
        if uploaded_file:
            audio_data = uploaded_file
            source_type = "upload"

    # --- Submission ---
    if audio_data is not None:
        st.audio(audio_data, format="audio/wav")
        
        if st.button("🚀 Process & Save to Dataset", type="primary"):
            # Validation
            if pd_status == "Select...":
                st.error("⚠️ Please select a valid Parkinson's status (Yes/No). We need labeled data.")
                return
            if source_role == 'doctor' and (not participant_id or participant_id == "anon"):
                st.error("⚠️ Doctors must provide a Patient/Reference ID.")
                return

            with st.spinner("Extracting Acoustic Biomarkers..."):
                try:
                    # Temp File Logic
                    file_ext = "wav"
                    if hasattr(audio_data, 'name'):
                        file_ext = audio_data.name.split('.')[-1]
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                        tmp.write(audio_data.getvalue())
                        tmp_path = tmp.name

                    # Extract
                    features = analyzer.extract_all_features(tmp_path)
                    os.unlink(tmp_path) # Cleanup immediate

                    if not features:
                        st.error("Feature extraction failed. Try a clearer audio.")
                        return
                    
                    # Prepare Metadata
                    metadata = {
                        "age": age,
                        "gender": gender,
                        "language": language,
                        "pd_status": pd_status, # The Label
                        "notes": notes,
                        "recorded_by_role": source_role,
                        "recorder_id": st.session_state.user.id, # Who pressed the button
                        "subject_id": participant_id
                    }

                    # Save using shared client
                    # For audio_url, we skip bucket for now as agreed
                    save_recording_data(st.session_state.user.id, metadata, "not_stored", features)
                    
                    st.balloons()
                    st.success("✅ Data Successfully Contributed to Research Dataset!")
                    
                    with st.expander("View Extracted Data"):
                        st.json(features)
                        
                except Exception as e:
                    st.error(f"Error: {e}")
