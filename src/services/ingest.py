"""Email ingestion service for fetching emails from Outlook folders."""

import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from O365 import Message
from src.config import config, CACHE_DIR
from src.auth.graph_auth import graph_auth
from src.models.database import db

logger = logging.getLogger(__name__)


class EmailIngestor:
    """Service for ingesting emails from Outlook folders."""
    
    def __init__(self):
        self.max_attachment_size = config.get_setting('max_attachment_size_mb', 25) * 1024 * 1024
        self.supported_extensions = config.get_setting('supported_file_types', ['.pdf', '.doc', '.docx'])
        self.cache_dir = CACHE_DIR
        
    def get_folders(self) -> List[Dict[str, str]]:
        """Get list of available mail folders."""
        try:
            mailbox = graph_auth.get_mailbox()
            folders = []
            
            # Get all folders recursively
            def traverse_folders(folder, level=0, parent_path=""):
                # Build full path name
                full_name = f"{parent_path}/{folder.name}" if parent_path else folder.name
                
                folders.append({
                    'id': folder.folder_id,
                    'name': folder.name,
                    'full_name': full_name,
                    'level': level,
                    'parent_id': getattr(folder, 'parent_id', None)
                })
                
                # Get child folders
                for child in folder.get_folders():
                    traverse_folders(child, level + 1, full_name)
            
            # Start from root
            for folder in mailbox.get_folders():
                traverse_folders(folder)
            
            return folders
            
        except Exception as e:
            logger.error(f"Error getting folders: {str(e)}")
            return []
    
    def sync_folder(self, folder_id: str, include_subfolders: bool = False) -> Tuple[int, int]:
        """
        Sync emails from specified folder.
        
        Returns:
            Tuple of (processed_count, error_count)
        """
        try:
            mailbox = graph_auth.get_mailbox()
            folder = mailbox.get_folder(folder_id=folder_id)
            
            if not folder:
                raise ValueError(f"Folder not found: {folder_id}")
            
            processed_count = 0
            error_count = 0
            
            # Get messages from folder
            messages = folder.get_messages(
                download_attachments=False,
                query=self._build_query()
            )
            
            with db.get_session() as session:
                for message in messages:
                    try:
                        # Check if already processed
                        if db.get_candidate_by_email_id(session, message.object_id):
                            logger.debug(f"Message already processed: {message.object_id}")
                            continue
                        
                        # Process message
                        if self._process_message(session, message):
                            processed_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing message {message.object_id}: {str(e)}")
                        error_count += 1
                        db.log_processing(
                            session,
                            message.object_id,
                            'fetch',
                            'failed',
                            str(e)
                        )
            
            logger.info(f"Sync completed: {processed_count} processed, {error_count} errors")
            return processed_count, error_count
            
        except Exception as e:
            logger.error(f"Sync error: {str(e)}")
            return 0, 1
    
    def _build_query(self) -> Optional[str]:
        """Build OData query for filtering messages."""
        # Get messages from last N days based on retention setting
        retention_days = config.get_setting('retention_days', 30)
        start_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Build query
        query_parts = [
            f"receivedDateTime ge {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}",
            "hasAttachments eq true"
        ]
        
        return " and ".join(query_parts)
    
    def _process_message(self, session, message: Message) -> bool:
        """Process a single email message."""
        try:
            # Download attachments
            message.attachments.download_attachments()
            
            # Find resume attachments
            resume_attachments = []
            for attachment in message.attachments:
                if self._is_valid_attachment(attachment):
                    resume_attachments.append(attachment)
            
            if not resume_attachments:
                logger.debug(f"No valid attachments in message: {message.object_id}")
                db.log_processing(
                    session,
                    message.object_id,
                    'fetch',
                    'skipped',
                    'No valid resume attachments'
                )
                return False
            
            # Process each attachment
            for attachment in resume_attachments:
                try:
                    # Save attachment to cache
                    file_path = self._save_attachment(attachment, message.object_id)
                    
                    # Calculate hash
                    file_hash = self._calculate_file_hash(file_path)
                    
                    # Check for duplicate
                    if db.get_candidate_by_hash(session, file_hash):
                        logger.info(f"Duplicate resume found: {attachment.name}")
                        db.log_processing(
                            session,
                            message.object_id,
                            'fetch',
                            'skipped',
                            f'Duplicate resume: {attachment.name}'
                        )
                        continue
                    
                    # Create candidate record
                    candidate_data = {
                        'email_id': message.object_id,
                        'email_date': message.received,
                        'sender_email': message.sender.address if message.sender else None,
                        'sender_name': message.sender.name if message.sender else None,
                        'subject': message.subject,
                        'resume_filename': attachment.name,
                        'resume_hash': file_hash,
                        'resume_size_bytes': attachment.size
                    }
                    
                    db.add_candidate(session, candidate_data)
                    
                    db.log_processing(
                        session,
                        message.object_id,
                        'fetch',
                        'success',
                        f'Processed: {attachment.name}'
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing attachment {attachment.name}: {str(e)}")
                    db.log_processing(
                        session,
                        message.object_id,
                        'fetch',
                        'failed',
                        f'Attachment error: {str(e)}'
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return False
    
    def _is_valid_attachment(self, attachment) -> bool:
        """Check if attachment is a valid resume file."""
        # Check size
        if attachment.size > self.max_attachment_size:
            logger.warning(f"Attachment too large: {attachment.name} ({attachment.size} bytes)")
            return False
        
        # Check extension
        file_ext = Path(attachment.name).suffix.lower()
        if file_ext not in self.supported_extensions:
            logger.debug(f"Unsupported file type: {attachment.name}")
            return False
        
        return True
    
    def _save_attachment(self, attachment, email_id: str) -> Path:
        """Save attachment to cache directory."""
        # Create email-specific directory
        email_dir = self.cache_dir / email_id
        email_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = email_dir / attachment.name
        with open(file_path, 'wb') as f:
            f.write(attachment.content)
        
        logger.debug(f"Saved attachment: {file_path}")
        return file_path
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# Global ingestor instance
email_ingestor = EmailIngestor() 