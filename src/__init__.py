"""
Social Agent - Multi-Agent Framework for WhatsApp Conversation Analysis

A sophisticated system that leverages AutoGen's multi-agent framework
to analyze WhatsApp conversations with sentiment analysis, categorization,
and intelligent response suggestions.
"""

__version__ = "1.0.0"
__author__ = "Social Agent Development Team"
__description__ = "Multi-agent framework for WhatsApp conversation analysis"

from src.utils.config import get_settings, get_platform_config
from src.utils.database import db_manager, init_database
from src.utils.vector_db import get_vector_db
from src.agents.base import get_orchestrator
from src.agents.sentiment import SentimentAnalysisAgent
from src.scrapers.whatsapp import WhatsAppScraper

__all__ = [
    "get_settings",
    "get_platform_config",
    "db_manager", 
    "init_database",
    "get_vector_db",
    "get_orchestrator",
    "SentimentAnalysisAgent",
    "WhatsAppScraper",
]
