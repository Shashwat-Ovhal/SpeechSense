import streamlit as st
import pandas as pd
import json
from supabase_client import get_all_recordings

def render_admin_view():
    st.header("Admin Dashboard")
    st.markdown("System Overview, Statistics, and Data Management.")

    # 1. Fetch Data
    with st.spinner("Fetching system data..."):
        try:
            response = get_all_recordings()
            data = response.data
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return

    if not data:
        st.info("No data available.")
        return

    # Process Data
    flat_data = []
    for row in data:
        item = row.copy() # Start with all base fields
        
        # Flatten metadata
        meta = row.get('metadata', {})
        if isinstance(meta, str):
             try: meta = json.loads(meta)
             except: meta = {}
        
        for k, v in meta.items():
            item[f"meta_{k}"] = v
            
        # Flatten features (just counts or key stats)
        feats = row.get('features', {})
        if isinstance(feats, str):
            try: feats = json.loads(feats)
            except: feats = {}
            
        item['feature_count'] = len(feats)
        flat_data.append(item)
        
    df = pd.DataFrame(flat_data)
    df['created_at'] = pd.to_datetime(df['created_at'])

    # 2. Key Metrics
    st.subheader("System Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Recordings", len(df))
    col2.metric("Unique Users", df['user_id'].nunique())
    
    # Calculate breakdown
    pd_count = len(df[df['meta_pd_status'] == "Parkinson's Disease"]) if 'meta_pd_status' in df.columns else 0
    control_count = len(df[df['meta_pd_status'] == "Healthy Control"]) if 'meta_pd_status' in df.columns else 0
    
    col3.metric("PD Patients", pd_count)
    col4.metric("Controls", control_count)

    # 3. Time Series
    st.subheader("Growth")
    if not df.empty:
        daily_counts = df.set_index('created_at').resample('D').size()
        st.line_chart(daily_counts)

    # 4. Data Export
    st.subheader("Data Management")
    st.markdown("Download full dataset for research usage.")
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Full Dataset (CSV)",
        data=csv,
        file_name='speechsense_full_dataset.csv',
        mime='text/csv',
    )
    
    # 5. Data Management (Delete)
    st.divider()
    st.subheader("⚠️ Dangerous Zone: Data Management")
    st.markdown("Select a recording to permanently delete from the database.")
    
    # Create a cleaner selectbox label
    # We use a tuple of (label, index) to track selection, or just match by ID
    # Let's map ID to a display string
    
    if not df.empty:
        # Create a dictionary for mapping: "ID | User | Date" -> ID
        options_map = {
             f"{row['id']} | {row['user_id'][:8]}... | {row['created_at'].strftime('%Y-%m-%d %H:%M')}": row['id'] 
             for _, row in df.iterrows()
        }
        
        selected_option = st.selectbox("Select Recording to Delete", options=list(options_map.keys()))
        
        if selected_option:
            selected_id = options_map[selected_option]
            
            if st.button("🗑️ Permanently Delete Recording", type="primary"):
                # Confirmation is good but Streamlit modals are tricky, so we use a checkbox or just button
                # For safety, let's use a checkbox confirmation pattern
                pass # logic handled below

            confirm_delete = st.checkbox("I confirm that this action cannot be undone.")
            if confirm_delete and st.button("Confirm Delete"):
                with st.spinner("Deleting..."):
                    from supabase_client import delete_recording
                    try:
                        delete_recording(selected_id)
                        st.success("Recording deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Deletion failed: {e}")
    else:
        st.info("No data to manage.")
