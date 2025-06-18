"""
Data models for the Social Agent system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

Base = declarative_base()


class PlatformType(str, Enum):
    """Supported social media platforms."""
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"


class PostType(str, Enum):
    """Types of social media posts."""
    POST = "post"
    COMMENT = "comment"
    REPLY = "reply"
    MESSAGE = "message"
    STORY = "story"


class SentimentType(str, Enum):
    """Sentiment analysis results."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class AnalysisStatus(str, Enum):
    """Status of analysis tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# SQLAlchemy Models

class SocialMediaAccount(Base):
    """Social media account configuration."""
    __tablename__ = "social_media_accounts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)
    username = Column(String(255), nullable=False)
    display_name = Column(String(255))
    account_id = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Configuration for this account
    config = Column(JSON)
    
    # Relationships
    posts = relationship("SocialMediaPost", back_populates="account")


class SocialMediaPost(Base):
    """Social media post data."""
    __tablename__ = "social_media_posts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)
    post_id = Column(String(255), nullable=False, index=True)
    post_type = Column(String(50), default=PostType.POST)
    
    # Post content
    content = Column(Text)
    author_username = Column(String(255))
    author_name = Column(String(255))
    
    # Metadata
    url = Column(String(500))
    created_at = Column(DateTime, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    # Engagement metrics
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    
    # Additional data
    hashtags = Column(JSON)  # List of hashtags
    mentions = Column(JSON)  # List of mentions
    media_urls = Column(JSON)  # List of media URLs
    raw_data = Column(JSON)  # Raw platform data
    
    # Foreign keys
    account_id = Column(Integer, ForeignKey("social_media_accounts.id"))
    
    # Relationships
    account = relationship("SocialMediaAccount", back_populates="posts")
    analyses = relationship("AnalysisResult", back_populates="post")


class AnalysisResult(Base):
    """Analysis results for posts."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String(100), nullable=False)  # sentiment, competitor, trend, etc.
    status = Column(String(50), default=AnalysisStatus.PENDING)
    
    # Results
    score = Column(Float)  # Numerical score (0-1 or -1 to 1)
    category = Column(String(100))  # Category/classification
    confidence = Column(Float)  # Confidence level
    
    # Detailed results
    results = Column(JSON)  # Detailed analysis results
    analysis_metadata = Column(JSON)  # Analysis metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Foreign keys
    post_id = Column(Integer, ForeignKey("social_media_posts.id"))
    
    # Relationships
    post = relationship("SocialMediaPost", back_populates="analyses")


class WhatsAppGroup(Base):
    """WhatsApp group configuration."""
    __tablename__ = "whatsapp_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(255), nullable=False)
    group_id = Column(String(255), unique=True)
    description = Column(Text)
    
    # Configuration
    is_monitored = Column(Boolean, default=True)
    categories = Column(JSON)  # Custom categories for this group
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("WhatsAppMessage", back_populates="group")


class WhatsAppMessage(Base):
    """WhatsApp messages."""
    __tablename__ = "whatsapp_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), unique=True)
    
    # Message content
    content = Column(Text)
    sender_name = Column(String(255))
    sender_phone = Column(String(50))
    
    # Metadata
    timestamp = Column(DateTime, nullable=False)
    message_type = Column(String(50))  # text, image, audio, etc.
    
    # Analysis
    category = Column(String(100))  # Auto-categorized
    priority = Column(String(50))  # high, medium, low
    requires_response = Column(Boolean, default=False)
    
    # Foreign keys
    group_id = Column(Integer, ForeignKey("whatsapp_groups.id"))
    
    # Relationships
    group = relationship("WhatsAppGroup", back_populates="messages")


class AgentTask(Base):
    """Agent task tracking."""
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(100), nullable=False)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(50), default=AnalysisStatus.PENDING)
    
    # Task configuration
    config = Column(JSON)
    
    # Results
    result = Column(JSON)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


# Pydantic Models for API

class SocialMediaAccountCreate(BaseModel):
    platform: PlatformType
    username: str
    display_name: Optional[str] = None
    account_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class SocialMediaAccountResponse(BaseModel):
    id: int
    platform: str
    username: str
    display_name: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SocialMediaPostCreate(BaseModel):
    platform: PlatformType
    post_id: str
    post_type: PostType = PostType.POST
    content: Optional[str] = None
    author_username: Optional[str] = None
    author_name: Optional[str] = None
    url: Optional[str] = None
    created_at: datetime
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    views_count: int = 0
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    media_urls: Optional[List[str]] = None
    raw_data: Optional[Dict[str, Any]] = None


class SocialMediaPostResponse(BaseModel):
    id: int
    platform: str
    post_id: str
    content: Optional[str]
    author_username: Optional[str]
    created_at: datetime
    likes_count: int
    comments_count: int
    shares_count: int
    
    class Config:
        from_attributes = True


class AnalysisResultCreate(BaseModel):
    analysis_type: str
    score: Optional[float] = None
    category: Optional[str] = None
    confidence: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisResultResponse(BaseModel):
    id: int
    analysis_type: str
    status: str
    score: Optional[float]
    category: Optional[str]
    confidence: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class WhatsAppGroupCreate(BaseModel):
    group_name: str
    group_id: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[str]] = None


class WhatsAppMessageCreate(BaseModel):
    message_id: str
    content: str
    sender_name: Optional[str] = None
    sender_phone: Optional[str] = None
    timestamp: datetime
    message_type: str = "text"
    group_id: int
