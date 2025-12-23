import streamlit as st
import pandas as pd
import json
from supabase_client import get_all_recordings
from views.components import render_recording_section

def render_doctor_view():
    st.header("Medical Associate / Doctor Dashboard")
    
    tab1, tab2 = st.tabs(["📊 Data Explorer", "🎙️ New Patient Session"])
    
    # --- Tab 1: Data View (Existing Logic) ---
    with tab1:
        render_data_explorer()
        
    # --- Tab 2: Recording (New Feature) ---
    with tab2:
        st.info("Record audio for a patient during a clinical visit. This data is marked as 'Doctor Verified'.")
        render_recording_section(source_role="doctor")

def render_data_explorer():
    # 1. Fetch Data
    with st.spinner("Fetching dataset..."):
        try:
            response = get_all_recordings()
            data = response.data
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return

    if not data:
        st.info("No recordings found.")
        return

    # 2. Process Data
    flat_data = []
    for row in data:
        item = {
            'id': row.get('id'),
            'created_at': row.get('created_at'),
            'audio_url': row.get('audio_url')
        }
        
        # Meta
        meta = row.get('metadata', {})
        if isinstance(meta, str):
            try: meta = json.loads(meta)
            except: meta = {}
        
        item.update({
            'subject_id': meta.get('subject_id', 'anon'),
            'age': meta.get('age'),
            'gender': meta.get('gender'),
            'language': meta.get('language'),
            'pd_status': meta.get('pd_status'),
            'recorded_by': meta.get('recorded_by_role', 'unknown'), # patient vs doctor
            'notes': meta.get('notes')
        })
        
        # Features (summary)
        feats = row.get('features', {})
        if isinstance(feats, str):
            try: feats = json.loads(feats)
            except: feats = {}
            
        item.update({
            'jitter': feats.get('jitter_local', 0),
            'shimmer': feats.get('shimmer_local', 0),
            'full_features': feats
        })
        
        flat_data.append(item)

    df = pd.DataFrame(flat_data)
    df['created_at'] = pd.to_datetime(df['created_at'])

    # 3. Filters
    with st.expander("🔍 Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            # Filter by "Recorded By" (Authenticity check)
            rec_filter = st.multiselect("Recorded By", options=df['recorded_by'].unique(), default=df['recorded_by'].unique())
        with col2:
            status_filter = st.multiselect("PD Status", options=df['pd_status'].unique(), default=df['pd_status'].unique())
        with col3:
            lang_filter = st.multiselect("Language", options=df['language'].unique(), default=df['language'].unique())

    # Apply
    filtered_df = df[
        (df['recorded_by'].isin(rec_filter)) &
        (df['pd_status'].isin(status_filter)) & 
        (df['language'].isin(lang_filter))
    ]

    st.subheader(f"Clinical Dataset ({len(filtered_df)} records)")
    
    # Grid
    display_cols = ['created_at', 'recorded_by', 'subject_id', 'pd_status', 'age', 'language', 'jitter', 'shimmer']
    st.dataframe(filtered_df[display_cols], use_container_width=True)

    # Detailed View
    st.divider()
    st.markdown("### Selected Record Detail")
    
    # Select by ID logic or simple index
    if not filtered_df.empty:
        sel_idx = st.selectbox("Select Record ID", options=filtered_df.index, format_func=lambda x: f"{filtered_df.loc[x, 'subject_id']} ({filtered_df.loc[x, 'created_at']})")
        
        row = filtered_df.loc[sel_idx]
        c1, c2 = st.columns(2)
        with c1:
            st.json({k:v for k,v in row.items() if k != 'full_features'})
        with c2:
            st.write("Acoustic Features:")
            st.json(row['full_features'])
