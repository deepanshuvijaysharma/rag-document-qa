"""Lightweight Persistent Conversation History Store.

Stores chat session history in a thread-safe JSON file, decoupled from vector database storage.
"""

import os
import json
import logging
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("rag_app.conversation_store")

# Default conversation storage file path
DEFAULT_CONVERSATION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "conversations.json"
)


class ConversationStore:
    """Thread-safe persistent JSON conversation history store."""

    _lock = threading.Lock()

    def __init__(self, file_path: Optional[str] = None) -> None:
        """Initialize ConversationStore with file persistence path.
        
        Args:
            file_path: Optional custom JSON file path for storage.
        """
        self.file_path = file_path or DEFAULT_CONVERSATION_FILE
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create empty JSON object file if it does not exist."""
        if not os.path.exists(self.file_path):
            with self._lock:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=2)

    def _read_data(self) -> Dict[str, Dict[str, Any]]:
        """Read conversation JSON file safely."""
        with self._lock:
            try:
                if not os.path.exists(self.file_path):
                    return {}
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as err:
                logger.error(f"Error reading conversation store '{self.file_path}': {err}")
                return {}

    def _write_data(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Write conversation JSON file atomically using a temporary file."""
        with self._lock:
            temp_path = f"{self.file_path}.tmp"
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                os.replace(temp_path, self.file_path)
            except Exception as err:
                logger.error(f"Error writing conversation store '{self.file_path}': {err}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

    def get_history(self, conversation_id: str, max_messages: int = 6) -> List[Dict[str, str]]:
        """Retrieve recent conversation history turns up to max_messages limit.
        
        Args:
            conversation_id: Session identifier string
            max_messages: Maximum number of recent history messages to return (default: 6)
            
        Returns:
            List of message dicts [{"role": "user", "content": "..."}, ...]
        """
        if not conversation_id:
            return []

        data = self._read_data()
        session = data.get(conversation_id)
        if not session or "history" not in session:
            return []

        full_history: List[Dict[str, str]] = session["history"]
        # Return last N messages cleanly
        if len(full_history) <= max_messages:
            return full_history
        return full_history[-max_messages:]

    def append_turns(self, conversation_id: str, user_message: str, assistant_message: str) -> None:
        """Append user question and assistant answer turn to conversation history."""
        if not conversation_id:
            return

        data = self._read_data()
        now_iso = datetime.utcnow().isoformat()

        if conversation_id not in data:
            data[conversation_id] = {
                "conversation_id": conversation_id,
                "created_at": now_iso,
                "updated_at": now_iso,
                "history": []
            }

        session = data[conversation_id]
        session["updated_at"] = now_iso
        history: List[Dict[str, str]] = session.get("history", [])

        # Clean message contents
        history.append({"role": "user", "content": user_message.strip()})
        history.append({"role": "assistant", "content": assistant_message.strip()})

        # Retain last 20 messages maximum per conversation session on disk
        if len(history) > 20:
            history = history[-20:]

        session["history"] = history
        self._write_data(data)
        logger.info(f"Appended chat turn to conversation '{conversation_id}'. Total history messages: {len(history)}")

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation history session."""
        data = self._read_data()
        if conversation_id in data:
            del data[conversation_id]
            self._write_data(data)
            logger.info(f"Deleted conversation session '{conversation_id}'.")
            return True
        return False

    def clear(self) -> None:
        """Clear all stored conversations (primarily for tests/reset)."""
        self._write_data({})
