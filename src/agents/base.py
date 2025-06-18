"""
Base agent class and agent orchestrator for the Social Agent system using AutoGen v0.3.0+.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json

# AutoGen v0.4+ imports
from autogen_agentchat.agents import AssistantAgent, BaseChatAgent
from autogen_agentchat.teams import RoundRobinGroupChat

from src.utils.logging import get_logger, log_agent_activity
from src.utils.config import get_settings, get_platform_config
from src.utils.database import db_manager
from src.models import AgentTask, AnalysisStatus


class BaseAgent(ABC):
    """Base class for all social media agents using AutoGen v0.3.0+."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = get_logger(f"agent.{name}")
        self.settings = get_settings()
        self.platform_config = get_platform_config()
        self.is_running = False
        self.tasks = []
        
        # Initialize AutoGen conversable agent with v0.3.0+ API
        self.autogen_agent = self._create_autogen_agent()
    
    def _create_autogen_agent(self) -> AssistantAgent:
        """Create AutoGen AssistantAgent with v0.4+ configuration."""
        # Get model client config
        model_client = self._get_model_client()
        
        # Create the agent
        agent = AssistantAgent(
            name=self.name,
            model_client=model_client,
            system_message=self._get_system_message()
        )
        
        return agent
    
    def _get_model_client(self):
        """Get the model client for AutoGen v0.4+."""
        openai_config = self.platform_config.get_openai_config()
        
        if openai_config["api_key"]:
            # For now, we'll use a mock client since we need to check the exact model client API
            # This will be updated once we test the exact AutoGen 0.4+ model client interface
            return MockModelClient(
                model=openai_config["model"],
                api_key=openai_config["api_key"],
                temperature=openai_config["temperature"],
                max_tokens=openai_config["max_tokens"]
            )
        else:
            # Use mock client for development without API key
            return MockModelClient(model="mock-model")
    
    def _get_system_message(self) -> str:
        """Get the system message for the AutoGen agent."""
        return f"""
        You are {self.name}, a specialized agent in the Social Agent system.
        Description: {self.description}
        
        Your role is to:
        1. Process social media data and perform analysis
        2. Collaborate with other agents to provide comprehensive insights
        3. Maintain data quality and accuracy
        4. Report findings in a structured JSON format
        
        Guidelines:
        - Always respond in valid JSON format when providing analysis results
        - Be precise and factual in your analysis
        - Collaborate effectively with other agents
        - Focus on actionable insights
        
        When analyzing WhatsApp messages, pay special attention to:
        - Context and conversation flow
        - Sentiment and emotional tone
        - Urgency and priority indicators
        - Cultural nuances and communication patterns
        """
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data and return results."""
        pass
    
    async def start(self):
        """Start the agent."""
        self.is_running = True
        log_agent_activity(self.name, "started")
        self.logger.info(f"Agent {self.name} started")
    
    async def stop(self):
        """Stop the agent."""
        self.is_running = False
        log_agent_activity(self.name, "stopped")
        self.logger.info(f"Agent {self.name} stopped")
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task and log the results."""
        task_id = task_data.get("id", "unknown")
        
        try:
            log_agent_activity(self.name, "task_started", {"task_id": task_id})
            
            # Create task record
            with db_manager.session_scope() as session:
                task = AgentTask(
                    task_type=task_data.get("type", "unknown"),
                    agent_name=self.name,
                    status=AnalysisStatus.IN_PROGRESS,
                    config=task_data,
                    started_at=datetime.utcnow()
                )
                session.add(task)
                session.flush()
                task_id = task.id
            
            # Process the task
            result = await self.process(task_data)
            
            # Update task record
            with db_manager.session_scope() as session:
                task = session.query(AgentTask).filter(AgentTask.id == task_id).first()
                if task:
                    task.status = AnalysisStatus.COMPLETED
                    task.result = result
                    task.completed_at = datetime.utcnow()
            
            log_agent_activity(self.name, "task_completed", {"task_id": task_id, "result": result})
            return result
            
        except Exception as e:
            # Update task record with error
            with db_manager.session_scope() as session:
                task = session.query(AgentTask).filter(AgentTask.id == task_id).first()
                if task:
                    task.status = AnalysisStatus.FAILED
                    task.error_message = str(e)
                    task.completed_at = datetime.utcnow()
            
            log_agent_activity(self.name, "task_failed", {"task_id": task_id, "error": str(e)})
            self.logger.error(f"Task {task_id} failed: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "name": self.name,
            "description": self.description,
            "is_running": self.is_running,
            "tasks_count": len(self.tasks),
        }


class MockModelClient:
    """Mock model client for development without API keys."""
    
    def __init__(self, model: str = "mock-model", api_key: str = "", temperature: float = 0.1, max_tokens: int = 1000):
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    async def create(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Mock create method that returns a simple response."""
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "analysis": "Mock analysis result",
                        "confidence": 0.8,
                        "status": "completed"
                    })
                }
            }]
        }


class MockLLMClient:
    """Mock LLM client for development without API keys."""
    
    def __init__(self, model: str = "mock-model"):
        self.model = model
    
    async def create(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Mock create method that returns a simple response."""
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "analysis": "Mock analysis result",
                        "confidence": 0.8,
                        "status": "completed"
                    })
                }
            }]
        }


class AgentOrchestrator:
    """Orchestrates multiple agents using AutoGen v0.3.0+ RoundRobinGroupChat."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = get_logger("orchestrator")
        self.settings = get_settings()
        self.platform_config = get_platform_config()
        self.group_chat = None
        
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agents[agent.name] = agent
        self.logger.info(f"Registered agent: {agent.name}")
        
        # Recreate group chat with new agent
        self._setup_group_chat()
    
    def unregister_agent(self, agent_name: str):
        """Unregister an agent."""
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"Unregistered agent: {agent_name}")
            self._setup_group_chat()
    
    def _setup_group_chat(self):
        """Set up AutoGen group chat with registered agents using v0.4+ RoundRobinGroupChat."""
        if not self.agents:
            return
        
        # Get AutoGen agents
        autogen_agents = [agent.autogen_agent for agent in self.agents.values()]
        
        # Create round-robin group chat using AutoGen 0.4+ API
        self.group_chat = RoundRobinGroupChat(
            participants=autogen_agents
        )
        
        self.logger.info(f"Set up round-robin group chat with {len(autogen_agents)} agents")
    
    async def start_all_agents(self):
        """Start all registered agents."""
        tasks = [agent.start() for agent in self.agents.values()]
        await asyncio.gather(*tasks)
        self.logger.info("All agents started")
    
    async def stop_all_agents(self):
        """Stop all registered agents."""
        tasks = [agent.stop() for agent in self.agents.values()]
        await asyncio.gather(*tasks)
        self.logger.info("All agents stopped")
    
    async def execute_collaborative_task(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task that requires collaboration between agents."""
        if not self.group_chat:
            raise ValueError("No agents registered for collaboration")
        
        try:
            # Format the task message
            message = f"""
            Task: {task_description}
            Context: {json.dumps(context, indent=2)}
            
            Please collaborate to analyze this data and provide comprehensive insights.
            Each agent should contribute their specialized analysis.
            Provide the final result in JSON format.
            """
            
            # Run the group chat
            chat_result = await self.group_chat.run(message)
            
            # Extract the results from the chat
            if hasattr(chat_result, 'messages') and chat_result.messages:
                last_message = chat_result.messages[-1]
                return {
                    "result": last_message.content if hasattr(last_message, 'content') else str(last_message),
                    "collaboration_summary": f"Processed by {len(self.agents)} agents",
                    "agents_involved": list(self.agents.keys())
                }
            
            return {"result": "No result generated", "agents_involved": list(self.agents.keys())}
            
        except Exception as e:
            self.logger.error(f"Collaborative task failed: {e}")
            raise
    
    async def distribute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Distribute a task to the appropriate agent."""
        # Find the best agent for the task
        suitable_agent = self._find_suitable_agent(task_type)
        
        if not suitable_agent:
            raise ValueError(f"No suitable agent found for task type: {task_type}")
        
        return await suitable_agent.execute_task(task_data)
    
    def _find_suitable_agent(self, task_type: str) -> Optional[BaseAgent]:
        """Find the most suitable agent for a task type."""
        # Enhanced mapping for WhatsApp-focused system
        task_agent_mapping = {
            "sentiment_analysis": "SentimentAnalysisAgent",
            "whatsapp_sentiment": "SentimentAnalysisAgent",
            "message_categorization": "MessageCategorizationAgent",
            "whatsapp_categorization": "MessageCategorizationAgent",
            "response_suggestion": "ResponseSuggestionAgent",
            "whatsapp_response": "ResponseSuggestionAgent",
            "conversation_analysis": "ConversationAnalysisAgent",
            "competitor_analysis": "CompetitorAnalysisAgent",
            "trend_analysis": "TrendAnalysisAgent",
        }
        
        agent_name = task_agent_mapping.get(task_type)
        return self.agents.get(agent_name) if agent_name else None
    
    async def process_whatsapp_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a WhatsApp message through multiple agents."""
        try:
            results = {}
            
            # Sentiment analysis
            if self.settings.sentiment_analysis_enabled:
                sentiment_agent = self.agents.get("SentimentAnalysisAgent")
                if sentiment_agent:
                    sentiment_result = await sentiment_agent.process(message_data)
                    results["sentiment"] = sentiment_result
            
            # Message categorization
            if self.settings.categorization_enabled:
                categorization_agent = self.agents.get("MessageCategorizationAgent")
                if categorization_agent:
                    category_result = await categorization_agent.process(message_data)
                    results["categorization"] = category_result
            
            # Response suggestions
            if self.settings.response_suggestions_enabled:
                response_agent = self.agents.get("ResponseSuggestionAgent")
                if response_agent:
                    response_result = await response_agent.process(message_data)
                    results["response_suggestion"] = response_result
            
            return {
                "message_id": message_data.get("id", "unknown"),
                "processing_results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing WhatsApp message: {e}")
            return {"error": str(e), "message_id": message_data.get("id", "unknown")}
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "total_agents": len(self.agents),
            "running_agents": sum(1 for agent in self.agents.values() if agent.is_running),
            "agents": [agent.get_status() for agent in self.agents.values()],
            "enabled_platforms": self.platform_config.get_enabled_platforms(),
            "autogen_version": "0.3.0+",
            "group_chat_active": self.group_chat is not None
        }


# Global orchestrator instance
orchestrator = AgentOrchestrator()


def get_orchestrator() -> AgentOrchestrator:
    """Get the global agent orchestrator."""
    return orchestrator
