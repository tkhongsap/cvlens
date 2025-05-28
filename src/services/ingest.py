"""Email ingestion service for fetching emails from Outlook folders."""

import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from O365 import Message
from src.config import config, CACHE_DIR
from src.auth.graph_auth import graph_auth
from src.models.file_storage import file_storage
from src.models.candidate import CandidateData

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
            
            for message in messages:
                try:
                    # Process message (removed duplicate check to force reprocessing)
                    if self._process_message(message):
                        processed_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing message {message.object_id}: {str(e)}")
                    error_count += 1
                    file_storage.log_processing(
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
    
    def _process_message(self, message: Message) -> bool:
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
                file_storage.log_processing(
                    message.object_id,
                    'fetch',
                    'skipped',
                    'No valid resume attachments'
                )
                return False
            
            # Save all valid attachments first
            saved_attachments = []
            for attachment in resume_attachments:
                try:
                    file_path = self._save_attachment(attachment, message.object_id)
                    file_hash = self._calculate_file_hash(file_path)
                    
                    # Save all valid attachments (removed duplicate check for now)
                    saved_attachments.append({
                        'name': attachment.name,
                        'path': file_path,
                        'hash': file_hash,
                        'size': attachment.size
                    })
                
                except Exception as e:
                    logger.error(f"Error processing attachment {attachment.name}: {str(e)}")
            
            if not saved_attachments:
                logger.info(f"No new attachments to process for message: {message.object_id}")
                file_storage.log_processing(
                    message.object_id,
                    'fetch',
                    'skipped',
                    'All attachments were duplicates'
                )
                return False
            
            # Select the best resume file (prioritize by name patterns and size)
            best_attachment = self._select_best_resume(saved_attachments)
            
            # Extract email content
            email_content = self._extract_email_content(message)
            
            # Create single candidate record with the best resume
            candidate = CandidateData(
                email_id=message.object_id,
                email_date=message.received,
                sender_email=message.sender.address if message.sender else "",
                sender_name=message.sender.name if message.sender else "",
                subject=message.subject or "",
                resume_filename=best_attachment['name'],
                resume_hash=best_attachment['hash'],
                resume_size_bytes=best_attachment['size']
            )
            
            # Save candidate metadata
            if file_storage.save_candidate_metadata(candidate):
                attachment_names = [att['name'] for att in saved_attachments]
                file_storage.log_processing(
                    message.object_id,
                    'fetch',
                    'success',
                    f'Processed {len(saved_attachments)} attachments: {", ".join(attachment_names)}. Primary: {best_attachment["name"]}'
                )
                return True
            else:
                file_storage.log_processing(
                    message.object_id,
                    'fetch',
                    'failed',
                    f'Failed to save metadata for: {best_attachment["name"]}'
                )
                return False
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return False
    
    def _select_best_resume(self, attachments: List[Dict]) -> Dict:
        """Select the best resume file from multiple attachments."""
        if len(attachments) == 1:
            return attachments[0]
        
        # Score each attachment
        scored_attachments = []
        for att in attachments:
            score = 0
            filename_lower = att['name'].lower()
            
            # Prefer files with "resume" or "cv" in name
            if 'resume' in filename_lower:
                score += 10
            elif 'cv' in filename_lower:
                score += 8
            elif any(word in filename_lower for word in ['curriculum', 'vitae']):
                score += 6
            
            # Prefer larger files (more content)
            if att['size'] > 200000:  # > 200KB
                score += 5
            elif att['size'] > 100000:  # > 100KB
                score += 3
            elif att['size'] > 50000:   # > 50KB
                score += 1
            
            # Prefer PDF over other formats
            if att['name'].lower().endswith('.pdf'):
                score += 2
            
            scored_attachments.append((score, att))
        
        # Return the highest scored attachment
        scored_attachments.sort(key=lambda x: x[0], reverse=True)
        best_attachment = scored_attachments[0][1]
        
        logger.info(f"Selected best resume: {best_attachment['name']} from {len(attachments)} attachments")
        return best_attachment
    
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
        
        # Check filename patterns to exclude non-resume documents
        filename_lower = attachment.name.lower()
        
        # Exclude common non-resume document patterns (more comprehensive)
        exclude_patterns = [
            'nda', 'non-disclosure', 'agreement', 'contract', 'form', 'application',
            'consent', 'template', 'policy', 'terms', 'conditions', 'waiver',
            'release', 'authorization', 'permission', 'disclaimer', 'tcctech',
            'pdpa', 'revision', 'transcript', 'certificate', 'diploma'
        ]
        
        for pattern in exclude_patterns:
            if pattern in filename_lower:
                logger.info(f"Excluding non-resume document: {attachment.name} (contains '{pattern}')")
                return False
        
        # Prefer files with resume-like names
        resume_patterns = ['resume', 'cv', 'curriculum', 'vitae', 'profile', 'bio']
        has_resume_pattern = any(pattern in filename_lower for pattern in resume_patterns)
        
        # If it's a small file (< 50KB) and doesn't have resume patterns, it's likely not a resume
        if attachment.size < 50000 and not has_resume_pattern:
            logger.info(f"Excluding small non-resume file: {attachment.name} ({attachment.size} bytes)")
            return False
        
        # Log what we're accepting
        logger.info(f"Accepting potential resume file: {attachment.name} ({attachment.size} bytes)")
        return True
    
    def _save_attachment(self, attachment, email_id: str) -> Path:
        """Save attachment to candidate directory."""
        # Create candidate-specific directory structure
        candidate_dir = file_storage.get_candidate_dir(email_id)
        attachments_dir = candidate_dir / "attachments"
        attachments_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = attachments_dir / attachment.name
        
        try:
            # Try different ways to get attachment content
            if hasattr(attachment, 'content'):
                content = attachment.content
            elif hasattr(attachment, 'get_content'):
                content = attachment.get_content()
            else:
                # Fallback: save the attachment directly
                attachment.save(attachments_dir)
                logger.debug(f"Saved attachment using save method: {file_path}")
                return file_path
            
            # Ensure content is bytes
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.debug(f"Saved attachment: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving attachment {attachment.name}: {str(e)}")
            # Try alternative approach
            try:
                attachment.save(attachments_dir)
                logger.debug(f"Saved attachment using fallback method: {file_path}")
                return file_path
            except Exception as e2:
                logger.error(f"Fallback save also failed: {str(e2)}")
                raise e
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _extract_email_content(self, message) -> str:
        """Extract email body content."""
        try:
            # Try to get text content
            if hasattr(message, 'body_preview'):
                return message.body_preview
            elif hasattr(message, 'body'):
                # Handle different body types
                if hasattr(message.body, 'content'):
                    return message.body.content
                else:
                    return str(message.body)
            elif hasattr(message, 'text_body'):
                return message.text_body
            else:
                return ""
        except Exception as e:
            logger.warning(f"Could not extract email content: {str(e)}")
            return ""


# Global ingestor instance
email_ingestor = EmailIngestor() 