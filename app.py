"""
Publisher Final Delivery App - Streamlit Frontend
Overhauled UI with Modular Tabs, Granular Action Zones, and Final Export Validation.
"""
import streamlit as st
import pandas as pd
import os
import random
from engine import IngestionEngine

st.set_page_config(page_title="Publisher Final Delivery", layout="wide")

# Initialize Engine
if 'engine' not in st.session_state:
    st.session_state.engine = IngestionEngine()

# Safe Path Resolution
for required_path in ["01_VISUAL_REFERENCES", "02_VOICE_GUIDES", "02_VOICE_GUIDES/Council_Personas.json"]:
    if not os.path.exists(required_path):
        st.error(f"Critical Dependency Missing: `{required_path}` was not found on the server. Please check your deployment structure.")

# Initialize Central App Data
if 'app_data' not in st.session_state:
    st.session_state.app_data = {
        'tracks': [], # List of dicts: Title, Keywords, Track Description
        'album_description': '',
        'album_name': '',
        'cover_art': '',
        'mailchimp_intro': ''
    }

if 'ingestion_error' not in st.session_state:
    st.session_state.ingestion_error = None

# --- Sidebar Configuration ---
st.sidebar.title("App Configuration")
api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    st.warning("Missing GEMINI_API_KEY in Streamlit Secrets. Please configure your secrets. AI features will be disabled.")
    
catalog = st.sidebar.selectbox("Active Catalog Persona", ["redCola", "SSC", "EPP"])

st.sidebar.markdown("---")
st.sidebar.title("Waterfall Navigation")
tabs = [
    "Tab 00: The Flight Deck",
    "Tab 01: Keywords & Ingestion",
    "Tab 02: Track Descriptions",
    "Tab 03: Album Description",
    "Tab 04: Album Name",
    "Tab 05: Cover Art",
    "Tab 06: MailChimp Intro",
    "Tab 07: Final Export Gate"
]
active_tab = st.sidebar.radio("Go to:", tabs)

st.title(active_tab)

# Helper function for Council Settings
def render_council_settings(PromptText="No prompt used.", Members="General Council"):
    with st.expander("Council Settings"):
        st.markdown(f"**Active Personas**: {Members}")
        st.code(PromptText, language="text")

# --- Tab 00: The Flight Deck ---
if active_tab == tabs[0]:
    st.write("### Welcome to the Publisher Final Delivery App")
    st.info("**Philosophy Statement**: *Never Guess. Always Reference.*")
    st.markdown("""
    This application utilizes the **Drawer of Personas** to enforce rigid brand guidelines across all generated text and imagery.
    
    ### How to Use the App:
    - Flow through Tabs 01 to 06 sequentially. 
    - The AI builds context continuously through `st.session_state`.
    - Edit outputs directly in the text boxes or data editors provided.
    - Export the final package at Tab 07, assuming the data passes the Clean Room validation.
    """)
    if st.button("Clear All Session Data", type="primary"):
        st.session_state.app_data = {
            'tracks': [], 'album_description': '', 'album_name': '',
            'cover_art': '', 'mailchimp_intro': ''
        }
        st.success("Session Cleared.")

# --- Tab 01: Keywords & Ingestion ---
elif active_tab == tabs[1]:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Action Zone: Ingestion")
        uploaded_files = st.file_uploader("Upload Master Audio", type=['mp3', 'wav'], accept_multiple_files=True)
        if st.button("Run AI Analysis", disabled=not uploaded_files):
            with st.spinner("Analyzing audio..."):
                for uploaded_file in uploaded_files:
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    try:
                        metadata = st.session_state.engine.analyze_audio_file(temp_path, catalog, api_key)
                        
                        if metadata:
                            clean_name = os.path.splitext(uploaded_file.name)[0].lstrip('0123456789 -')
                            st.session_state.app_data['tracks'].append({
                                'Title': metadata.get("Title", clean_name),
                                'Keywords': metadata.get("Keywords", ""),
                                'Track Description': metadata.get("Description", "")
                            })
                    except Exception as e:
                        import traceback
                        st.session_state.ingestion_error = f"🚨 Analysis Failed for {uploaded_file.name}: {str(e)}\n\nTraceback: {traceback.format_exc()}"
                    finally:
                        if os.path.exists(temp_path): os.remove(temp_path)
                        
                st.success("Analysis Complete!")
                st.rerun()

    with col2:
        st.subheader("Data Editor")
        
        # Display pinned error if exists
        if st.session_state.ingestion_error:
            st.error(st.session_state.ingestion_error)
            if st.button("Dismiss Error"):
                st.session_state.ingestion_error = None
                st.rerun()
                
        if st.session_state.app_data['tracks']:
            df = pd.DataFrame(st.session_state.app_data['tracks'])
            edited_df = st.data_editor(df, use_container_width=True, key="editor_tab1", num_rows="dynamic")
            st.session_state.app_data['tracks'] = edited_df.to_dict('records')
            
            # Local Download
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Keywords CSV", csv, "Keywords.csv", "text/csv")
        else:
            st.info("No tracks ingested yet.")

    render_council_settings(
        PromptText=st.session_state.engine.prompts.generate_keywords_analysis_prompt(catalog),
        Members="Music Supervisor & Lead Video Editor"
    )

# --- Tab 02: Track Descriptions ---
elif active_tab == tabs[2]:
    if not st.session_state.app_data['tracks']:
        st.warning("Please ingest tracks in Tab 01 first.")
    else:
        st.subheader("Action Zone: Generate 3-Sentence Arcs")
        if st.button("Generate Descriptions"):
             with st.spinner("Council Auditing Descriptions..."):
                 updated = []
                 for track in st.session_state.app_data['tracks']:
                     sys_instr, prompt = st.session_state.engine.prompts.generate_track_description_prompt(
                         track['Title'], track.get('Track Description', ''), catalog
                     )
                     new_desc = st.session_state.engine.call_gemini('gemini-3.1-pro', sys_instr, prompt, api_key)
                     track['Track Description'] = new_desc
                     updated.append(track)
                 st.session_state.app_data['tracks'] = updated
                 st.success("Descriptions updated!")
                 st.rerun()
                 
        col1, col2 = st.columns([1, 1])
        with col1:
             st.write("AI Output Preview")
             for t in st.session_state.app_data['tracks']:
                 st.markdown(f"**{t['Title']}**: {t.get('Track Description', '')}")
                 
        with col2:
             df = pd.DataFrame(st.session_state.app_data['tracks'])
             edited_df = st.data_editor(df, use_container_width=True, key="editor_tab2", disabled=['Title', 'Keywords'])
             st.session_state.app_data['tracks'] = edited_df.to_dict('records')
             
             csv = edited_df.to_csv(index=False).encode('utf-8')
             st.download_button("Download Descriptions CSV", csv, "Descriptions.csv", "text/csv")

        sys_instr, t_prompt = st.session_state.engine.prompts.generate_track_description_prompt("Example", "Example", catalog)
        render_council_settings(sys_instr, Members="Head of A&R, Lead Editor, Gatekeeper")

# --- Tab 03: Album Description ---
elif active_tab == tabs[3]:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Action Zone: Macro Summary")
        if st.button("Synthesize Album Description"):
            with st.spinner("Synthesizing..."):
                descs = [t.get('Track Description', '') for t in st.session_state.app_data['tracks']]
                sys_instr, prompt = st.session_state.engine.prompts.generate_album_description_prompt(descs, catalog)
                res = st.session_state.engine.call_gemini('gemini-3.1-pro', sys_instr, prompt, api_key)
                st.session_state.app_data['album_description'] = res
                st.rerun()
                
    with col2:
        st.subheader("Editable Output")
        edited_text = st.text_area("Album Description", value=st.session_state.app_data['album_description'], height=150)
        st.session_state.app_data['album_description'] = edited_text
        
        if edited_text:
             st.download_button("Download Text", edited_text.encode('utf-8'), "Album_Description.txt", "text/plain")

    sys_instr, t_prompt = st.session_state.engine.prompts.generate_album_description_prompt(["Example"], catalog)
    render_council_settings(sys_instr, Members="The Arbitrator")

# --- Tab 04: Album Name ---
elif active_tab == tabs[4]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Action Zone: Verbose Sampling")
        if st.button("Brainstorm Names"):
             with st.spinner("Generating 5 concepts..."):
                 sys_instr, prompt = st.session_state.engine.prompts.generate_album_name_prompt(st.session_state.app_data['album_description'], catalog)
                 res = st.session_state.engine.call_gemini('gemini-3.1-flash', sys_instr, prompt, api_key)
                 st.session_state.app_data['album_name'] = res
                 st.rerun()
                 
    with col2:
        st.subheader("Editable Output")
        edited_text = st.text_area("Album Name Concepts", value=st.session_state.app_data['album_name'], height=200)
        st.session_state.app_data['album_name'] = edited_text
        if edited_text:
             st.download_button("Download Text", edited_text.encode('utf-8'), "Album_Name.txt", "text/plain")

    sys_instr, t_prompt = st.session_state.engine.prompts.generate_album_name_prompt("Example", catalog)
    render_council_settings(sys_instr, Members="The Arbitrator & Brand Gatekeeper")

# --- Tab 05: Cover Art ---
elif active_tab == tabs[5]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Action Zone: Visual Prompts")
        if st.button("Generate MidJourney Prompts"):
             with st.spinner("Generating prompts..."):
                 # Get References
                 refs = []
                 cat_folder = st.session_state.engine.root_path / "01_VISUAL_REFERENCES" / catalog
                 if cat_folder.exists():
                     refs = [f"https://placeholder.url/{f.name}" for f in cat_folder.iterdir() if f.is_file() and not f.name.startswith('.')]
                 if not refs:
                     refs = ["https://dummy.url/ref1.jpg"] * 4 # Fallback
                     
                 # Select 4 random refs
                 selected_refs = random.choices(refs, k=4)
                 
                 sys_instr, prompt = st.session_state.engine.prompts.generate_cover_art_prompt(
                     st.session_state.app_data['album_name'],
                     st.session_state.app_data['album_description'],
                     catalog,
                     selected_refs
                 )
                 res = st.session_state.engine.call_gemini('gemini-3.1-pro', sys_instr, prompt, api_key)
                 st.session_state.app_data['cover_art'] = res
                 st.rerun()

    with col2:
        st.subheader("Editable MidJourney Output")
        edited_text = st.text_area("MidJourney v7 Prompts", value=st.session_state.app_data['cover_art'], height=300)
        st.session_state.app_data['cover_art'] = edited_text
        if edited_text:
             st.download_button("Download Text", edited_text.encode('utf-8'), "Cover_Art_Prompts.txt", "text/plain")

    sys_instr, t_prompt = st.session_state.engine.prompts.generate_cover_art_prompt("Example", "Example", catalog, ["URL"])
    render_council_settings(sys_instr, Members="Art Director & Brand Gatekeeper")

# --- Tab 06: MailChimp Intro ---
elif active_tab == tabs[6]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Action Zone: Marketing Memo")
        if st.button("Generate MailChimp Memo"):
             with st.spinner("Writing copy..."):
                 sys_instr, prompt = st.session_state.engine.prompts.generate_mailchimp_intro_prompt(
                     st.session_state.app_data['album_name'],
                     st.session_state.app_data['album_description'],
                     catalog
                 )
                 res = st.session_state.engine.call_gemini('gemini-3.1-pro', sys_instr, prompt, api_key)
                 st.session_state.app_data['mailchimp_intro'] = res
                 st.rerun()
                 
    with col2:
        st.subheader("Editable Output")
        edited_text = st.text_area("MailChimp Copy", value=st.session_state.app_data['mailchimp_intro'], height=300)
        st.session_state.app_data['mailchimp_intro'] = edited_text
        if edited_text:
             st.download_button("Download Text", edited_text.encode('utf-8'), "MailChimp_Intro.txt", "text/plain")

    sys_instr, t_prompt = st.session_state.engine.prompts.generate_mailchimp_intro_prompt("Example", "Example", catalog)
    render_council_settings(sys_instr, Members="Copywriter, Supervisor, Gatekeeper, Arbitrator")

# --- Tab 07: Final Export Gate ---
elif active_tab == tabs[7]:
    st.header("The Clean Room Validator")
    st.markdown("Running Data Integrity Firewall checks before allowing export...")
    
    passed, errors = st.session_state.engine.validate_data(st.session_state.app_data)
    
    if not passed:
        st.error(f"FATAL ERRORS DETECTED ({len(errors)}). EXPORT BLOCKED.")
        for msg in errors:
            st.warning(msg)
        st.info("Please navigate back to the respective tabs and correct the data in the Data Editors.")
    else:
        st.success("CLEAN ROOM PASSED ✅ All integrity checks validated.")
        st.markdown("Your Final Delivery Package is ready.")
        
        # Compile Zip
        zip_buffer = st.session_state.engine.compile_final_package(st.session_state.app_data)
        
        st.download_button(
            label="[Generate Final Delivery Package]",
            data=zip_buffer,
            file_name=f"{catalog}_Final_Delivery.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )
