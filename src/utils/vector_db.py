"""
Vector database management using ChromaDB for efficient conversation storage and retrieval.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import hashlib

from src.utils.config import get_settings
from src.utils.logging import get_logger


class VectorDatabaseManager:
    """Manages vector database operations for conversation storage and retrieval."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("vector_db")
        
        # Initialize ChromaDB
        self.db_path = self.settings.vector_db_path
        os.makedirs(self.db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.settings.embedding_model)
        
        # Get or create collection
        self.collection_name = self.settings.vector_db_collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            self.logger.info(f"Connected to existing collection: {self.collection_name}")
        except Exception as e:
            # Collection doesn't exist, create it
            self.logger.info(f"Collection {self.collection_name} not found, creating new one: {e}")
            try:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "WhatsApp conversations and messages"}
                )
                self.logger.info(f"Created new collection: {self.collection_name}")
            except Exception as create_error:
                self.logger.error(f"Failed to create collection {self.collection_name}: {create_error}")
                raise
    
    def add_message(self, message_data: Dict[str, Any]) -> str:
        """Add a single message to the vector database."""
        try:
            # Generate unique ID for the message
            message_id = self._generate_message_id(message_data)
            
            # Prepare text for embedding
            text_content = self._prepare_text_for_embedding(message_data)
            
            # Generate embedding
            embedding = self.embedding_model.encode(text_content).tolist()
            
            # Prepare metadata
            metadata = self._prepare_metadata(message_data)
            
            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[text_content],
                metadatas=[metadata],
                ids=[message_id]
            )
            
            self.logger.debug(f"Added message {message_id} to vector database")
            return message_id
            
        except Exception as e:
            self.logger.error(f"Failed to add message to vector database: {e}")
            raise
    
    def add_messages_batch(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Add multiple messages to the vector database in batch."""
        try:
            if not messages:
                return []
            
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for message_data in messages:
                # Generate unique ID
                message_id = self._generate_message_id(message_data)
                ids.append(message_id)
                
                # Prepare text for embedding
                text_content = self._prepare_text_for_embedding(message_data)
                documents.append(text_content)
                
                # Generate embedding
                embedding = self.embedding_model.encode(text_content).tolist()
                embeddings.append(embedding)
                
                # Prepare metadata
                metadata = self._prepare_metadata(message_data)
                metadatas.append(metadata)
            
            # Add batch to collection
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Added {len(messages)} messages to vector database")
            return ids
            
        except Exception as e:
            self.logger.error(f"Failed to add messages batch to vector database: {e}")
            raise
    
    def search_similar_messages(
        self, 
        query: str, 
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar messages using vector similarity."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['ids'][0]:  # Check if we have results
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'distance': results['distances'][0][i]
                    })
            
            self.logger.debug(f"Found {len(formatted_results)} similar messages for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Failed to search similar messages: {e}")
            return []
    
    def search_by_metadata(
        self, 
        where: Dict[str, Any], 
        n_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Search messages by metadata filters."""
        try:
            # Check if collection has any documents first
            count = self.collection.count()
            if count == 0:
                self.logger.debug("Collection is empty, returning empty results")
                return []
                
            results = self.collection.query(
                query_embeddings=None,
                n_results=n_results,
                where=where,
                include=["documents", "metadatas"]
            )
            
            # Format results
            formatted_results = []
            if results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i]
                    })
            
            self.logger.debug(f"Found {len(formatted_results)} messages matching metadata filter")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Failed to search by metadata: {e}")
            return []
    
    def get_conversation_context(
        self, 
        group_name: str, 
        around_timestamp: datetime, 
        context_window_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """Get conversation context around a specific timestamp."""
        try:
            # Calculate time window
            start_time = around_timestamp.timestamp() - (context_window_minutes * 60)
            end_time = around_timestamp.timestamp() + (context_window_minutes * 60)
            
            # Search with metadata filters
            where_filter = {
                "group_name": group_name,
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }
            
            results = self.search_by_metadata(where_filter, n_results=100)
            
            # Sort by timestamp
            results.sort(key=lambda x: x['metadata'].get('timestamp', 0))
            
            self.logger.debug(f"Retrieved {len(results)} messages for context around {around_timestamp}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation context: {e}")
            return []
    
    def get_user_message_history(
        self, 
        sender: str, 
        days_back: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get message history for a specific user."""
        try:
            # Calculate time window
            cutoff_time = (datetime.now().timestamp()) - (days_back * 24 * 60 * 60)
            
            where_filter = {
                "sender": sender,
                "timestamp": {"$gte": cutoff_time}
            }
            
            results = self.search_by_metadata(where_filter, n_results=limit)
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x['metadata'].get('timestamp', 0), reverse=True)
            
            self.logger.debug(f"Retrieved {len(results)} messages for user {sender}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get user message history: {e}")
            return []
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a message from the vector database."""
        try:
            self.collection.delete(ids=[message_id])
            self.logger.debug(f"Deleted message {message_id} from vector database")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete message {message_id}: {e}")
            return False
    
    def update_message_metadata(self, message_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """Update metadata for a specific message."""
        try:
            # Get current message
            result = self.collection.get(ids=[message_id], include=["metadatas"])
            
            if not result['ids']:
                self.logger.warning(f"Message {message_id} not found for metadata update")
                return False
            
            # Update metadata
            current_metadata = result['metadatas'][0]
            current_metadata.update(metadata_updates)
            
            # ChromaDB doesn't have direct update, so we need to delete and re-add
            # This is a limitation we might need to work around
            self.logger.warning("Metadata update requires delete and re-add operation")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to update message metadata: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database collection."""
        try:
            count = self.collection.count()
            
            # Only attempt to get sample if collection has documents
            if count == 0:
                return {
                    'total_messages': 0,
                    'unique_groups': 0,
                    'unique_senders': 0,
                    'average_message_length': 0,
                    'collection_name': self.collection_name,
                    'embedding_model': self.settings.embedding_model
                }
            
            # Get sample of recent messages for analysis
            recent_results = self.search_by_metadata(
                where={}, 
                n_results=min(100, count)
            )
            
            # Analyze metadata for statistics
            groups = set()
            senders = set()
            total_chars = 0
            
            for result in recent_results:
                metadata = result['metadata']
                groups.add(metadata.get('group_name', 'unknown'))
                senders.add(metadata.get('sender', 'unknown'))
                total_chars += len(result['document'])
            
            stats = {
                'total_messages': count,
                'unique_groups': len(groups),
                'unique_senders': len(senders),
                'average_message_length': total_chars / len(recent_results) if recent_results else 0,
                'collection_name': self.collection_name,
                'embedding_model': self.settings.embedding_model
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {'error': str(e)}
    
    def _generate_message_id(self, message_data: Dict[str, Any]) -> str:
        """Generate a unique ID for a message."""
        # Create a hash based on message content, sender, and timestamp
        content = f"{message_data.get('content', '')}-{message_data.get('sender', '')}-{message_data.get('timestamp', '')}-{message_data.get('group_name', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _prepare_text_for_embedding(self, message_data: Dict[str, Any]) -> str:
        """Prepare text content for embedding generation."""
        content = message_data.get('content', '')
        sender = message_data.get('sender', '')
        group_name = message_data.get('group_name', '')
        
        # Combine message content with context for better embeddings
        text_for_embedding = f"Group: {group_name}\nSender: {sender}\nMessage: {content}"
        
        return text_for_embedding
    
    def _prepare_metadata(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for storage."""
        metadata = {
            'sender': message_data.get('sender', ''),
            'group_name': message_data.get('group_name', ''),
            'timestamp': message_data.get('timestamp', datetime.now().timestamp()),
            'message_type': message_data.get('message_type', 'text'),
            'platform': message_data.get('platform', 'whatsapp'),
        }
        
        # Add optional metadata fields
        if 'sentiment' in message_data:
            metadata['sentiment'] = message_data['sentiment']
        
        if 'category' in message_data:
            metadata['category'] = message_data['category']
        
        if 'priority' in message_data:
            metadata['priority'] = message_data['priority']
        
        if 'language' in message_data:
            metadata['language'] = message_data['language']
        
        # Ensure all values are JSON serializable
        for key, value in metadata.items():
            if isinstance(value, datetime):
                metadata[key] = value.timestamp()
        
        return metadata
    
    def reset_collection(self) -> bool:
        """Reset the entire collection (use with caution)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "WhatsApp conversations and messages"}
            )
            self.logger.warning(f"Reset collection: {self.collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset collection: {e}")
            return False


# Global vector database manager instance
vector_db = VectorDatabaseManager()


def get_vector_db() -> VectorDatabaseManager:
    """Get the global vector database manager."""
    return vector_db
