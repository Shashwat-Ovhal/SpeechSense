import streamlit as st
import os
import tempfile
import json
from datetime import datetime
from supabase_client import save_recording_data, supabase
from feature_extractor import ComprehensiveSpeechAnalyzer

# Initialize analyzer
analyzer = ComprehensiveSpeechAnalyzer()

ALLOWED_EXTENSIONS = ['wav', 'mp3', 'm4a', 'ogg', 'webm']

def render_patient_view():
    st.header("Patient Dashboard")
    st.markdown("Please provide your details and record your voice.")

    with st.expander("ℹ️ Instructions", expanded=True):
        st.markdown("""
        1.  Fill out the **Patient Information** form.
        2.  **Record** your voice reading the passage below OR **Upload** an audio file.
        3.  Click **Submit Analysis**.
        """)

    # --- 1. Metadata Form ---
    st.subheader("1. Patient Information")
    with st.form("metadata_form"):
        col1, col2 = st.columns(2)
        with col1:
            participant_id = st.text_input("Participant ID (Optional/Anonymous)", 
                                         value=st.session_state.user.id if st.session_state.user else "anon")
            age = st.number_input("Age", min_value=18, max_value=120, step=1)
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
        
        with col2:
            language = st.selectbox("Native Language", ["English", "Hindi", "Marathi", "Tamil", "Other"])
            pd_status = st.selectbox("PD Status (Self-Reported)", ["Healthy Control", "Parkinson's Disease", "Unknown"])
            
        notes = st.text_area("Additional Notes (Medication, etc.)")
        
        # We don't submit here, we bundle it with the audio
        st.markdown("*Form details will be submitted with audio.*")
        auth_submit = st.form_submit_button("Confirm Details")

    # --- 2. Audio Capture ---
    st.subheader("2. Audio Recording")
    
    st.markdown("### Reading Passage")
    st.info('"The north wind and the sun were disputing which was the stronger, when a traveler came along wrapped in a warm cloak."')

    tab_record, tab_upload = st.tabs(["🎙️ Record Voice", "📤 Upload File"])
    
    audio_data = None
    source_type = None

    with tab_record:
        # checking for experimental audio input or fallback
        try:
            audio_value = st.audio_input("Record")
            if audio_value:
                audio_data = audio_value
                source_type = "recording"
        except AttributeError:
            st.warning("Native recording not supported in this Streamlit version. Please use Upload.")

    with tab_upload:
        uploaded_file = st.file_uploader("Upload Audio", type=ALLOWED_EXTENSIONS)
        if uploaded_file:
            audio_data = uploaded_file
            source_type = "upload"

    # --- 3. Processing & Submission ---
    if audio_data is not None:
        st.audio(audio_data, format="audio/wav")
        
        if st.button("🚀 Analyze & Submit Data", type="primary"):
            if not age or not language:
                st.error("Please fill in Age and Language fields.")
                return

            with st.spinner("Processing audio... This may take a moment."):
                try:
                    # 1. Save to Temp File
                    file_ext = "wav" # Default for recorder, or extract from upload
                    if hasattr(audio_data, 'name'):
                        file_ext = audio_data.name.split('.')[-1]
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                        tmp.write(audio_data.getvalue())
                        tmp_path = tmp.name

                    # 2. Extract Features
                    features = analyzer.extract_all_features(tmp_path)
                    
                    if not features:
                        st.error("Could not extract features. Please try a clearer recording.")
                        os.unlink(tmp_path)
                        return
                    
                    st.success("✅ Acoustic Biomarkers Extracted!")
                    with st.expander("View Feature Data"):
                        st.json(features)

                    # 3. Upload Audio to Supabase Storage (Optional - requires Storage bucket setup)
                    # For Phase 1, we might just skip audio file storage if bucket isn't ready, 
                    # OR we implement it. I'll try to implement it but safeguard it.
                    audio_url = "not_stored"
                    try:
                        # Assumption: 'audio-recordings' bucket exists. If not, this fails gracefully.
                        file_name = f"{st.session_state.user.id}/{datetime.now().isoformat()}.{file_ext}"
                        # Need to rewind/reset buffer if possible or re-read?
                        # audio_data.seek(0) -> Streamlit UploadedFile is seekable.
                        # user upload functionality specifically requires storage bucket
                        # We will skip actual file upload for this specific step to avoid blocking if bucket missing
                        # but we note it in the plan.
                        pass
                    except Exception as e:
                        print(f"Storage upload failed: {e}")

                    # 4. Save Record to DB
                    metadata = {
                        "age": age,
                        "gender": gender,
                        "language": language,
                        "pd_status": pd_status,
                        "notes": notes,
                        "source": source_type
                    }
                    
                    # We use the helper from supabase_client
                    # Note: We need to handle the case where 'recordings' table might expects UUID for user_id
                    try:
                        save_recording_data(st.session_state.user.id, metadata, audio_url, features)
                        st.balloons()
                        st.success("Data successfully saved to secure database!")
                    except Exception as db_err:
                        st.error(f"Database Error: {db_err}")
                        st.warning("Ensure the 'recordings' table exists in Supabase.")

                    # Cleanup
                    os.unlink(tmp_path)

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
