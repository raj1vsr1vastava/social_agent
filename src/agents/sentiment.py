"""
Sentiment Analysis Agent for analyzing social media posts.
"""

import re
from typing import Dict, Any, List
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src.agents.base import BaseAgent
from src.utils.helpers import clean_text, TextProcessor
from src.models import SentimentType


class SentimentAnalysisAgent(BaseAgent):
    """Agent specialized in sentiment analysis of social media content."""
    
    def __init__(self):
        super().__init__(
            name="SentimentAnalysisAgent",
            description="Analyzes sentiment of social media posts and comments using multiple NLP techniques"
        )
        
        # Initialize sentiment analyzers
        self.vader_analyzer = SentimentIntensityAnalyzer()
        self.text_processor = TextProcessor()
        
        # Sentiment thresholds
        self.positive_threshold = 0.1
        self.negative_threshold = -0.1
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sentiment analysis for given text data."""
        text = data.get("text", "")
        post_id = data.get("post_id", "unknown")
        platform = data.get("platform", "unknown")
        
        if not text:
            return {
                "error": "No text provided for sentiment analysis",
                "post_id": post_id
            }
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(text, platform)
        
        # Perform sentiment analysis using multiple methods
        textblob_sentiment = self._analyze_with_textblob(cleaned_text)
        vader_sentiment = self._analyze_with_vader(cleaned_text)
        
        # Combine results and determine final sentiment
        combined_sentiment = self._combine_sentiments(textblob_sentiment, vader_sentiment)
        
        # Extract additional insights
        insights = self._extract_insights(text, combined_sentiment)
        
        result = {
            "post_id": post_id,
            "platform": platform,
            "sentiment": combined_sentiment["sentiment"],
            "confidence": combined_sentiment["confidence"],
            "score": combined_sentiment["score"],
            "detailed_analysis": {
                "textblob": textblob_sentiment,
                "vader": vader_sentiment,
                "combined": combined_sentiment
            },
            "insights": insights,
            "processed_text": cleaned_text
        }
        
        self.logger.info(f"Sentiment analysis completed for post {post_id}: {combined_sentiment['sentiment']}")
        return result
    
    def _preprocess_text(self, text: str, platform: str) -> str:
        """Preprocess text for sentiment analysis."""
        # Clean basic text
        cleaned = clean_text(text)
        
        # Remove platform-specific elements that might skew sentiment
        if platform.lower() == "twitter":
            # Remove RT indicator
            cleaned = re.sub(r'\bRT\b', '', cleaned)
        
        # Remove URLs (they don't contribute to sentiment)
        cleaned = re.sub(r'http[s]?://\S+', '', cleaned)
        
        # Remove excessive punctuation
        cleaned = re.sub(r'[!]{2,}', '!', cleaned)
        cleaned = re.sub(r'[?]{2,}', '?', cleaned)
        
        # Remove mentions and hashtags for cleaner sentiment analysis
        # but keep the words for context
        cleaned = re.sub(r'[@#](\w+)', r'\1', cleaned)
        
        return cleaned.strip()
    
    def _analyze_with_textblob(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using TextBlob."""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Convert polarity to sentiment category
            if polarity > self.positive_threshold:
                sentiment = SentimentType.POSITIVE
            elif polarity < self.negative_threshold:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL
            
            return {
                "sentiment": sentiment,
                "polarity": polarity,
                "subjectivity": subjectivity,
                "confidence": abs(polarity)
            }
        except Exception as e:
            self.logger.error(f"TextBlob analysis failed: {e}")
            return {
                "sentiment": SentimentType.NEUTRAL,
                "polarity": 0.0,
                "subjectivity": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _analyze_with_vader(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using VADER."""
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            compound = scores['compound']  # -1 to 1
            
            # Convert compound score to sentiment category
            if compound >= 0.05:
                sentiment = SentimentType.POSITIVE
            elif compound <= -0.05:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL
            
            return {
                "sentiment": sentiment,
                "compound": compound,
                "positive": scores['pos'],
                "negative": scores['neg'],
                "neutral": scores['neu'],
                "confidence": abs(compound)
            }
        except Exception as e:
            self.logger.error(f"VADER analysis failed: {e}")
            return {
                "sentiment": SentimentType.NEUTRAL,
                "compound": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _combine_sentiments(self, textblob_result: Dict[str, Any], vader_result: Dict[str, Any]) -> Dict[str, Any]:
        """Combine results from multiple sentiment analyzers."""
        # Weight the different methods
        textblob_weight = 0.4
        vader_weight = 0.6
        
        # Calculate weighted score
        textblob_score = textblob_result.get("polarity", 0)
        vader_score = vader_result.get("compound", 0)
        
        combined_score = (textblob_score * textblob_weight) + (vader_score * vader_weight)
        
        # Determine final sentiment
        if combined_score > self.positive_threshold:
            final_sentiment = SentimentType.POSITIVE
        elif combined_score < self.negative_threshold:
            final_sentiment = SentimentType.NEGATIVE
        else:
            final_sentiment = SentimentType.NEUTRAL
        
        # Calculate confidence as average of individual confidences
        textblob_confidence = textblob_result.get("confidence", 0)
        vader_confidence = vader_result.get("confidence", 0)
        combined_confidence = (textblob_confidence + vader_confidence) / 2
        
        return {
            "sentiment": final_sentiment,
            "score": combined_score,
            "confidence": combined_confidence,
            "agreement": textblob_result.get("sentiment") == vader_result.get("sentiment")
        }
    
    def _extract_insights(self, original_text: str, sentiment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional insights from the sentiment analysis."""
        insights = {
            "word_count": len(original_text.split()),
            "has_emojis": bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', original_text)),
            "has_caps": bool(re.search(r'[A-Z]{3,}', original_text)),
            "has_exclamation": '!' in original_text,
            "has_question": '?' in original_text,
        }
        
        # Detect potential sarcasm indicators
        sarcasm_indicators = [
            "yeah right", "sure", "obviously", "totally", "definitely",
            "great job", "brilliant", "fantastic", "amazing"
        ]
        
        text_lower = original_text.lower()
        insights["potential_sarcasm"] = any(indicator in text_lower for indicator in sarcasm_indicators)
        
        # Emotional intensity
        if sentiment_result["sentiment"] != SentimentType.NEUTRAL:
            if sentiment_result["confidence"] > 0.7:
                insights["emotional_intensity"] = "high"
            elif sentiment_result["confidence"] > 0.3:
                insights["emotional_intensity"] = "medium"
            else:
                insights["emotional_intensity"] = "low"
        else:
            insights["emotional_intensity"] = "neutral"
        
        return insights
    
    async def analyze_batch(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze sentiment for a batch of posts."""
        results = []
        
        for post in posts:
            try:
                result = await self.process(post)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to analyze post {post.get('post_id', 'unknown')}: {e}")
                results.append({
                    "post_id": post.get("post_id", "unknown"),
                    "error": str(e),
                    "sentiment": SentimentType.NEUTRAL,
                    "confidence": 0.0
                })
        
        return results
    
    async def get_sentiment_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of sentiment analysis results."""
        if not results:
            return {"error": "No results to summarize"}
        
        total_posts = len(results)
        sentiment_counts = {
            SentimentType.POSITIVE: 0,
            SentimentType.NEGATIVE: 0,
            SentimentType.NEUTRAL: 0
        }
        
        total_confidence = 0
        successful_analyses = 0
        
        for result in results:
            if "error" not in result:
                sentiment = result.get("sentiment")
                if sentiment in sentiment_counts:
                    sentiment_counts[sentiment] += 1
                
                confidence = result.get("confidence", 0)
                total_confidence += confidence
                successful_analyses += 1
        
        # Calculate percentages
        sentiment_percentages = {
            sentiment: (count / total_posts) * 100
            for sentiment, count in sentiment_counts.items()
        }
        
        # Average confidence
        avg_confidence = total_confidence / successful_analyses if successful_analyses > 0 else 0
        
        return {
            "total_posts": total_posts,
            "successful_analyses": successful_analyses,
            "sentiment_distribution": {
                "counts": sentiment_counts,
                "percentages": sentiment_percentages
            },
            "average_confidence": avg_confidence,
            "overall_sentiment": max(sentiment_counts, key=sentiment_counts.get)
        }
