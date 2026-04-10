"""
Upload service for processing CSV and Excel files.
"""
import pandas as pd
import uuid
from typing import List, Dict, Any, Tuple
from datetime import datetime
from io import BytesIO
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from ..core.exceptions import FileProcessingError
from ..models.comment import CommentCreate, UploadProgress


class UploadService:
    """Service for handling file uploads and data validation."""
    
    SUPPORTED_CSV_EXTENSIONS = ['.csv', '.txt']
    SUPPORTED_EXCEL_EXTENSIONS = ['.xlsx', '.xls']
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    BULK_INSERT_BATCH_SIZE = 100  # Insert in batches for better performance
    
    @staticmethod
    async def process_csv_upload(file: UploadFile) -> Tuple[List[CommentCreate], List[str]]:
        """
        Process CSV file upload and extract comments.
        
        Args:
            file: Uploaded CSV file
            
        Returns:
            Tuple of (valid_comments, error_messages)
            
        Raises:
            FileProcessingError: If file cannot be processed
        """
        try:
            # Read file content
            content = await file.read()
            
            # Validate file size
            if len(content) > UploadService.MAX_FILE_SIZE:
                raise FileProcessingError(
                    "File size exceeds maximum allowed size of 50MB"
                )
            
            # Parse CSV with pandas
            try:
                df = pd.read_csv(BytesIO(content))
            except Exception as e:
                raise FileProcessingError(f"Invalid CSV format: {str(e)}")
            
            # Validate and extract comments
            return UploadService._extract_comments_from_dataframe(df, "csv_upload")
            
        except FileProcessingError:
            raise
        except Exception as e:
            raise FileProcessingError(f"Error processing CSV file: {str(e)}")
    
    @staticmethod
    async def process_excel_upload(file: UploadFile) -> Tuple[List[CommentCreate], List[str]]:
        """
        Process Excel file upload and extract comments.
        
        Args:
            file: Uploaded Excel file
            
        Returns:
            Tuple of (valid_comments, error_messages)
            
        Raises:
            FileProcessingError: If file cannot be processed
        """
        try:
            # Read file content
            content = await file.read()
            
            # Validate file size
            if len(content) > UploadService.MAX_FILE_SIZE:
                raise FileProcessingError(
                    "File size exceeds maximum allowed size of 50MB"
                )
            
            # Parse Excel with pandas
            try:
                df = pd.read_excel(BytesIO(content), engine='openpyxl')
            except Exception as e:
                raise FileProcessingError(f"Invalid Excel format: {str(e)}")
            
            # Validate and extract comments
            return UploadService._extract_comments_from_dataframe(df, "excel_upload")
            
        except FileProcessingError:
            raise
        except Exception as e:
            raise FileProcessingError(f"Error processing Excel file: {str(e)}")
    
    @staticmethod
    def _extract_comments_from_dataframe(
        df: pd.DataFrame, 
        source: str
    ) -> Tuple[List[CommentCreate], List[str]]:
        """
        Extract and validate comments from a pandas DataFrame.
        
        Args:
            df: DataFrame containing comment data
            source: Source identifier for the comments
            
        Returns:
            Tuple of (valid_comments, error_messages)
        """
        valid_comments = []
        errors = []
        
        # Validate required columns
        required_columns = ['comment_text']
        optional_columns = ['date_submitted', 'original_language', 'metadata']
        
        # Check for comment_text column (case-insensitive)
        df.columns = df.columns.str.strip().str.lower()
        
        if 'comment_text' not in df.columns:
            raise FileProcessingError(
                "Missing required column 'comment_text'. "
                "File must contain at least a 'comment_text' column."
            )
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                # Extract comment text
                comment_text = str(row['comment_text']).strip()
                
                # Skip empty comments
                if not comment_text or comment_text.lower() in ['nan', 'none', '']:
                    errors.append(f"Row {idx + 2}: Empty or invalid comment text")
                    continue
                
                # Validate comment length
                if len(comment_text) > 10000:
                    errors.append(f"Row {idx + 2}: Comment text exceeds 10000 characters")
                    continue
                
                # Extract optional fields
                date_submitted = None
                if 'date_submitted' in df.columns and pd.notna(row['date_submitted']):
                    try:
                        date_submitted = pd.to_datetime(row['date_submitted'])
                    except Exception:
                        errors.append(f"Row {idx + 2}: Invalid date format")
                
                original_language = None
                if 'original_language' in df.columns and pd.notna(row['original_language']):
                    original_language = str(row['original_language']).strip()
                
                # Create comment object
                comment = CommentCreate(
                    comment_text=comment_text,
                    source=source,
                    date_submitted=date_submitted,
                    original_language=original_language,
                    metadata={}
                )
                
                valid_comments.append(comment)
                
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        # Validate that we have at least some valid comments
        if not valid_comments:
            raise FileProcessingError(
                "No valid comments found in file. "
                f"Errors encountered: {'; '.join(errors[:5])}"
            )
        
        return valid_comments, errors
    
    @staticmethod
    def validate_file_extension(filename: str, file_type: str) -> bool:
        """
        Validate file extension matches expected type.
        
        Args:
            filename: Name of the uploaded file
            file_type: Expected file type ('csv' or 'excel')
            
        Returns:
            True if extension is valid
            
        Raises:
            FileProcessingError: If extension is invalid
        """
        filename_lower = filename.lower()
        
        if file_type == 'csv':
            if not any(filename_lower.endswith(ext) for ext in UploadService.SUPPORTED_CSV_EXTENSIONS):
                raise FileProcessingError(
                    f"Invalid file extension. Expected CSV file (.csv, .txt)"
                )
        elif file_type == 'excel':
            if not any(filename_lower.endswith(ext) for ext in UploadService.SUPPORTED_EXCEL_EXTENSIONS):
                raise FileProcessingError(
                    f"Invalid file extension. Expected Excel file (.xlsx, .xls)"
                )
        else:
            raise FileProcessingError(f"Unsupported file type: {file_type}")
        
        return True

    @staticmethod
    async def bulk_insert_comments(
        comments: List[CommentCreate],
        user_id: ObjectId,
        db: AsyncIOMotorDatabase,
        upload_id: str = None
    ) -> Dict[str, Any]:
        """
        Bulk insert comments with progress tracking.
        
        Args:
            comments: List of comments to insert
            user_id: ID of the user uploading comments
            db: Database instance
            upload_id: Optional upload ID for progress tracking
            
        Returns:
            Dictionary with insertion results and statistics
        """
        if not upload_id:
            upload_id = f"upload_{uuid.uuid4().hex[:12]}"
        
        total_comments = len(comments)
        stored_count = 0
        failed_count = 0
        errors = []
        
        # Initialize progress tracking
        progress = UploadProgress(
            upload_id=upload_id,
            user_id=str(user_id),
            total_comments=total_comments,
            processed_comments=0,
            stored_comments=0,
            failed_comments=0,
            status="processing"
        )
        
        await db.upload_progress.insert_one(progress.model_dump())
        
        try:
            # Process comments in batches
            for i in range(0, total_comments, UploadService.BULK_INSERT_BATCH_SIZE):
                batch = comments[i:i + UploadService.BULK_INSERT_BATCH_SIZE]
                batch_docs = []
                
                for comment in batch:
                    try:
                        comment_dict = comment.model_dump()
                        comment_dict['user_id'] = user_id
                        
                        # Set date_submitted if not provided
                        if not comment_dict.get('date_submitted'):
                            comment_dict['date_submitted'] = datetime.utcnow()
                        
                        batch_docs.append(comment_dict)
                    except Exception as e:
                        failed_count += 1
                        errors.append(f"Failed to prepare comment: {str(e)}")
                
                # Bulk insert batch
                if batch_docs:
                    try:
                        result = await db.comments.insert_many(batch_docs, ordered=False)
                        stored_count += len(result.inserted_ids)
                    except Exception as e:
                        failed_count += len(batch_docs)
                        errors.append(f"Batch insert failed: {str(e)}")
                
                # Update progress
                processed = min(i + UploadService.BULK_INSERT_BATCH_SIZE, total_comments)
                await db.upload_progress.update_one(
                    {"upload_id": upload_id},
                    {
                        "$set": {
                            "processed_comments": processed,
                            "stored_comments": stored_count,
                            "failed_comments": failed_count,
                            "errors": errors[:10],  # Keep only first 10 errors
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            
            # Mark as completed
            await db.upload_progress.update_one(
                {"upload_id": upload_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "upload_id": upload_id,
                "success": True,
                "total_comments": total_comments,
                "stored_count": stored_count,
                "failed_count": failed_count,
                "errors": errors[:10]
            }
            
        except Exception as e:
            # Mark as failed
            await db.upload_progress.update_one(
                {"upload_id": upload_id},
                {
                    "$set": {
                        "status": "failed",
                        "errors": errors + [f"Upload failed: {str(e)}"],
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            raise FileProcessingError(f"Bulk insert failed: {str(e)}")
    
    @staticmethod
    async def get_upload_progress(
        upload_id: str,
        db: AsyncIOMotorDatabase
    ) -> UploadProgress:
        """
        Get upload progress status.
        
        Args:
            upload_id: Upload identifier
            db: Database instance
            
        Returns:
            UploadProgress object with current status
        """
        progress_doc = await db.upload_progress.find_one({"upload_id": upload_id})
        
        if not progress_doc:
            raise FileProcessingError(f"Upload ID {upload_id} not found")
        
        return UploadProgress(**progress_doc)
