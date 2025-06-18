"""
Command Line Interface for the Social Agent system.
"""

import asyncio
import json
from typing import List, Optional
from datetime import datetime, timedelta

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from src.utils.config import get_settings, get_platform_config
from src.utils.database import db_manager, init_database
from src.utils.logging import get_logger
from src.agents.base import get_orchestrator
from src.agents.sentiment import SentimentAnalysisAgent
from src.scrapers.twitter import TwitterScraper
from src.models import SocialMediaAccount, SocialMediaPost, AnalysisResult


console = Console()
logger = get_logger("cli")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """Social Agent - Multi-Agent Social Media Analytics System."""
    if verbose:
        logger.setLevel("DEBUG")


@cli.command()
def init():
    """Initialize the database and system."""
    try:
        init_database()
        rprint("[green]✓[/green] Database initialized successfully!")
    except Exception as e:
        rprint(f"[red]✗[/red] Failed to initialize database: {e}")


@cli.command()
def status():
    """Show system status."""
    settings = get_settings()
    platform_config = get_platform_config()
    orchestrator = get_orchestrator()
    
    # Create status table
    table = Table(title="Social Agent System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    # Database status
    try:
        with db_manager.session_scope() as session:
            accounts_count = session.query(SocialMediaAccount).count()
            posts_count = session.query(SocialMediaPost).count()
            analyses_count = session.query(AnalysisResult).count()
        
        table.add_row(
            "Database",
            "✓ Connected",
            f"{accounts_count} accounts, {posts_count} posts, {analyses_count} analyses"
        )
    except Exception as e:
        table.add_row("Database", "✗ Error", str(e))
    
    # Platform configurations
    platforms = ["twitter", "instagram", "linkedin", "whatsapp"]
    for platform in platforms:
        is_configured = platform_config.is_platform_configured(platform)
        status_icon = "✓" if is_configured else "✗"
        status_text = "Configured" if is_configured else "Not configured"
        table.add_row(f"{platform.title()}", f"{status_icon} {status_text}", "")
    
    # Agent status
    orchestrator_status = orchestrator.get_orchestrator_status()
    table.add_row(
        "Agents",
        f"✓ {orchestrator_status['running_agents']}/{orchestrator_status['total_agents']} running",
        ""
    )
    
    console.print(table)


@cli.group()
def agents():
    """Manage agents."""
    pass


@agents.command('list')
def list_agents():
    """List all registered agents."""
    orchestrator = get_orchestrator()
    status = orchestrator.get_orchestrator_status()
    
    if not status['agents']:
        rprint("[yellow]No agents registered[/yellow]")
        return
    
    table = Table(title="Registered Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Description", style="green")
    table.add_column("Tasks", style="yellow")
    
    for agent_info in status['agents']:
        status_icon = "🟢" if agent_info['is_running'] else "🔴"
        table.add_row(
            agent_info['name'],
            f"{status_icon} {'Running' if agent_info['is_running'] else 'Stopped'}",
            agent_info['description'],
            str(agent_info['tasks_count'])
        )
    
    console.print(table)


@agents.command('start')
def start_agents():
    """Start all agents."""
    async def _start():
        orchestrator = get_orchestrator()
        
        # Register sentiment analysis agent
        sentiment_agent = SentimentAnalysisAgent()
        orchestrator.register_agent(sentiment_agent)
        
        await orchestrator.start_all_agents()
        rprint("[green]✓[/green] All agents started successfully!")
    
    asyncio.run(_start())


@agents.command('stop')
def stop_agents():
    """Stop all agents."""
    async def _stop():
        orchestrator = get_orchestrator()
        await orchestrator.stop_all_agents()
        rprint("[green]✓[/green] All agents stopped successfully!")
    
    asyncio.run(_stop())


@cli.group()
def scrape():
    """Scraping commands."""
    pass


@scrape.command('twitter')
@click.option('--username', '-u', help='Twitter username to scrape')
@click.option('--query', '-q', help='Search query')
@click.option('--max-tweets', '-m', default=50, help='Maximum number of tweets to scrape')
@click.option('--days-back', '-d', default=7, help='Number of days to go back')
@click.option('--analyze', '-a', is_flag=True, help='Run sentiment analysis on scraped tweets')
def scrape_twitter(username, query, max_tweets, days_back, analyze):
    """Scrape tweets from Twitter."""
    async def _scrape():
        scraper = TwitterScraper()
        
        if not scraper.is_configured():
            rprint("[red]✗[/red] Twitter API not configured. Please check your credentials.")
            return
        
        tweets_data = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            if username:
                task = progress.add_task(f"Scraping tweets from @{username}...", total=None)
                tweets_data = await scraper.scrape_user_tweets(username, max_tweets, days_back)
            elif query:
                task = progress.add_task(f"Searching tweets for '{query}'...", total=None)
                tweets_data = await scraper.search_tweets(query, max_tweets, days_back)
            else:
                rprint("[red]✗[/red] Please provide either --username or --query")
                return
            
            progress.update(task, completed=True)
        
        if not tweets_data:
            rprint("[yellow]No tweets found[/yellow]")
            return
        
        # Store tweets in database
        with db_manager.session_scope() as session:
            stored_count = 0
            for tweet_data in tweets_data:
                # Check if tweet already exists
                existing = session.query(SocialMediaPost).filter(
                    SocialMediaPost.platform == tweet_data["platform"],
                    SocialMediaPost.post_id == tweet_data["post_id"]
                ).first()
                
                if not existing:
                    post = SocialMediaPost(**tweet_data)
                    session.add(post)
                    stored_count += 1
            
            session.commit()
        
        rprint(f"[green]✓[/green] Scraped {len(tweets_data)} tweets, stored {stored_count} new tweets")
        
        # Run sentiment analysis if requested
        if analyze and tweets_data:
            await _analyze_tweets(tweets_data)
    
    asyncio.run(_scrape())


async def _analyze_tweets(tweets_data):
    """Analyze tweets with sentiment analysis."""
    orchestrator = get_orchestrator()
    
    # Start sentiment agent if not running
    sentiment_agent = SentimentAnalysisAgent()
    orchestrator.register_agent(sentiment_agent)
    await sentiment_agent.start()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Analyzing sentiment...", total=len(tweets_data))
        
        results = []
        for i, tweet in enumerate(tweets_data):
            analysis_data = {
                "text": tweet.get("content", ""),
                "post_id": tweet.get("post_id"),
                "platform": tweet.get("platform")
            }
            
            result = await sentiment_agent.process(analysis_data)
            results.append(result)
            
            # Store analysis result
            with db_manager.session_scope() as session:
                post = session.query(SocialMediaPost).filter(
                    SocialMediaPost.platform == tweet["platform"],
                    SocialMediaPost.post_id == tweet["post_id"]
                ).first()
                
                if post:
                    analysis = AnalysisResult(
                        post_id=post.id,
                        analysis_type="sentiment_analysis",
                        status="completed",
                        score=result.get("score", 0),
                        category=result.get("sentiment"),
                        confidence=result.get("confidence", 0),
                        results=result,
                        completed_at=datetime.utcnow()
                    )
                    session.add(analysis)
            
            progress.update(task, advance=1)
    
    # Show summary
    summary = await sentiment_agent.get_sentiment_summary(results)
    _display_sentiment_summary(summary)


def _display_sentiment_summary(summary):
    """Display sentiment analysis summary."""
    if "error" in summary:
        rprint(f"[red]✗[/red] {summary['error']}")
        return
    
    panel_content = f"""
[bold]Total Posts Analyzed:[/bold] {summary['total_posts']}
[bold]Successful Analyses:[/bold] {summary['successful_analyses']}
[bold]Average Confidence:[/bold] {summary['average_confidence']:.2f}

[bold]Sentiment Distribution:[/bold]
• Positive: {summary['sentiment_distribution']['counts']['positive']} ({summary['sentiment_distribution']['percentages']['positive']:.1f}%)
• Negative: {summary['sentiment_distribution']['counts']['negative']} ({summary['sentiment_distribution']['percentages']['negative']:.1f}%)
• Neutral: {summary['sentiment_distribution']['counts']['neutral']} ({summary['sentiment_distribution']['percentages']['neutral']:.1f}%)

[bold]Overall Sentiment:[/bold] {summary['overall_sentiment']}
    """
    
    console.print(Panel(panel_content, title="Sentiment Analysis Summary", border_style="green"))


@cli.group()
def analyze():
    """Analysis commands."""
    pass


@analyze.command('sentiment')
@click.option('--platform', '-p', help='Filter by platform')
@click.option('--days', '-d', default=7, help='Analyze posts from last N days')
def analyze_sentiment(platform, days):
    """Run sentiment analysis on stored posts."""
    async def _analyze():
        # Get posts from database
        since_date = datetime.utcnow() - timedelta(days=days)
        
        with db_manager.session_scope() as session:
            query = session.query(SocialMediaPost).filter(
                SocialMediaPost.created_at >= since_date
            )
            
            if platform:
                query = query.filter(SocialMediaPost.platform == platform)
            
            posts = query.all()
        
        if not posts:
            rprint("[yellow]No posts found to analyze[/yellow]")
            return
        
        # Convert to analysis format
        tweets_data = []
        for post in posts:
            tweets_data.append({
                "content": post.content,
                "post_id": post.post_id,
                "platform": post.platform
            })
        
        await _analyze_tweets(tweets_data)
    
    asyncio.run(_analyze())


@cli.command()
@click.option('--platform', '-p', help='Filter by platform')
@click.option('--limit', '-l', default=10, help='Number of posts to show')
def recent(platform, limit):
    """Show recent posts."""
    with db_manager.session_scope() as session:
        query = session.query(SocialMediaPost).order_by(SocialMediaPost.created_at.desc())
        
        if platform:
            query = query.filter(SocialMediaPost.platform == platform)
        
        posts = query.limit(limit).all()
    
    if not posts:
        rprint("[yellow]No posts found[/yellow]")
        return
    
    table = Table(title=f"Recent Posts ({limit})")
    table.add_column("Platform", style="cyan")
    table.add_column("Author", style="magenta")
    table.add_column("Content", style="green", max_width=50)
    table.add_column("Created", style="yellow")
    table.add_column("Engagement", style="blue")
    
    for post in posts:
        engagement = f"👍{post.likes_count} 💬{post.comments_count} 🔄{post.shares_count}"
        content = (post.content[:47] + "...") if post.content and len(post.content) > 50 else (post.content or "")
        
        table.add_row(
            post.platform.upper(),
            post.author_username or "Unknown",
            content,
            post.created_at.strftime("%m/%d %H:%M"),
            engagement
        )
    
    console.print(table)


if __name__ == "__main__":
    cli()
