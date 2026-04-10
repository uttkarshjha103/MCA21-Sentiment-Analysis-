"""
Upload endpoints for CSV and Excel file processing.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List, Dict, Any
from ....core.database import get_database
from ....core.exceptions import FileProcessingError
from ....models.user import User
from ....models.comment import CommentCreate, CommentResponse, UploadProgress
from ....services.upload import UploadService
from .auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId


router = APIRouter()


@router.post("/csv", response_model=Dict[str, Any])
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Upload and process a CSV file containing comments with bulk insert and progress tracking.
    
    Expected CSV format:
    - Required column: comment_text
    - Optional columns: date_submitted, original_language, metadata
    
    Returns:
        Dictionary with upload results including upload_id for progress tracking
    """
    # Validate file extension
    try:
        UploadService.validate_file_extension(file.filename, 'csv')
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Process CSV file
    try:
        valid_comments, validation_errors = await UploadService.process_csv_upload(file)
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Bulk insert comments with progress tracking
    try:
        result = await UploadService.bulk_insert_comments(
            comments=valid_comments,
            user_id=ObjectId(current_user.id),
            db=db
        )
        
        result['validation_errors'] = validation_errors
        result['message'] = f"Successfully uploaded {result['stored_count']} comments from CSV file"
        
        return result
        
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/excel", response_model=Dict[str, Any])
async def upload_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Upload and process an Excel file containing comments with bulk insert and progress tracking.
    
    Expected Excel format:
    - Required column: comment_text
    - Optional columns: date_submitted, original_language, metadata
    
    Returns:
        Dictionary with upload results including upload_id for progress tracking
    """
    # Validate file extension
    try:
        UploadService.validate_file_extension(file.filename, 'excel')
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Process Excel file
    try:
        valid_comments, validation_errors = await UploadService.process_excel_upload(file)
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Bulk insert comments with progress tracking
    try:
        result = await UploadService.bulk_insert_comments(
            comments=valid_comments,
            user_id=ObjectId(current_user.id),
            db=db
        )
        
        result['validation_errors'] = validation_errors
        result['message'] = f"Successfully uploaded {result['stored_count']} comments from Excel file"
        
        return result
        
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/manual", response_model=CommentResponse)
async def upload_manual_comment(
    comment: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Manually add a single comment.
    
    Args:
        comment: Comment data to be added
        
    Returns:
        Created comment with ID
    """
    try:
        comment_dict = comment.model_dump()
        comment_dict['user_id'] = ObjectId(current_user.id)
        
        # Set date_submitted if not provided
        if not comment_dict.get('date_submitted'):
            comment_dict['date_submitted'] = datetime.utcnow()
        
        result = await db.comments.insert_one(comment_dict)
        
        # Retrieve the created comment
        created_comment = await db.comments.find_one({"_id": result.inserted_id})
        
        return CommentResponse(
            _id=str(created_comment['_id']),
            comment_text=created_comment['comment_text'],
            source=created_comment['source'],
            user_id=str(created_comment['user_id']),
            date_submitted=created_comment['date_submitted'],
            original_language=created_comment.get('original_language'),
            metadata=created_comment.get('metadata'),
            processed_at=created_comment.get('processed_at'),
            sentiment=created_comment.get('sentiment'),
            keywords=created_comment.get('keywords')
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.get("/progress/{upload_id}", response_model=UploadProgress)
async def get_upload_progress(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get the progress status of a bulk upload operation.
    
    Args:
        upload_id: The upload identifier returned from CSV/Excel upload
        
    Returns:
        UploadProgress object with current status and statistics
    """
    try:
        progress = await UploadService.get_upload_progress(upload_id, db)
        
        # Verify user has access to this upload
        if progress.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this upload"
            )
        
        return progress
        
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve upload progress: {str(e)}"
        )
