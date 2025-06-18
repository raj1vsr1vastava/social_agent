"""
WhatsApp scraper using Selenium WebDriver for web-based WhatsApp monitoring.
"""

import asyncio
import time
import json
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from src.utils.config import get_platform_config
from src.utils.logging import get_logger, log_scraping_activity
from src.utils.helpers import clean_text, normalize_datetime
from src.utils.vector_db import get_vector_db
from src.models import PlatformType


class WhatsAppScraper:
    """WhatsApp scraper using Selenium WebDriver for web.whatsapp.com."""
    
    def __init__(self):
        self.platform_config = get_platform_config()
        self.logger = get_logger("scraper.whatsapp")
        self.vector_db = get_vector_db()
        
        self.driver = None
        self.is_logged_in = False
        self.last_message_time = {}  # Track last message time per chat
        self.message_callback: Optional[Callable] = None
        
        # Configuration
        self.config = self.platform_config.get_whatsapp_config()
        self.session_path = self.config["session_path"]
        
        # Ensure session directory exists
        os.makedirs(self.session_path, exist_ok=True)
    
    def is_configured(self) -> bool:
        """Check if WhatsApp scraper is properly configured."""
        return self.config["monitoring_enabled"] and bool(self.config["phone_number"])
    
    async def initialize_driver(self) -> bool:
        """Initialize the Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            
            # Basic options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # User data directory for session persistence
            user_data_dir = os.path.join(self.session_path, "chrome_profile")
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            
            # Headless mode (configurable)
            if self.config["headless"]:
                chrome_options.add_argument("--headless")
            else:
                chrome_options.add_argument("--window-size=1200,800")
            
            # Disable notifications
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Install and setup ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            # Create driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            self.logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            return False
    
    async def login_to_whatsapp(self) -> bool:
        """Login to WhatsApp Web."""
        try:
            if not self.driver:
                if not await self.initialize_driver():
                    return False
            
            # Navigate to WhatsApp Web
            self.driver.get("https://web.whatsapp.com")
            self.logger.info("Navigated to WhatsApp Web")
            
            # Wait for either QR code or chat interface
            wait = WebDriverWait(self.driver, 30)
            
            try:
                # Check if already logged in
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-list']")))
                self.is_logged_in = True
                self.logger.info("Already logged in to WhatsApp Web")
                return True
                
            except TimeoutException:
                # Need to scan QR code
                try:
                    qr_code = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-ref]")))
                    if qr_code:
                        self.logger.info("QR code detected. Please scan with your phone to login.")
                        
                        if not self.config["headless"]:
                            print("\n" + "="*50)
                            print("WhatsApp Web QR Code detected!")
                            print("Please scan the QR code with your WhatsApp mobile app")
                            print("Waiting for login...")
                            print("="*50 + "\n")
                        
                        # Wait for login completion (QR code disappears)
                        WebDriverWait(self.driver, 120).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-list']"))
                        )
                        
                        self.is_logged_in = True
                        self.logger.info("Successfully logged in to WhatsApp Web")
                        return True
                        
                except TimeoutException:
                    self.logger.error("Login timeout - QR code not scanned within 2 minutes")
                    return False
            
        except Exception as e:
            self.logger.error(f"Failed to login to WhatsApp Web: {e}")
            return False
    
    async def get_chat_list(self) -> List[Dict[str, Any]]:
        """Get list of available chats."""
        try:
            if not self.is_logged_in:
                if not await self.login_to_whatsapp():
                    return []
            
            # Find all chat elements
            chat_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='cell-frame-container']")
            
            chats = []
            for chat_element in chat_elements[:20]:  # Limit to first 20 chats
                try:
                    # Get chat name
                    name_element = chat_element.find_element(By.CSS_SELECTOR, "[data-testid='conversation-info-header']")
                    chat_name = name_element.text.strip()
                    
                    # Get last message preview (if available)
                    try:
                        last_message_element = chat_element.find_element(By.CSS_SELECTOR, "[data-testid='last-msg-preview']")
                        last_message = last_message_element.text.strip()
                    except NoSuchElementException:
                        last_message = ""
                    
                    # Get timestamp (if available)
                    try:
                        time_element = chat_element.find_element(By.CSS_SELECTOR, "[data-testid='msg-time']")
                        timestamp_text = time_element.text.strip()
                    except NoSuchElementException:
                        timestamp_text = ""
                    
                    chats.append({
                        "name": chat_name,
                        "last_message": last_message,
                        "timestamp": timestamp_text,
                        "element": chat_element
                    })
                    
                except Exception as e:
                    self.logger.debug(f"Failed to parse chat element: {e}")
                    continue
            
            self.logger.info(f"Found {len(chats)} available chats")
            return chats
            
        except Exception as e:
            self.logger.error(f"Failed to get chat list: {e}")
            return []
    
    async def open_chat(self, chat_name: str) -> bool:
        """Open a specific chat by name."""
        try:
            # Search for the chat
            search_box = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='chat-list-search']")
            search_box.clear()
            search_box.send_keys(chat_name)
            
            # Wait for search results
            await asyncio.sleep(2)
            
            # Click on the first result
            try:
                first_result = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='cell-frame-container']"))
                )
                first_result.click()
                
                # Wait for chat to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='conversation-header']"))
                )
                
                self.logger.info(f"Opened chat: {chat_name}")
                return True
                
            except TimeoutException:
                self.logger.warning(f"Chat not found: {chat_name}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to open chat {chat_name}: {e}")
            return False
    
    async def scrape_chat_messages(self, chat_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape messages from a specific chat."""
        try:
            if not await self.open_chat(chat_name):
                return []
            
            messages = []
            
            # Scroll up to load more messages
            chat_container = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='conversation-panel-messages']")
            
            # Scroll to load messages
            for _ in range(3):  # Scroll 3 times to load more messages
                self.driver.execute_script("arguments[0].scrollTop = 0", chat_container)
                await asyncio.sleep(1)
            
            # Get message elements
            message_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='msg-container']")
            
            for msg_element in message_elements[-limit:]:  # Get last N messages
                try:
                    message_data = await self._parse_message_element(msg_element, chat_name)
                    if message_data:
                        messages.append(message_data)
                        
                except Exception as e:
                    self.logger.debug(f"Failed to parse message element: {e}")
                    continue
            
            self.logger.info(f"Scraped {len(messages)} messages from chat: {chat_name}")
            return messages
            
        except Exception as e:
            self.logger.error(f"Failed to scrape messages from chat {chat_name}: {e}")
            return []
    
    async def _parse_message_element(self, msg_element, chat_name: str) -> Optional[Dict[str, Any]]:
        """Parse a single message element."""
        try:
            # Get message text
            try:
                text_element = msg_element.find_element(By.CSS_SELECTOR, "[data-testid='msg-text']")
                message_text = text_element.text.strip()
            except NoSuchElementException:
                # Might be a media message or system message
                try:
                    media_element = msg_element.find_element(By.CSS_SELECTOR, "[data-testid='media-caption']")
                    message_text = media_element.text.strip()
                except NoSuchElementException:
                    message_text = "[Media or System Message]"
            
            # Get sender information
            try:
                sender_element = msg_element.find_element(By.CSS_SELECTOR, "[data-testid='msg-meta']")
                sender_info = sender_element.get_attribute("data-pre-plain-text") or ""
                
                # Parse sender from the format "[HH:MM, DD/MM/YYYY] Sender Name: "
                if "] " in sender_info:
                    sender_name = sender_info.split("] ")[1].replace(":", "").strip()
                else:
                    sender_name = "Unknown"
                    
            except NoSuchElementException:
                sender_name = "Unknown"
            
            # Get timestamp
            try:
                time_element = msg_element.find_element(By.CSS_SELECTOR, "[data-testid='msg-time']")
                timestamp_text = time_element.text.strip()
                timestamp = self._parse_whatsapp_timestamp(timestamp_text)
            except NoSuchElementException:
                timestamp = datetime.now()
            
            # Determine if it's an outgoing message
            is_outgoing = "message-out" in msg_element.get_attribute("class")
            
            # Determine message type
            message_type = "text"
            if "[Media" in message_text or "image" in msg_element.get_attribute("outerHTML").lower():
                message_type = "media"
            elif "audio" in msg_element.get_attribute("outerHTML").lower():
                message_type = "audio"
            elif "document" in msg_element.get_attribute("outerHTML").lower():
                message_type = "document"
            
            message_data = {
                "content": clean_text(message_text),
                "sender": sender_name if not is_outgoing else "Me",
                "group_name": chat_name,
                "timestamp": timestamp.timestamp(),
                "message_type": message_type,
                "platform": PlatformType.WHATSAPP,
                "is_outgoing": is_outgoing,
                "raw_html": msg_element.get_attribute("outerHTML")[:500]  # Truncated HTML for debugging
            }
            
            return message_data
            
        except Exception as e:
            self.logger.debug(f"Failed to parse message element: {e}")
            return None
    
    def _parse_whatsapp_timestamp(self, timestamp_text: str) -> datetime:
        """Parse WhatsApp timestamp format."""
        try:
            # WhatsApp shows time in various formats like "12:34", "Yesterday", "DD/MM/YYYY"
            now = datetime.now()
            
            if ":" in timestamp_text and len(timestamp_text) <= 5:
                # Format: "HH:MM" (today)
                time_parts = timestamp_text.split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            elif timestamp_text.lower() == "yesterday":
                return now - timedelta(days=1)
            
            elif "/" in timestamp_text:
                # Format: "DD/MM/YYYY" or similar
                try:
                    return datetime.strptime(timestamp_text, "%d/%m/%Y")
                except ValueError:
                    return now
            
            else:
                return now
                
        except Exception:
            return datetime.now()
    
    async def monitor_chats(self, callback: Optional[Callable] = None) -> None:
        """Monitor specified chats for new messages."""
        try:
            if not self.is_logged_in:
                if not await self.login_to_whatsapp():
                    return
            
            self.message_callback = callback
            monitor_groups = self.config["monitor_groups"]
            monitor_contacts = self.config["monitor_contacts"]
            
            all_chats_to_monitor = monitor_groups + monitor_contacts
            
            if not all_chats_to_monitor:
                self.logger.warning("No chats configured for monitoring")
                return
            
            self.logger.info(f"Starting monitoring for {len(all_chats_to_monitor)} chats")
            
            while True:
                for chat_name in all_chats_to_monitor:
                    try:
                        # Get recent messages
                        messages = await self.scrape_chat_messages(chat_name, limit=10)
                        
                        # Filter new messages
                        new_messages = self._filter_new_messages(chat_name, messages)
                        
                        if new_messages:
                            self.logger.info(f"Found {len(new_messages)} new messages in {chat_name}")
                            
                            # Store in vector database
                            await self._store_messages_in_db(new_messages)
                            
                            # Call callback if provided
                            if self.message_callback:
                                for message in new_messages:
                                    await self.message_callback(message)
                    
                    except Exception as e:
                        self.logger.error(f"Error monitoring chat {chat_name}: {e}")
                        continue
                
                # Wait before next monitoring cycle
                await asyncio.sleep(self.platform_config.settings.message_processing_interval)
                
        except Exception as e:
            self.logger.error(f"Error in chat monitoring: {e}")
            raise
    
    def _filter_new_messages(self, chat_name: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out messages that have already been processed."""
        if not messages:
            return []
        
        last_seen_time = self.last_message_time.get(chat_name, 0)
        new_messages = []
        
        latest_time = last_seen_time
        
        for message in messages:
            message_time = message.get("timestamp", 0)
            if message_time > last_seen_time:
                new_messages.append(message)
                latest_time = max(latest_time, message_time)
        
        # Update last seen time
        if new_messages:
            self.last_message_time[chat_name] = latest_time
        
        return new_messages
    
    async def _store_messages_in_db(self, messages: List[Dict[str, Any]]) -> None:
        """Store messages in vector database."""
        try:
            if messages:
                message_ids = self.vector_db.add_messages_batch(messages)
                log_scraping_activity("whatsapp", "stored messages in vector DB", len(messages))
                
        except Exception as e:
            self.logger.error(f"Failed to store messages in database: {e}")
    
    async def send_message(self, chat_name: str, message: str) -> bool:
        """Send a message to a specific chat."""
        try:
            if not await self.open_chat(chat_name):
                return False
            
            # Find message input box
            message_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='msg-input']"))
            )
            
            # Type and send message
            message_box.clear()
            message_box.send_keys(message)
            
            # Find and click send button
            send_button = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='send-button']")
            send_button.click()
            
            self.logger.info(f"Sent message to {chat_name}: {message[:50]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {chat_name}: {e}")
            return False
    
    async def get_chat_info(self, chat_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific chat."""
        try:
            if not await self.open_chat(chat_name):
                return None
            
            # Click on chat header to open info
            header = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='conversation-header']")
            header.click()
            
            await asyncio.sleep(2)
            
            # Extract chat information
            info = {
                "name": chat_name,
                "type": "group" if "group" in header.text.lower() else "contact",
                "participants": [],
                "description": ""
            }
            
            # TODO: Extract more detailed information from the info panel
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get chat info for {chat_name}: {e}")
            return None
    
    async def close(self):
        """Close the WhatsApp scraper and cleanup."""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("WhatsApp scraper closed successfully")
                
        except Exception as e:
            self.logger.error(f"Error closing WhatsApp scraper: {e}")
    
    def __del__(self):
        """Destructor to ensure driver is closed."""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
