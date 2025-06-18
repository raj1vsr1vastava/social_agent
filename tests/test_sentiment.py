"""
Basic tests for the Social Agent system.
"""

import pytest
import asyncio
from datetime import datetime

from src.agents.sentiment import SentimentAnalysisAgent
from src.models import SentimentType


class TestSentimentAnalysisAgent:
    """Test the sentiment analysis agent."""
    
    @pytest.fixture
    def agent(self):
        return SentimentAnalysisAgent()
    
    @pytest.mark.asyncio
    async def test_positive_sentiment(self, agent):
        """Test positive sentiment analysis."""
        data = {
            "text": "I love this product! It's amazing and works perfectly!",
            "post_id": "test_positive",
            "platform": "twitter"
        }
        
        result = await agent.process(data)
        
        assert result["sentiment"] == SentimentType.POSITIVE
        assert result["confidence"] > 0.3
        assert "post_id" in result
        assert "insights" in result
    
    @pytest.mark.asyncio
    async def test_negative_sentiment(self, agent):
        """Test negative sentiment analysis."""
        data = {
            "text": "This is terrible! I hate it so much. Worst experience ever!",
            "post_id": "test_negative", 
            "platform": "twitter"
        }
        
        result = await agent.process(data)
        
        assert result["sentiment"] == SentimentType.NEGATIVE
        assert result["confidence"] > 0.3
        assert "post_id" in result
    
    @pytest.mark.asyncio
    async def test_neutral_sentiment(self, agent):
        """Test neutral sentiment analysis."""
        data = {
            "text": "This is a regular product. It has features.",
            "post_id": "test_neutral",
            "platform": "twitter"
        }
        
        result = await agent.process(data)
        
        assert result["sentiment"] == SentimentType.NEUTRAL
        assert "post_id" in result
    
    @pytest.mark.asyncio
    async def test_empty_text(self, agent):
        """Test handling of empty text."""
        data = {
            "text": "",
            "post_id": "test_empty",
            "platform": "twitter"
        }
        
        result = await agent.process(data)
        
        assert "error" in result
        assert result["post_id"] == "test_empty"
    
    @pytest.mark.asyncio
    async def test_batch_analysis(self, agent):
        """Test batch sentiment analysis."""
        posts = [
            {"text": "Great product!", "post_id": "1", "platform": "twitter"},
            {"text": "Terrible service!", "post_id": "2", "platform": "twitter"},
            {"text": "Average experience", "post_id": "3", "platform": "twitter"}
        ]
        
        results = await agent.analyze_batch(posts)
        
        assert len(results) == 3
        assert all("sentiment" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_sentiment_summary(self, agent):
        """Test sentiment summary generation."""
        results = [
            {"sentiment": SentimentType.POSITIVE, "confidence": 0.8},
            {"sentiment": SentimentType.NEGATIVE, "confidence": 0.7},
            {"sentiment": SentimentType.NEUTRAL, "confidence": 0.5},
            {"sentiment": SentimentType.POSITIVE, "confidence": 0.9}
        ]
        
        summary = await agent.get_sentiment_summary(results)
        
        assert summary["total_posts"] == 4
        assert summary["sentiment_distribution"]["counts"][SentimentType.POSITIVE] == 2
        assert summary["sentiment_distribution"]["counts"][SentimentType.NEGATIVE] == 1
        assert summary["sentiment_distribution"]["counts"][SentimentType.NEUTRAL] == 1
        assert summary["overall_sentiment"] == SentimentType.POSITIVE


if __name__ == "__main__":
    pytest.main([__file__])
