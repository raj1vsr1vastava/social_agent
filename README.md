# Social Agent - Multi-Agent Social Media Analytics System

A comprehensive social media analytics platform built with AutoGen multi-agent framework.

## Overview

Social Agent is a sophisticated system that leverages multiple AI agents to:
- Scrape and monitor social media channels (Twitter, Instagram, WhatsApp, LinkedIn)
- Perform sentiment analysis on posts and interactions
- Conduct competitor analysis
- Categorize and analyze WhatsApp group conversations
- Identify trends and opportunities for content improvement

## Architecture

### Backend (Python)
- **Multi-Agent Framework**: Built on AutoGen for orchestrating specialized agents
- **Scrapers**: Modular scrapers for different social media platforms
- **Analysis Agents**: Specialized agents for sentiment, competitor, and trend analysis
- **Data Pipeline**: Robust data processing and storage system
- **API Layer**: RESTful API for frontend communication

### Frontend (React)
- **Dashboard**: Real-time analytics and visualization
- **Configuration**: Easy setup and management of social media channels
- **Agent Management**: Monitor and control agent activities

## Project Structure

```
social_agent/
├── src/
│   ├── agents/           # Multi-agent framework and individual agents
│   ├── scrapers/         # Social media scrapers
│   ├── models/           # Data models and database schemas
│   ├── api/              # API endpoints and services
│   ├── utils/            # Utility functions and helpers
│   └── cli/              # Command-line interface
├── tests/                # Test files
├── config/               # Configuration files
├── data/                 # Data storage (development)
└── requirements.txt      # Python dependencies
```

## Development Phases

1. **Phase 1**: Core backend infrastructure and multi-agent framework
2. **Phase 2**: Command-line interface for testing and configuration
3. **Phase 3**: API layer and React frontend

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+ (for frontend)
- Git

### Installation

1. Clone the repository
2. Install Python dependencies: `pip install -r requirements.txt`
3. Configure your social media API credentials
4. Run the CLI tool: `python -m src.cli.main --help`

## Features

### Current Features (Phase 1)
- Multi-agent framework setup
- Basic social media scrapers
- Sentiment analysis agent
- Data storage and retrieval

### Planned Features
- Advanced competitor analysis
- WhatsApp group conversation categorization
- Real-time monitoring dashboard
- Automated reporting
- Trend prediction

## License

This project is licensed under the MIT License.
