"""
Utility functions for the Social Agent system.
"""

import re
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
import json


def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text."""
    if not text:
        return []
    
    hashtag_pattern = r'#\w+'
    hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
    return [tag.lower() for tag in hashtags]


def extract_mentions(text: str, platform: str = "twitter") -> List[str]:
    """Extract mentions from text based on platform."""
    if not text:
        return []
    
    if platform.lower() == "twitter":
        mention_pattern = r'@\w+'
    elif platform.lower() == "instagram":
        mention_pattern = r'@[\w.]+'
    elif platform.lower() == "linkedin":
        mention_pattern = r'@[\w\s]+'
    else:
        mention_pattern = r'@\w+'
    
    mentions = re.findall(mention_pattern, text, re.IGNORECASE)
    return [mention.lower() for mention in mentions]


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    if not text:
        return []
    
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return urls


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and special characters."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:\-@#]', '', text)
    
    return text.strip()


def generate_post_hash(post_data: Dict[str, Any]) -> str:
    """Generate a unique hash for a post based on its content."""
    # Create a string representation of key post data
    hash_string = f"{post_data.get('platform', '')}-{post_data.get('post_id', '')}-{post_data.get('content', '')}"
    
    # Generate MD5 hash
    return hashlib.md5(hash_string.encode()).hexdigest()


def normalize_datetime(dt: Any) -> datetime:
    """Normalize various datetime formats to UTC datetime."""
    if isinstance(dt, str):
        # Try to parse common datetime formats
        for fmt in [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ]:
            try:
                dt = datetime.strptime(dt, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Unable to parse datetime string: {dt}")
    
    # Ensure timezone awareness
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to UTC
    if dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)
    
    # Remove timezone info for SQLAlchemy compatibility
    return dt.replace(tzinfo=None)


def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove extra spaces and dots
    filename = re.sub(r'\s+', '_', filename)
    filename = re.sub(r'\.+', '.', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255 - len(ext) - 1] + ('.' + ext if ext else '')
    
    return filename


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string, returning default value on error."""
    try:
        return json.loads(json_str) if json_str else default
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely dump object to JSON string, returning default on error."""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default


def calculate_engagement_rate(likes: int, comments: int, shares: int, followers: int) -> float:
    """Calculate engagement rate for a post."""
    if followers == 0:
        return 0.0
    
    total_engagement = likes + comments + shares
    return (total_engagement / followers) * 100


def get_platform_emoji(platform: str) -> str:
    """Get emoji for platform."""
    platform_emojis = {
        "twitter": "🐦",
        "instagram": "📸",
        "linkedin": "💼",
        "whatsapp": "💬",
    }
    return platform_emojis.get(platform.lower(), "📱")


def format_large_number(num: int) -> str:
    """Format large numbers with K, M, B suffixes."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)


class TextProcessor:
    """Text processing utilities."""
    
    @staticmethod
    def remove_emojis(text: str) -> str:
        """Remove emojis from text."""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r'', text)
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> List[str]:
        """Extract keywords from text."""
        if not text:
            return []
        
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter words by length and remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them'
        }
        
        keywords = [
            word for word in words
            if len(word) >= min_length and word not in stop_words
        ]
        
        return list(set(keywords))  # Remove duplicates
