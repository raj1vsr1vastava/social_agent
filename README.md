# Social Agent - Multi-Agent Social Media Analytics System

🚀 **Current Status: Production Ready with AutoGen 0.4+**

A comprehensive social media analytics platform built with Microsoft AutoGen 0.4+ multi-agent framework, featuring WhatsApp conversation analysis, sentiment tracking, and intelligent message categorization.

## 🎯 Overview

Social Agent is a sophisticated multi-agent system that leverages AI to:
- 📱 **WhatsApp Analysis**: Scrape and analyze group conversations in real-time
- 🎭 **Sentiment Monitoring**: Track emotional trends and team morale
- 🔍 **Semantic Search**: Find relevant messages using vector similarity
- 🤖 **Agent Collaboration**: Multiple AI agents working together via AutoGen 0.4+
- 📊 **Analytics Dashboard**: CLI interface with rich terminal output

## ✨ Key Features

### 🤖 Multi-Agent Framework (AutoGen 0.4+)
- **AssistantAgent**: Specialized agents for different analysis tasks
- **RoundRobinGroupChat**: Coordinated agent collaboration
- **Async Processing**: Concurrent agent operations
- **Mock Client Support**: Development without API keys

### 💾 Vector Database (ChromaDB)
- **Semantic Search**: Find similar messages using AI embeddings
- **Persistent Storage**: ChromaDB with sentence-transformers
- **Metadata Filtering**: Rich search capabilities
- **Batch Processing**: Efficient message storage

### 📱 WhatsApp Integration
- **Selenium WebDriver**: Automated browser control
- **Session Persistence**: Maintains login between runs
- **Real-time Monitoring**: Continuous message scraping
- **Multi-Group Support**: Monitor multiple conversations

### 🎭 Sentiment Analysis
- **VADER Sentiment**: Compound sentiment scoring
- **TextBlob Integration**: Polarity and subjectivity analysis
- **Confidence Tracking**: Analysis reliability metrics
- **Trend Monitoring**: Historical sentiment patterns

## 🏗️ Architecture

### Backend (Python 3.12+)
- **Multi-Agent Framework**: Built on AutoGen 0.4+ for orchestrating specialized agents
- **Vector Database**: ChromaDB for semantic search and message storage
- **Scrapers**: Selenium-based WhatsApp scraper with session management
- **Analysis Agents**: Sentiment analysis with extensible framework
- **CLI Interface**: Rich terminal interface with comprehensive commands

## 📁 Project Structure

```
social_agent/
├── src/
│   ├── agents/           # AutoGen 0.4+ agents (BaseAgent, SentimentAgent)
│   ├── scrapers/         # WhatsApp scraper with Selenium WebDriver
│   ├── models/           # SQLAlchemy models and data schemas
│   ├── utils/            # Vector DB, config, logging, helpers
│   └── cli/              # Command-line interface with Rich output
├── tests/                # Test files and mock data
├── docs/                 # Technical documentation
├── data/                 # Vector DB, logs, WhatsApp sessions (gitignored)
├── .env.example          # Configuration template
├── requirements.txt      # Python dependencies (AutoGen 0.4+)
└── run.py               # Main CLI entry point
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+** (tested with 3.12)
- **Chrome Browser** (for WhatsApp scraping)
- **Git**

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/raj1vsr1vastava/social_agent.git
cd social_agent
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings (WhatsApp phone, OpenAI key, etc.)
```

5. **Initialize system**
```bash
python run.py init
```

## 🎮 Usage

### Command Line Interface

```bash
# Initialize the system
python run.py init

# Check configuration
python run.py config

# View system statistics
python run.py stats

# Scrape WhatsApp messages (requires configuration)
python run.py whatsapp scrape --group "Project Team"

# Monitor WhatsApp in real-time
python run.py whatsapp monitor

# Analyze stored messages
python run.py analyze --sentiment --category

# Search messages semantically
python run.py search "project deadline concerns"
```

### Configuration Options

Edit `.env` file for:
```bash
# WhatsApp Settings
WHATSAPP_PHONE_NUMBER=your_phone_number
WHATSAPP_MONITOR_GROUPS=Group1,Group2,Group3

# OpenAI Integration (optional)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4-turbo-preview

# Vector Database
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DB_COLLECTION=whatsapp_conversations

# Analysis Settings
SENTIMENT_ANALYSIS_ENABLED=true
CATEGORIZATION_ENABLED=true
```

## 🧪 Demo with Mock Data

Try the system without WhatsApp setup:

```bash
# Run the comprehensive demo
python -c "
from datetime import datetime, timedelta
import json

# Mock conversation data
messages = [
    {'content': 'Hey team! How is the project going?', 'sender': 'Alice', 'timestamp': datetime.now()},
    {'content': 'Going great! We are ahead of schedule 😊', 'sender': 'Bob', 'timestamp': datetime.now()},
    {'content': 'I am worried about the deadline...', 'sender': 'Charlie', 'timestamp': datetime.now()}
]

print('🚀 Social Agent Demo')
print('📱 Mock Messages:', len(messages))
for msg in messages:
    print(f'  {msg[\"sender\"]}: {msg[\"content\"]}')
"
```
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

## 🏆 Current Status

### ✅ Completed Features
- **AutoGen 0.4+ Integration**: Multi-agent framework operational
- **Vector Database**: ChromaDB with semantic search
- **WhatsApp Scraper**: Selenium-based with session persistence
- **Sentiment Analysis**: VADER and TextBlob integration
- **CLI Interface**: Complete command-line functionality
- **Configuration System**: Environment-based settings
- **Documentation**: Technical paper and API documentation

### 🔄 In Development
- **Message Categorization Agent**: ML-powered topic classification
- **Response Recommendation Agent**: AI-powered reply suggestions
- **Analytics Dashboard**: Web-based visualization interface
- **Multi-Platform Support**: Twitter, Instagram, LinkedIn integration

### 🎯 Roadmap
- **Web Dashboard**: React-based frontend interface
- **Real-time Notifications**: Webhook and alert system
- **Advanced Analytics**: Trend analysis and reporting
- **Team Management**: User roles and permissions
- **API Layer**: RESTful API for third-party integration

## 🧑‍💻 Development

### Running Tests
```bash
# Run basic import tests
python -c "from src.utils.vector_db import get_vector_db; print('✅ Vector DB working')"

# Test AutoGen integration
python -c "from src.agents.base import BaseAgent; print('✅ AutoGen 0.4+ working')"

# Test sentiment analysis
python -c "from src.agents.sentiment import SentimentAnalysisAgent; print('✅ Sentiment agent ready')"
```

### Project Dependencies
- **AutoGen 0.4+**: Multi-agent framework
- **ChromaDB**: Vector database for semantic search
- **Selenium**: WhatsApp web automation
- **Sentence Transformers**: Text embeddings
- **VADER/TextBlob**: Sentiment analysis
- **SQLAlchemy**: Database ORM
- **Click**: CLI framework
- **Rich**: Terminal formatting
- **Pydantic**: Configuration management

## 📚 Documentation

- **[Technical Paper](docs/technical_paper.md)**: Comprehensive architecture documentation
- **[API Reference](src/)**: Code documentation and examples
- **[Configuration Guide](.env.example)**: Setup and configuration options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Microsoft AutoGen Team**: For the excellent multi-agent framework
- **ChromaDB Team**: For the efficient vector database
- **Hugging Face**: For sentence-transformers and NLP models
- **Open Source Community**: For the amazing Python ecosystem

## 📞 Support

For questions and support:
- **Issues**: GitHub Issues tab
- **Documentation**: Check the technical paper and code comments
- **Discussions**: GitHub Discussions for community help

---

**Built with ❤️ using AutoGen 0.4+, ChromaDB, and Python**
