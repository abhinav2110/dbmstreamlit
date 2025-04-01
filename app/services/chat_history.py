import logging
import warnings
import os
import logging
from typing import List, Dict

from services.logging_config import setup_logging  # Import the logging setup

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)


# Setup logging
logger=setup_logging()


class SimpleChatStore:
    """In-memory chat store for maintaining user chat history."""

    def __init__(self):
        self.user_chats: Dict[str, List[Dict[str, str]]] = {}

    def add_message(self, user_id: str, user_input: str, llm_response: str):
        if user_id not in self.user_chats:
            self.user_chats[user_id] = []
        self.user_chats[user_id].append({"user": user_input, "text": llm_response})
        logger.debug(f"Added to chat history for user {user_id}: User Input: {user_input}, Response: {self.user_chats[user_id]}")

    def get_chat_history(self, user_id: str) -> str:
        if user_id not in self.user_chats:
            return ""
        formatted_history = "\n\n".join(
            [f"User: {entry['user']}\nBot: {entry['text']}" for entry in self.user_chats[user_id]]
        )
        logger.debug(f"Formatted chat history for user {user_id}: {formatted_history}")
        return formatted_history

    def clear_history(self, user_id: str):
        if user_id in self.user_chats:
            self.user_chats.pop(user_id)
            logger.debug(f"Cleared chat history for user {user_id}.")
    
    def truncate_chat_history(self, history: List[Dict[str, str]], max_tokens: int) -> List[Dict[str, str]]:
        total_tokens = sum(len(item['text']) for item in history)
        while total_tokens > max_tokens and len(history) > 1:
            logger.debug(f"Truncating chat history: Removing oldest entry {history[0]}")
            history.pop(0)
            total_tokens = sum(len(item['text']) for item in history)
        return history


