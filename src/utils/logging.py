"""
Logging configuration for the Social Agent system.
"""

import os
import logging
import logging.handlers
from typing import Optional
from datetime import datetime

from src.utils.config import get_settings


class SocialAgentLogger:
    """Custom logger for the Social Agent system."""
    
    def __init__(self, name: str = "social_agent"):
        self.settings = get_settings()
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up the logger with appropriate handlers and formatters."""
        # Clear existing handlers
        self.logger.handlers = []
        
        # Set log level
        log_level = getattr(logging, self.settings.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if self.settings.log_file:
            # Ensure log directory exists
            log_dir = os.path.dirname(self.settings.log_file)
            os.makedirs(log_dir, exist_ok=True)
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                self.settings.log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger."""
        return self.logger


# Global logger instance
_main_logger = SocialAgentLogger("social_agent")
logger = _main_logger.get_logger()


def get_logger(name: str = "social_agent") -> logging.Logger:
    """Get a logger with the specified name."""
    if name == "social_agent":
        return logger
    else:
        custom_logger = SocialAgentLogger(name)
        return custom_logger.get_logger()


def log_agent_activity(agent_name: str, activity: str, details: Optional[dict] = None):
    """Log agent activity with structured information."""
    log_message = f"Agent '{agent_name}': {activity}"
    if details:
        log_message += f" - Details: {details}"
    
    agent_logger = get_logger(f"agent.{agent_name}")
    agent_logger.info(log_message)


def log_scraping_activity(platform: str, action: str, count: int = 0, details: Optional[dict] = None):
    """Log scraping activity."""
    log_message = f"Scraping {platform}: {action}"
    if count > 0:
        log_message += f" (count: {count})"
    if details:
        log_message += f" - Details: {details}"
    
    scraper_logger = get_logger(f"scraper.{platform}")
    scraper_logger.info(log_message)


def log_analysis_activity(analysis_type: str, post_id: str, result: Optional[dict] = None):
    """Log analysis activity."""
    log_message = f"Analysis '{analysis_type}' for post {post_id}"
    if result:
        log_message += f" - Result: {result}"
    
    analysis_logger = get_logger(f"analysis.{analysis_type}")
    analysis_logger.info(log_message)
