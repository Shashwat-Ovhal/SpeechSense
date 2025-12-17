import streamlit as st
import pandas as pd
import json
from supabase_client import get_all_recordings

def render_doctor_view():
    st.header("Medical Associate / Doctor Dashboard")
    st.markdown("View and filter patient recordings and extracted acoustic biomarkers.")

    # 1. Fetch Data
    with st.spinner("Fetching dataset..."):
        try:
            response = get_all_recordings()
            data = response.data
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return

    if not data:
        st.info("No recordings found in the database.")
        st.stop()

    # 2. Process Data into DataFrame
    # Flatten metadata and features for easier table viewing
    flat_data = []
    for row in data:
        item = {
            'id': row.get('id'),
            'created_at': row.get('created_at'),
            'user_id': row.get('user_id'), # In real app, might want to hash this or hide it
            'audio_url': row.get('audio_url')
        }
        
        # Unpack metadata
        meta = row.get('metadata', {})
        if isinstance(meta, str):
            try: meta = json.loads(meta)
            except: meta = {}
        
        item.update({
            'age': meta.get('age'),
            'gender': meta.get('gender'),
            'language': meta.get('language'),
            'pd_status': meta.get('pd_status'),
            'source': meta.get('source')
        })
        
        # Unpack features (select a few key ones for summary)
        feats = row.get('features', {})
        if isinstance(feats, str):
            try: feats = json.loads(feats)
            except: feats = {}
            
        item.update({
            'jitter_local': feats.get('jitter_local', 0),
            'shimmer_local': feats.get('shimmer_local', 0),
            'hnr': feats.get('hnr', 0),
            'f0_mean': feats.get('f0_mean', 0),
            'all_features': feats # Keep full object for detailed view
        })
        
        flat_data.append(item)

    df = pd.DataFrame(flat_data)
    df['created_at'] = pd.to_datetime(df['created_at'])

    # 3. Filters
    with st.expander("🔍 Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect("PD Status", options=df['pd_status'].unique(), default=df['pd_status'].unique())
        with col2:
            lang_filter = st.multiselect("Language", options=df['language'].unique(), default=df['language'].unique())
        with col3:
            gender_filter = st.multiselect("Gender", options=df['gender'].unique(), default=df['gender'].unique())

    # Apply filters
    filtered_df = df[
        (df['pd_status'].isin(status_filter)) & 
        (df['language'].isin(lang_filter)) &
        (df['gender'].isin(gender_filter))
    ]

    st.subheader(f"Dataset ({len(filtered_df)} recordings)")
    
    # 4. Data Grid
    # Hide complex columns for the main view
    display_cols = ['created_at', 'age', 'gender', 'language', 'pd_status', 'f0_mean', 'jitter_local', 'hnr', 'source']
    st.dataframe(filtered_df[display_cols], use_container_width=True)

    # 5. Detailed Inspection
    st.subheader("Structure & Feature Inspection")
    selected_row_index = st.number_input("Select Row Index to Inspect", min_value=0, max_value=len(filtered_df)-1, step=1, value=0)
    
    if not filtered_df.empty and selected_row_index < len(filtered_df):
        selected_row = filtered_df.iloc[selected_row_index]
        
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**Participant Details**")
            st.write(f"ID: {selected_row['user_id']}")
            st.write(f"Status: {selected_row['pd_status']}")
            st.write(f"Language: {selected_row['language']}")
            
            if selected_row['audio_url'] and selected_row['audio_url'] != 'not_stored':
                 st.audio(selected_row['audio_url'])
        
        with col_r:
            st.markdown("**Acoustic Biomarkers**")
            st.json(selected_row['all_features'])

    # 6. Basic Stats (Non-ML)
    st.divider()
    st.subheader("Descriptive Statistics")
    
    if not filtered_df.empty:
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Avg Age", f"{filtered_df['age'].mean():.1f}")
        col_s2.metric("Avg F0 (Pitch)", f"{filtered_df['f0_mean'].mean():.2f} Hz")
        col_s3.metric("Avg HNR", f"{filtered_df['hnr'].mean():.2f} dB")
