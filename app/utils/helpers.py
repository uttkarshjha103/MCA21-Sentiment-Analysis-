"""
General utility functions and helpers.
"""
import re
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from bson import ObjectId
    BSON_AVAILABLE = True
except ImportError:
    BSON_AVAILABLE = False


def generate_id() -> str:
    """Generate a unique ID string."""
    if BSON_AVAILABLE:
        return str(ObjectId())
    else:
        # Fallback to UUID for testing without bson
        return str(uuid.uuid4()).replace('-', '')[:24]


def clean_text(text: str) -> str:
    """Clean and normalize text for processing."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:-]', '', text)
    
    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate file type based on extension."""
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1]
    return extension in [t.lower() for t in allowed_types]


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = f"file_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    return filename


def parse_date_range(date_str: str) -> Optional[Dict[str, datetime]]:
    """Parse date range string into start and end dates."""
    try:
        if ' to ' in date_str:
            start_str, end_str = date_str.split(' to ')
            start_date = datetime.fromisoformat(start_str.strip())
            end_date = datetime.fromisoformat(end_str.strip())
            return {"start": start_date, "end": end_date}
        else:
            # Single date
            date = datetime.fromisoformat(date_str.strip())
            return {"start": date, "end": date}
    except ValueError:
        return None


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later ones taking precedence."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def extract_keywords_simple(text: str, min_length: int = 3) -> List[str]:
    """Simple keyword extraction using basic text processing."""
    if not text:
        return []
    
    # Convert to lowercase and split into words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter by minimum length and remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
        'they', 'me', 'him', 'her', 'us', 'them'
    }
    
    keywords = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords[:20]  # Return top 20 keywords