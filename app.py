"""CVLens-Agent - Streamlit UI Application."""

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import logging
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="CVLens-Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import after streamlit to avoid import issues
from src.config import config
from src.auth.graph_auth import graph_auth
from src.services.ingest import email_ingestor
from src.services.parse import resume_parser
from src.services.score import candidate_scorer
from src.models.database import db

logger = logging.getLogger(__name__)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'selected_folder' not in st.session_state:
    st.session_state.selected_folder = None
if 'sync_in_progress' not in st.session_state:
    st.session_state.sync_in_progress = False


def main():
    """Main application entry point."""
    st.title("📄 CVLens-Agent")
    st.markdown("**Privacy-first resume screening from your Outlook inbox**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Authentication section
        if not st.session_state.authenticated:
            if st.button("🔐 Authenticate with Microsoft", type="primary"):
                authenticate()
        else:
            user_info = graph_auth.get_user_info()
            if user_info:
                st.success(f"✅ Logged in as: {user_info.get('display_name', 'Unknown')}")
            
            if st.button("🚪 Logout"):
                logout()
        
        st.divider()
        
        # Folder selection
        if st.session_state.authenticated:
            folder_selection()
        
        st.divider()
        
        # Data management
        st.header("🗑️ Data Management")
        if st.button("🧹 Purge All Data", type="secondary"):
            if st.checkbox("I understand this will delete all data"):
                purge_data()
    
    # Main content area
    if not st.session_state.authenticated:
        show_welcome_screen()
    elif not st.session_state.selected_folder:
        show_folder_selection_prompt()
    else:
        show_dashboard()


def authenticate():
    """Handle Microsoft authentication."""
    with st.spinner("🔄 Starting authentication flow..."):
        try:
            # Show device code info
            st.info("""
            **Device Code Authentication**
            
            1. A browser window will open shortly
            2. Enter the code displayed in the console
            3. Sign in with your Microsoft account
            4. Return here once authenticated
            """)
            
            # Authenticate
            if graph_auth.authenticate():
                st.session_state.authenticated = True
                st.success("✅ Authentication successful!")
                st.rerun()
            else:
                st.error("❌ Authentication failed. Please try again.")
                
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            logger.error(f"Authentication error: {str(e)}")


def logout():
    """Handle logout."""
    graph_auth.logout()
    st.session_state.authenticated = False
    st.session_state.selected_folder = None
    st.success("✅ Logged out successfully")
    st.rerun()


def folder_selection():
    """Handle folder selection."""
    st.header("📁 Folder Selection")
    
    try:
        # Get folders
        folders = email_ingestor.get_folders()
        
        if not folders:
            st.warning("No folders found. Please check your permissions.")
            return
        
        # Create folder options
        folder_options = {f"{f['full_name']} ({f['name']})": f['id'] for f in folders}
        
        # Get current folder
        current_folder_id = config.get_setting('folder_id')
        current_folder_name = None
        
        if current_folder_id:
            for name, fid in folder_options.items():
                if fid == current_folder_id:
                    current_folder_name = name
                    break
        
        # Folder selector
        selected_name = st.selectbox(
            "Select email folder:",
            options=list(folder_options.keys()),
            index=list(folder_options.keys()).index(current_folder_name) if current_folder_name else 0
        )
        
        selected_id = folder_options[selected_name]
        
        # Include subfolders option
        include_subfolders = st.checkbox(
            "Include subfolders",
            value=config.get_setting('include_subfolders', False)
        )
        
        # Save button
        if st.button("💾 Save Folder Selection"):
            config.update_setting('folder_id', selected_id)
            config.update_setting('folder_name', selected_name)
            config.update_setting('include_subfolders', include_subfolders)
            st.session_state.selected_folder = selected_id
            st.success(f"✅ Selected folder: {selected_name}")
            st.rerun()
            
    except Exception as e:
        st.error(f"Error loading folders: {str(e)}")
        logger.error(f"Folder selection error: {str(e)}")


def show_welcome_screen():
    """Show welcome screen for unauthenticated users."""
    st.markdown("""
    ## Welcome to CVLens-Agent! 👋
    
    CVLens-Agent helps you streamline your hiring process by:
    - 📧 Automatically collecting resumes from your Outlook folders
    - 📄 Parsing PDF and Word documents
    - 🎯 Scoring candidates against your job requirements
    - 🔒 Keeping all data local and encrypted
    
    ### Getting Started
    
    1. Click **Authenticate with Microsoft** in the sidebar
    2. Follow the device code authentication flow
    3. Select your recruitment email folder
    4. Start syncing and reviewing candidates!
    
    ### Privacy First 🔐
    
    All processing happens locally on your machine. No resume data leaves your computer.
    """)


def show_folder_selection_prompt():
    """Show prompt to select a folder."""
    st.info("📁 Please select an email folder from the sidebar to begin.")


def show_dashboard():
    """Show main dashboard."""
    st.header("📊 Candidate Dashboard")
    
    # Sync controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        if st.button("🔄 Sync Emails", type="primary", disabled=st.session_state.sync_in_progress):
            run_sync_pipeline()
    
    with col2:
        auto_sync = st.checkbox("Auto-sync", value=config.get_setting('auto_poll_enabled', False))
        if auto_sync != config.get_setting('auto_poll_enabled', False):
            config.update_setting('auto_poll_enabled', auto_sync)
    
    with col3:
        if st.button("📊 Export CSV"):
            export_candidates()
    
    with col4:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Show sync progress
    if st.session_state.sync_in_progress:
        show_sync_progress()
    
    # Candidate list
    show_candidate_list()


def run_sync_pipeline():
    """Run the full sync pipeline."""
    st.session_state.sync_in_progress = True
    
    progress_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Sync emails
            status_text.text("📧 Syncing emails...")
            progress_bar.progress(0.1)
            
            folder_id = st.session_state.selected_folder
            processed, errors = email_ingestor.sync_folder(folder_id)
            
            status_text.text(f"📧 Synced {processed} emails ({errors} errors)")
            progress_bar.progress(0.4)
            
            # Step 2: Parse resumes
            status_text.text("📄 Parsing resumes...")
            parsed, parse_errors = resume_parser.parse_all_pending()
            
            status_text.text(f"📄 Parsed {parsed} resumes ({parse_errors} errors)")
            progress_bar.progress(0.7)
            
            # Step 3: Score candidates
            status_text.text("🎯 Scoring candidates...")
            scored, score_errors = candidate_scorer.score_all_pending()
            
            status_text.text(f"🎯 Scored {scored} candidates ({score_errors} errors)")
            progress_bar.progress(1.0)
            
            # Complete
            time.sleep(1)
            st.success(f"✅ Sync complete! Processed {processed} emails, parsed {parsed} resumes, scored {scored} candidates.")
            
        except Exception as e:
            st.error(f"Sync error: {str(e)}")
            logger.error(f"Sync pipeline error: {str(e)}")
        
        finally:
            st.session_state.sync_in_progress = False
            st.rerun()


def show_sync_progress():
    """Show sync progress indicator."""
    st.info("🔄 Sync in progress... Please wait.")


def show_candidate_list():
    """Show list of candidates."""
    try:
        # Get candidates from database
        with db.get_session() as session:
            from src.models.database import Candidate
            candidates = session.query(Candidate).order_by(
                Candidate.score.desc()
            ).all()
            
            if not candidates:
                st.info("No candidates found. Click **Sync Emails** to fetch resumes.")
                return
            
            # Convert to dataframe
            candidate_data = []
            for candidate in candidates:
                decrypted = candidate.to_dict(db.cipher)
                candidate_data.append({
                    'ID': candidate.id,
                    'Name': decrypted.get('candidate_name', 'Unknown'),
                    'Email': decrypted.get('candidate_email', 'N/A'),
                    'Score': f"{candidate.score:.1f}",
                    'Status': candidate.status.title(),
                    'Date': candidate.email_date.strftime('%Y-%m-%d'),
                    'Resume': candidate.resume_filename
                })
            
            df = pd.DataFrame(candidate_data)
            
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox(
                    "Status",
                    options=['All', 'New', 'Interested', 'Pass'],
                    index=0
                )
            
            with col2:
                min_score = st.slider("Min Score", 0, 100, 0)
            
            with col3:
                search_term = st.text_input("Search", placeholder="Name or email...")
            
            # Apply filters
            if status_filter != 'All':
                df = df[df['Status'] == status_filter]
            
            df = df[df['Score'].astype(float) >= min_score]
            
            if search_term:
                mask = (
                    df['Name'].str.contains(search_term, case=False, na=False) |
                    df['Email'].str.contains(search_term, case=False, na=False)
                )
                df = df[mask]
            
            # Display candidates
            st.subheader(f"📋 Candidates ({len(df)})")
            
            # Create expandable rows for each candidate
            for idx, row in df.iterrows():
                with st.expander(f"{row['Name']} - Score: {row['Score']} - {row['Status']}"):
                    show_candidate_details(row['ID'])
                    
    except Exception as e:
        st.error(f"Error loading candidates: {str(e)}")
        logger.error(f"Candidate list error: {str(e)}")


def show_candidate_details(candidate_id: int):
    """Show detailed view of a candidate."""
    try:
        with db.get_session() as session:
            from src.models.database import Candidate
            candidate = session.query(Candidate).filter_by(id=candidate_id).first()
            
            if not candidate:
                st.error("Candidate not found")
                return
            
            decrypted = candidate.to_dict(db.cipher)
            
            # Basic info
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Contact Information**")
                st.text(f"Name: {decrypted.get('candidate_name', 'Unknown')}")
                st.text(f"Email: {decrypted.get('candidate_email', 'N/A')}")
                st.text(f"Phone: {decrypted.get('candidate_phone', 'N/A')}")
            
            with col2:
                st.markdown("**Application Details**")
                st.text(f"Received: {candidate.email_date.strftime('%Y-%m-%d %H:%M')}")
                st.text(f"From: {candidate.sender_email}")
                st.text(f"Resume: {candidate.resume_filename}")
            
            # Score breakdown
            if candidate.score_breakdown:
                st.markdown("**Score Breakdown**")
                breakdown = decrypted.get('score_breakdown', {})
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    skills = breakdown.get('skills', {})
                    st.metric("Skills", f"{skills.get('score', 0)*100:.0f}%")
                    if skills.get('matched_skills'):
                        st.caption(f"Matched: {', '.join(skills['matched_skills'][:5])}")
                
                with col2:
                    education = breakdown.get('education', {})
                    st.metric("Education", f"{education.get('score', 0)*100:.0f}%")
                
                with col3:
                    experience = breakdown.get('experience', {})
                    st.metric("Experience", f"{experience.get('score', 0)*100:.0f}%")
                    st.caption(f"Years: {experience.get('total_years', 0):.1f}")
            
            # Actions
            st.markdown("**Actions**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✅ Interested", key=f"interested_{candidate_id}"):
                    update_candidate_status(candidate_id, 'interested')
            
            with col2:
                if st.button("❌ Pass", key=f"pass_{candidate_id}"):
                    update_candidate_status(candidate_id, 'pass')
            
            with col3:
                if st.button("↩️ Reset", key=f"reset_{candidate_id}"):
                    update_candidate_status(candidate_id, 'new')
            
            with col4:
                # Download resume button
                cache_path = Path(config.CACHE_DIR) / candidate.email_id / candidate.resume_filename
                if cache_path.exists():
                    with open(cache_path, 'rb') as f:
                        st.download_button(
                            "📥 Resume",
                            data=f.read(),
                            file_name=candidate.resume_filename,
                            mime="application/octet-stream",
                            key=f"download_{candidate_id}"
                        )
            
            # Notes
            st.markdown("**Notes**")
            current_notes = decrypted.get('notes', '')
            new_notes = st.text_area(
                "Add notes",
                value=current_notes,
                key=f"notes_{candidate_id}",
                height=100
            )
            
            if new_notes != current_notes:
                if st.button("💾 Save Notes", key=f"save_notes_{candidate_id}"):
                    save_candidate_notes(candidate_id, new_notes)
                    
    except Exception as e:
        st.error(f"Error showing candidate details: {str(e)}")
        logger.error(f"Candidate details error: {str(e)}")


def update_candidate_status(candidate_id: int, status: str):
    """Update candidate status."""
    try:
        with db.get_session() as session:
            if db.update_candidate_status(session, candidate_id, status):
                st.success(f"✅ Status updated to: {status}")
                st.rerun()
            else:
                st.error("Failed to update status")
    except Exception as e:
        st.error(f"Error updating status: {str(e)}")


def save_candidate_notes(candidate_id: int, notes: str):
    """Save candidate notes."""
    try:
        with db.get_session() as session:
            from src.models.database import Candidate
            candidate = session.query(Candidate).filter_by(id=candidate_id).first()
            if candidate:
                candidate.notes = db.cipher.encrypt(notes) if notes else None
                session.commit()
                st.success("✅ Notes saved")
                st.rerun()
    except Exception as e:
        st.error(f"Error saving notes: {str(e)}")


def export_candidates():
    """Export candidates to CSV."""
    try:
        with db.get_session() as session:
            from src.models.database import Candidate
            candidates = session.query(Candidate).all()
            
            if not candidates:
                st.warning("No candidates to export")
                return
            
            # Create export data
            export_data = []
            for candidate in candidates:
                decrypted = candidate.to_dict(db.cipher)
                export_data.append({
                    'Name': decrypted.get('candidate_name', 'Unknown'),
                    'Email': decrypted.get('candidate_email', ''),
                    'Phone': decrypted.get('candidate_phone', ''),
                    'Score': candidate.score,
                    'Status': candidate.status,
                    'Skills': ', '.join(decrypted.get('skills', [])),
                    'Education': ', '.join([e.get('text', '') for e in decrypted.get('education', [])]),
                    'Experience Years': sum(e.get('years', 0) for e in decrypted.get('experience', [])),
                    'Resume': candidate.resume_filename,
                    'Received Date': candidate.email_date.strftime('%Y-%m-%d'),
                    'Notes': decrypted.get('notes', '')
                })
            
            df = pd.DataFrame(export_data)
            
            # Generate CSV
            csv = df.to_csv(index=False)
            
            # Download button
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"Export error: {str(e)}")
        logger.error(f"Export error: {str(e)}")


def purge_data():
    """Purge all data from the system."""
    try:
        if db.purge_all_data():
            # Also clear cache directory
            import shutil
            if config.CACHE_DIR.exists():
                shutil.rmtree(config.CACHE_DIR)
                config.CACHE_DIR.mkdir(exist_ok=True)
            
            st.success("✅ All data has been purged")
            st.rerun()
        else:
            st.error("Failed to purge data")
    except Exception as e:
        st.error(f"Purge error: {str(e)}")
        logger.error(f"Purge error: {str(e)}")


if __name__ == "__main__":
    # Check if authenticated on startup
    if graph_auth.is_authenticated():
        st.session_state.authenticated = True
    
    # Check for saved folder
    folder_id = config.get_setting('folder_id')
    if folder_id:
        st.session_state.selected_folder = folder_id
    
    # Run main app
    main() 