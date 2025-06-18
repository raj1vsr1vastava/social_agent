"""
Configuration management for the Social Agent system.
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="API_DEBUG")
    
    # Database
    database_url: str = Field(default="sqlite:///./data/social_agent.db", env="DATABASE_URL")
    
    # Vector Database
    vector_db_path: str = Field(default="./data/chroma_db", env="VECTOR_DB_PATH")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    vector_db_collection: str = Field(default="whatsapp_conversations", env="VECTOR_DB_COLLECTION")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    
    # API Configuration
    api_host: str = Field(default="localhost", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    openai_timeout: int = Field(default=30, env="OPENAI_TIMEOUT")
    fallback_model: str = Field(default="gpt-3.5-turbo", env="FALLBACK_MODEL")
    
    # WhatsApp Configuration (Primary Focus)
    whatsapp_phone_number: Optional[str] = Field(default=None, env="WHATSAPP_PHONE_NUMBER")
    whatsapp_session_path: str = Field(default="./data/whatsapp_session", env="WHATSAPP_SESSION_PATH")
    whatsapp_chrome_path: str = Field(default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", env="WHATSAPP_CHROME_PATH")
    whatsapp_auto_login: bool = Field(default=True, env="WHATSAPP_AUTO_LOGIN")
    whatsapp_headless: bool = Field(default=False, env="WHATSAPP_HEADLESS")
    whatsapp_monitoring_enabled: bool = Field(default=True, env="WHATSAPP_MONITORING_ENABLED")
    
    # WhatsApp Monitoring Configuration
    whatsapp_monitor_groups: str = Field(default="", env="WHATSAPP_MONITOR_GROUPS")
    whatsapp_monitor_contacts: str = Field(default="", env="WHATSAPP_MONITOR_CONTACTS")
    
    # Social Media API Keys (Optional/Configurable)
    twitter_enabled: bool = Field(default=False, env="TWITTER_ENABLED")
    twitter_api_key: Optional[str] = Field(default=None, env="TWITTER_API_KEY")
    twitter_api_secret: Optional[str] = Field(default=None, env="TWITTER_API_SECRET")
    twitter_access_token: Optional[str] = Field(default=None, env="TWITTER_ACCESS_TOKEN")
    twitter_access_token_secret: Optional[str] = Field(default=None, env="TWITTER_ACCESS_TOKEN_SECRET")
    twitter_bearer_token: Optional[str] = Field(default=None, env="TWITTER_BEARER_TOKEN")
    
    instagram_enabled: bool = Field(default=False, env="INSTAGRAM_ENABLED")
    instagram_username: Optional[str] = Field(default=None, env="INSTAGRAM_USERNAME")
    instagram_password: Optional[str] = Field(default=None, env="INSTAGRAM_PASSWORD")
    
    linkedin_enabled: bool = Field(default=False, env="LINKEDIN_ENABLED")
    linkedin_username: Optional[str] = Field(default=None, env="LINKEDIN_USERNAME")
    linkedin_password: Optional[str] = Field(default=None, env="LINKEDIN_PASSWORD")
    
    # Agent Configuration
    max_concurrent_agents: int = Field(default=3, env="MAX_CONCURRENT_AGENTS")
    agent_timeout: int = Field(default=300, env="AGENT_TIMEOUT")
    message_processing_interval: int = Field(default=5, env="MESSAGE_PROCESSING_INTERVAL")
    
    # Analysis Configuration
    sentiment_analysis_enabled: bool = Field(default=True, env="SENTIMENT_ANALYSIS_ENABLED")
    categorization_enabled: bool = Field(default=True, env="CATEGORIZATION_ENABLED")
    response_suggestions_enabled: bool = Field(default=True, env="RESPONSE_SUGGESTIONS_ENABLED")
    sentiment_confidence_threshold: float = Field(default=0.7, env="SENTIMENT_CONFIDENCE_THRESHOLD")
    categorization_confidence_threshold: float = Field(default=0.8, env="CATEGORIZATION_CONFIDENCE_THRESHOLD")
    auto_response_enabled: bool = Field(default=False, env="AUTO_RESPONSE_ENABLED")
    high_priority_keywords: str = Field(default="urgent,important,help,emergency", env="HIGH_PRIORITY_KEYWORDS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./data/logs/social_agent.log", env="LOG_FILE")
    
    # Security Configuration
    encrypt_stored_messages: bool = Field(default=True, env="ENCRYPT_STORED_MESSAGES")
    data_retention_days: int = Field(default=90, env="DATA_RETENTION_DAYS")
    anonymize_phone_numbers: bool = Field(default=True, env="ANONYMIZE_PHONE_NUMBERS")
    
    # Performance Configuration
    batch_size: int = Field(default=50, env="BATCH_SIZE")
    cache_size: int = Field(default=1000, env="CACHE_SIZE")
    async_processing: bool = Field(default=True, env="ASYNC_PROCESSING")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in environment
    
    def get_whatsapp_monitor_groups(self) -> List[str]:
        """Get list of WhatsApp groups to monitor."""
        if not self.whatsapp_monitor_groups:
            return []
        return [group.strip() for group in self.whatsapp_monitor_groups.split(",") if group.strip()]
    
    def get_whatsapp_monitor_contacts(self) -> List[str]:
        """Get list of WhatsApp contacts to monitor."""
        if not self.whatsapp_monitor_contacts:
            return []
        return [contact.strip() for contact in self.whatsapp_monitor_contacts.split(",") if contact.strip()]
    
    def get_high_priority_keywords(self) -> List[str]:
        """Get list of high priority keywords."""
        if not self.high_priority_keywords:
            return []
        return [keyword.strip().lower() for keyword in self.high_priority_keywords.split(",") if keyword.strip()]


class PlatformConfig:
    """Configuration for social media platforms."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration."""
        return {
            "api_key": self.settings.openai_api_key,
            "model": self.settings.openai_model,
            "temperature": self.settings.openai_temperature,
            "max_tokens": self.settings.openai_max_tokens,
            "timeout": self.settings.openai_timeout,
            "fallback_model": self.settings.fallback_model,
        }
    
    def get_whatsapp_config(self) -> Dict[str, Any]:
        """Get WhatsApp configuration."""
        return {
            "phone_number": self.settings.whatsapp_phone_number,
            "session_path": self.settings.whatsapp_session_path,
            "chrome_path": self.settings.whatsapp_chrome_path,
            "auto_login": self.settings.whatsapp_auto_login,
            "headless": self.settings.whatsapp_headless,
            "monitoring_enabled": self.settings.whatsapp_monitoring_enabled,
            "monitor_groups": self.settings.get_whatsapp_monitor_groups(),
            "monitor_contacts": self.settings.get_whatsapp_monitor_contacts(),
        }
    
    def get_twitter_config(self) -> Dict[str, Any]:
        """Get Twitter API configuration."""
        return {
            "enabled": self.settings.twitter_enabled,
            "api_key": self.settings.twitter_api_key,
            "api_secret": self.settings.twitter_api_secret,
            "access_token": self.settings.twitter_access_token,
            "access_token_secret": self.settings.twitter_access_token_secret,
            "bearer_token": self.settings.twitter_bearer_token,
        }
    
    def get_instagram_config(self) -> Dict[str, Any]:
        """Get Instagram configuration."""
        return {
            "enabled": self.settings.instagram_enabled,
            "username": self.settings.instagram_username,
            "password": self.settings.instagram_password,
        }
    
    def get_linkedin_config(self) -> Dict[str, Any]:
        """Get LinkedIn configuration."""
        return {
            "enabled": self.settings.linkedin_enabled,
            "username": self.settings.linkedin_username,
            "password": self.settings.linkedin_password,
        }
    
    def is_platform_configured(self, platform: str) -> bool:
        """Check if a platform is properly configured."""
        if platform.lower() == "whatsapp":
            config = self.get_whatsapp_config()
            return bool(config["phone_number"] and config["monitoring_enabled"])
        
        elif platform.lower() == "twitter":
            config = self.get_twitter_config()
            return bool(config["enabled"] and config["api_key"] and config["api_secret"])
        
        elif platform.lower() == "instagram":
            config = self.get_instagram_config()
            return bool(config["enabled"] and config["username"] and config["password"])
        
        elif platform.lower() == "linkedin":
            config = self.get_linkedin_config()
            return bool(config["enabled"] and config["username"] and config["password"])
        
        return False
    
    def get_enabled_platforms(self) -> List[str]:
        """Get list of enabled social media platforms."""
        enabled = []
        
        if self.is_platform_configured("whatsapp"):
            enabled.append("whatsapp")
        
        if self.is_platform_configured("twitter"):
            enabled.append("twitter")
        
        if self.is_platform_configured("instagram"):
            enabled.append("instagram")
        
        if self.is_platform_configured("linkedin"):
            enabled.append("linkedin")
        
        return enabled


# Global settings instance
settings = Settings()
platform_config = PlatformConfig(settings)


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def get_platform_config() -> PlatformConfig:
    """Get platform configuration."""
    return platform_config
