"""
Command Line Interface for Social Agent - WhatsApp Conversation Analysis System.
"""

import asyncio
import click
import json
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime

from src.utils.config import get_settings, get_platform_config
from src.utils.database import init_database, db_manager
from src.utils.vector_db import get_vector_db
from src.utils.logging import get_logger
from src.scrapers.whatsapp import WhatsAppScraper
from src.agents.sentiment import SentimentAnalysisAgent
from src.agents.base import get_orchestrator

console = Console()
logger = get_logger("cli")


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Social Agent - WhatsApp Conversation Analysis System"""
    pass


@cli.command()
def init():
    """Initialize the Social Agent system."""
    console.print(Panel("🚀 Initializing Social Agent System", style="bold blue"))
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Initialize database
            task1 = progress.add_task("Setting up database...", total=None)
            init_database()
            progress.update(task1, description="✅ Database initialized")
            
            # Initialize vector database
            task2 = progress.add_task("Setting up vector database...", total=None)
            vector_db = get_vector_db()
            stats = vector_db.get_collection_stats()
            progress.update(task2, description="✅ Vector database initialized")
            
            # Check configuration
            task3 = progress.add_task("Checking configuration...", total=None)
            settings = get_settings()
            platform_config = get_platform_config()
            enabled_platforms = platform_config.get_enabled_platforms()
            progress.update(task3, description="✅ Configuration loaded")
        
        console.print("\n✅ Social Agent initialized successfully!", style="bold green")
        console.print(f"📊 Vector database: {stats.get('total_messages', 0)} messages stored")
        console.print(f"🔧 Enabled platforms: {', '.join(enabled_platforms) if enabled_platforms else 'None'}")
        
        if not enabled_platforms:
            console.print("\n⚠️  No platforms configured. Please update your .env file.", style="yellow")
            console.print("Copy .env.example to .env and add your configuration.")
    
    except Exception as e:
        console.print(f"\n❌ Initialization failed: {e}", style="bold red")
        logger.error(f"Initialization failed: {e}")


@cli.command()
def config():
    """Show current configuration."""
    console.print(Panel("⚙️  Current Configuration", style="bold cyan"))
    
    try:
        settings = get_settings()
        platform_config = get_platform_config()
        
        # Basic settings
        console.print("🔧 Basic Settings:")
        console.print(f"  Environment: {settings.environment}")
        console.print(f"  Debug Mode: {settings.debug}")
        console.print(f"  Log Level: {settings.log_level}")
        
        # Platform settings
        console.print("\n📱 Platform Configuration:")
        enabled_platforms = platform_config.get_enabled_platforms()
        console.print(f"  Enabled Platforms: {', '.join(enabled_platforms) if enabled_platforms else 'None'}")
        
        # WhatsApp settings
        whatsapp_config = platform_config.get_whatsapp_config()
        console.print(f"  WhatsApp Phone: {whatsapp_config['phone_number'] or 'Not configured'}")
        console.print(f"  Monitor Groups: {len(whatsapp_config['monitor_groups'])} configured")
        console.print(f"  Monitor Contacts: {len(whatsapp_config['monitor_contacts'])} configured")
        
        # AI settings
        console.print("\n🤖 AI Configuration:")
        console.print(f"  OpenAI Key: {'✅ Configured' if settings.openai_api_key else '❌ Not configured'}")
        console.print(f"  OpenAI Model: {settings.openai_model}")
        console.print(f"  Sentiment Analysis: {'✅ Enabled' if settings.sentiment_analysis_enabled else '❌ Disabled'}")
        console.print(f"  Categorization: {'✅ Enabled' if settings.categorization_enabled else '❌ Disabled'}")
        
        # Database settings
        console.print("\n💾 Database Configuration:")
        console.print(f"  Database URL: {settings.database_url}")
        console.print(f"  Vector DB Path: {settings.vector_db_path}")
        console.print(f"  Embedding Model: {settings.embedding_model}")
    
    except Exception as e:
        console.print(f"❌ Failed to show config: {e}", style="red")


if __name__ == "__main__":
    cli()
