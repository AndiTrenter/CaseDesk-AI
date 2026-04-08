"""Date/Time utility functions for robust parsing and serialization"""
from datetime import datetime, timezone
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


def safe_parse_datetime(date_val: Union[datetime, str, None]) -> Optional[str]:
    """
    Safely parse datetime values from database to ISO string format.
    Handles both datetime objects and various string formats (including malformed ones).
    
    Args:
        date_val: datetime object, string, or None
        
    Returns:
        ISO 8601 formatted string or None if invalid
        
    Examples:
        - datetime object → "2026-04-09T10:30:00"
        - "2026-04-09T" → "2026-04-09T00:00:00"
        - "2026-04-09T:00" → "2026-04-09T00:00:00"
        - "2026-04-09" → "2026-04-09T00:00:00"
        - None → None
    """
    if date_val is None:
        return None
    
    # If already a datetime object, convert to ISO string
    if isinstance(date_val, datetime):
        return date_val.isoformat()
    
    # If it's a string, try to parse and fix common issues
    if isinstance(date_val, str):
        date_str = date_val.strip()
        
        if not date_str:
            return None
        
        try:
            # Try parsing as ISO format first
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return parsed.isoformat()
        except (ValueError, AttributeError):
            pass
        
        # Fix common malformed patterns
        # Pattern: "2026-04-09T" (missing time)
        if date_str.endswith('T'):
            date_str = date_str + '00:00:00'
            try:
                parsed = datetime.fromisoformat(date_str)
                return parsed.isoformat()
            except (ValueError, AttributeError):
                pass
        
        # Pattern: "2026-04-09T:00" (malformed time)
        if 'T:' in date_str:
            date_str = date_str.replace('T:', 'T00:')
            # Add seconds if missing
            if date_str.count(':') == 1:
                date_str += ':00'
            try:
                parsed = datetime.fromisoformat(date_str)
                return parsed.isoformat()
            except (ValueError, AttributeError):
                pass
        
        # Pattern: "2026-04-09" (date only)
        if len(date_str) == 10 and date_str.count('-') == 2:
            date_str = date_str + 'T00:00:00'
            try:
                parsed = datetime.fromisoformat(date_str)
                return parsed.isoformat()
            except (ValueError, AttributeError):
                pass
        
        # Try common datetime formats
        formats_to_try = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
            '%d.%m.%Y %H:%M:%S',
            '%d.%m.%Y',
        ]
        
        for fmt in formats_to_try:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.isoformat()
            except (ValueError, AttributeError):
                continue
        
        # If all parsing attempts fail, log warning and return None
        logger.warning(f"Could not parse date string: {date_val}")
        return None
    
    # Unknown type
    logger.warning(f"Unexpected date type: {type(date_val)} - {date_val}")
    return None
