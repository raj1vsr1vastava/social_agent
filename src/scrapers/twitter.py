"""
Twitter scraper for collecting tweets and user data.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import tweepy

from src.utils.config import get_platform_config
from src.utils.logging import get_logger, log_scraping_activity
from src.utils.helpers import extract_hashtags, extract_mentions, extract_urls, normalize_datetime
from src.models import SocialMediaPost, PostType, PlatformType


class TwitterScraper:
    """Scraper for Twitter data using Tweepy."""
    
    def __init__(self):
        self.platform_config = get_platform_config()
        self.logger = get_logger("scraper.twitter")
        self.api = None
        self.client = None
        self._initialize_api()
    
    def _initialize_api(self):
        """Initialize Twitter API clients."""
        config = self.platform_config.get_twitter_config()
        
        if not config.get("api_key") or not config.get("api_secret"):
            self.logger.warning("Twitter API credentials not configured")
            return
        
        try:
            # Initialize API v1.1 (for some legacy endpoints)
            auth = tweepy.OAuthHandler(
                config["api_key"],
                config["api_secret"]
            )
            
            if config.get("access_token") and config.get("access_token_secret"):
                auth.set_access_token(
                    config["access_token"],
                    config["access_token_secret"]
                )
            
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Initialize API v2 client
            if config.get("bearer_token"):
                self.client = tweepy.Client(
                    bearer_token=config["bearer_token"],
                    consumer_key=config["api_key"],
                    consumer_secret=config["api_secret"],
                    access_token=config.get("access_token"),
                    access_token_secret=config.get("access_token_secret"),
                    wait_on_rate_limit=True
                )
            
            self.logger.info("Twitter API initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter API: {e}")
            self.api = None
            self.client = None
    
    def is_configured(self) -> bool:
        """Check if Twitter scraper is properly configured."""
        return self.client is not None or self.api is not None
    
    async def scrape_user_tweets(self, username: str, max_tweets: int = 100, days_back: int = 7) -> List[Dict[str, Any]]:
        """Scrape tweets from a specific user."""
        if not self.is_configured():
            raise ValueError("Twitter API not configured")
        
        try:
            tweets_data = []
            since_date = datetime.now() - timedelta(days=days_back)
            
            # Use API v2 if available, otherwise fall back to v1.1
            if self.client:
                tweets = tweepy.Paginator(
                    self.client.get_users_tweets,
                    username=username,
                    max_results=min(max_tweets, 100),
                    tweet_fields=[
                        'created_at', 'public_metrics', 'context_annotations',
                        'entities', 'author_id', 'conversation_id'
                    ],
                    start_time=since_date.isoformat()
                ).flatten(limit=max_tweets)
                
                for tweet in tweets:
                    tweet_data = self._process_tweet_v2(tweet)
                    if tweet_data:
                        tweets_data.append(tweet_data)
            
            elif self.api:
                tweets = tweepy.Cursor(
                    self.api.user_timeline,
                    screen_name=username,
                    count=min(max_tweets, 200),
                    include_rts=True,
                    exclude_replies=False,
                    tweet_mode='extended'
                ).items(max_tweets)
                
                for tweet in tweets:
                    if tweet.created_at >= since_date:
                        tweet_data = self._process_tweet_v1(tweet)
                        if tweet_data:
                            tweets_data.append(tweet_data)
            
            log_scraping_activity("twitter", f"scraped user tweets for @{username}", len(tweets_data))
            return tweets_data
            
        except Exception as e:
            self.logger.error(f"Failed to scrape tweets for user {username}: {e}")
            raise
    
    async def search_tweets(self, query: str, max_tweets: int = 100, days_back: int = 7) -> List[Dict[str, Any]]:
        """Search for tweets based on a query."""
        if not self.is_configured():
            raise ValueError("Twitter API not configured")
        
        try:
            tweets_data = []
            since_date = datetime.now() - timedelta(days=days_back)
            
            if self.client:
                tweets = tweepy.Paginator(
                    self.client.search_recent_tweets,
                    query=query,
                    max_results=min(max_tweets, 100),
                    tweet_fields=[
                        'created_at', 'public_metrics', 'context_annotations',
                        'entities', 'author_id', 'conversation_id'
                    ],
                    start_time=since_date.isoformat()
                ).flatten(limit=max_tweets)
                
                for tweet in tweets:
                    tweet_data = self._process_tweet_v2(tweet)
                    if tweet_data:
                        tweets_data.append(tweet_data)
            
            elif self.api:
                tweets = tweepy.Cursor(
                    self.api.search_tweets,
                    q=query,
                    count=min(max_tweets, 100),
                    result_type='recent',
                    tweet_mode='extended'
                ).items(max_tweets)
                
                for tweet in tweets:
                    if tweet.created_at >= since_date:
                        tweet_data = self._process_tweet_v1(tweet)
                        if tweet_data:
                            tweets_data.append(tweet_data)
            
            log_scraping_activity("twitter", f"searched tweets for query: {query}", len(tweets_data))
            return tweets_data
            
        except Exception as e:
            self.logger.error(f"Failed to search tweets for query {query}: {e}")
            raise
    
    async def scrape_tweet_replies(self, tweet_id: str, max_replies: int = 50) -> List[Dict[str, Any]]:
        """Scrape replies to a specific tweet."""
        if not self.client:
            self.logger.warning("Tweet replies require API v2")
            return []
        
        try:
            # Search for tweets that are replies to the original tweet
            query = f"conversation_id:{tweet_id}"
            
            replies = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=min(max_replies, 100),
                tweet_fields=[
                    'created_at', 'public_metrics', 'context_annotations',
                    'entities', 'author_id', 'conversation_id', 'in_reply_to_user_id'
                ]
            ).flatten(limit=max_replies)
            
            replies_data = []
            for reply in replies:
                if reply.id != tweet_id:  # Exclude the original tweet
                    reply_data = self._process_tweet_v2(reply, post_type=PostType.REPLY)
                    if reply_data:
                        replies_data.append(reply_data)
            
            log_scraping_activity("twitter", f"scraped replies for tweet {tweet_id}", len(replies_data))
            return replies_data
            
        except Exception as e:
            self.logger.error(f"Failed to scrape replies for tweet {tweet_id}: {e}")
            return []
    
    def _process_tweet_v2(self, tweet, post_type: PostType = PostType.POST) -> Optional[Dict[str, Any]]:
        """Process a tweet from API v2."""
        try:
            # Get public metrics
            metrics = tweet.public_metrics or {}
            
            # Extract entities
            entities = tweet.entities or {}
            hashtags = [tag['tag'] for tag in entities.get('hashtags', [])]
            mentions = [mention['username'] for mention in entities.get('mentions', [])]
            urls = [url['expanded_url'] for url in entities.get('urls', []) if url.get('expanded_url')]
            
            return {
                "platform": PlatformType.TWITTER,
                "post_id": str(tweet.id),
                "post_type": post_type,
                "content": tweet.text,
                "author_username": None,  # Need to fetch user data separately
                "author_name": None,
                "url": f"https://twitter.com/user/status/{tweet.id}",
                "created_at": normalize_datetime(tweet.created_at),
                "likes_count": metrics.get('like_count', 0),
                "comments_count": metrics.get('reply_count', 0),
                "shares_count": metrics.get('retweet_count', 0),
                "views_count": metrics.get('impression_count', 0),
                "hashtags": hashtags,
                "mentions": mentions,
                "media_urls": urls,
                "raw_data": {
                    "tweet_id": str(tweet.id),
                    "author_id": str(tweet.author_id) if tweet.author_id else None,
                    "conversation_id": str(tweet.conversation_id) if tweet.conversation_id else None,
                    "public_metrics": metrics,
                    "context_annotations": getattr(tweet, 'context_annotations', []),
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process tweet v2: {e}")
            return None
    
    def _process_tweet_v1(self, tweet, post_type: PostType = PostType.POST) -> Optional[Dict[str, Any]]:
        """Process a tweet from API v1.1."""
        try:
            # Get tweet text (full text for extended tweets)
            text = getattr(tweet, 'full_text', tweet.text)
            
            # Extract hashtags and mentions
            hashtags = extract_hashtags(text)
            mentions = extract_mentions(text, "twitter")
            urls = extract_urls(text)
            
            # Get media URLs if available
            media_urls = []
            if hasattr(tweet, 'entities') and 'media' in tweet.entities:
                media_urls = [media['media_url_https'] for media in tweet.entities['media']]
            
            return {
                "platform": PlatformType.TWITTER,
                "post_id": str(tweet.id),
                "post_type": post_type,
                "content": text,
                "author_username": tweet.user.screen_name,
                "author_name": tweet.user.name,
                "url": f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}",
                "created_at": normalize_datetime(tweet.created_at),
                "likes_count": tweet.favorite_count,
                "comments_count": 0,  # Not available in v1.1
                "shares_count": tweet.retweet_count,
                "views_count": 0,  # Not available in v1.1
                "hashtags": hashtags,
                "mentions": mentions,
                "media_urls": media_urls + urls,
                "raw_data": {
                    "tweet_id": str(tweet.id),
                    "user_id": str(tweet.user.id),
                    "is_retweet": hasattr(tweet, 'retweeted_status'),
                    "lang": getattr(tweet, 'lang', None),
                    "source": getattr(tweet, 'source', None),
                    "geo": getattr(tweet, 'geo', None),
                    "place": getattr(tweet, 'place', None),
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process tweet v1: {e}")
            return None
    
    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        if not self.is_configured():
            return None
        
        try:
            if self.client:
                user = self.client.get_user(username=username, user_fields=['public_metrics'])
                if user.data:
                    metrics = user.data.public_metrics or {}
                    return {
                        "user_id": str(user.data.id),
                        "username": user.data.username,
                        "name": user.data.name,
                        "description": getattr(user.data, 'description', ''),
                        "followers_count": metrics.get('followers_count', 0),
                        "following_count": metrics.get('following_count', 0),
                        "tweet_count": metrics.get('tweet_count', 0),
                        "verified": getattr(user.data, 'verified', False),
                    }
            
            elif self.api:
                user = self.api.get_user(screen_name=username)
                return {
                    "user_id": str(user.id),
                    "username": user.screen_name,
                    "name": user.name,
                    "description": user.description,
                    "followers_count": user.followers_count,
                    "following_count": user.friends_count,
                    "tweet_count": user.statuses_count,
                    "verified": user.verified,
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get user info for {username}: {e}")
            return None
    
    async def monitor_mentions(self, username: str, max_mentions: int = 50) -> List[Dict[str, Any]]:
        """Monitor mentions of a specific username."""
        query = f"@{username} -from:{username}"  # Exclude self-mentions
        return await self.search_tweets(query, max_mentions)
    
    async def monitor_hashtags(self, hashtags: List[str], max_tweets: int = 100) -> List[Dict[str, Any]]:
        """Monitor specific hashtags."""
        query = " OR ".join([f"#{tag}" for tag in hashtags])
        return await self.search_tweets(query, max_tweets)
